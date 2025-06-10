import os

import glob
import pickle
import asyncio
import base64
import datetime

import asyncpg
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D

from tool.helper import *
from tool.sql_builder import ChartSQLFactory

"""
This file defines the class for building the panels json file in Grafana.
    - General Panels
    - IV Curve Plot
"""

class PanelBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
    
    # -- Regular Panels --
    def generate_sql(self, chart_type: str, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        """Generate the SQL command from ChartSQLFactory. -> sql_builder.py
        """
        # Get Generator
        generator = ChartSQLFactory.get_generator(chart_type)

        # Generate SQL command
        panel_sql = generator.generate_sql(table, condition, groupby, filters, distinct)

        return panel_sql

    def assign_gridPos(self, config_panels: list, max_cols=24) -> list:
        """Assign gridPos to each panel in the dashboard. 
        """
        # initial settings
        x, y = 0, 0

        # set up the size of each panel
        num_panels = len(config_panels)

        if num_panels <= 3:
            width = max_cols // num_panels
        else:
            width = 8     # max 3 in a row

        height = width // 2 + 2

        # assign gridPos to each panel
        for panel in config_panels:
            if x + width > max_cols:    # Switch lines
                x = 0
                y += height

            panel["gridPos"] = {
                "x": x,
                "y": y,
                "w": width,
                "h": height
            }

            x += width

        return config_panels
    
    def generate_panel(self, title: str, raw_sql: str, table: str, chart_type: str, gridPos: dict) -> dict:
        """Generate a panel json based on the given title, raw_sql, table, chart_type, and gridPos.
        """
        # generate the panel json:
        panel_json = {
        "datasource": {
            "type": "grafana-postgresql-datasource",
            "uid": f"{self.datasource_uid}"
        },
        "fieldConfig": {
            "defaults": {
            "color": {
                "mode": "palette-classic"
            },
            "custom": {
                "scaleDistribution": {
                "type": "linear"
                },
            },
            "mappings": [],
            },
            "overrides": []
        },
        "gridPos": gridPos,
        "id": 1,
        "options": {
            "barRadius": 0,
            "barWidth": 0.97,
            "fullHighlight": False,
            "groupWidth": 0.7,
            "legend": {
            "calcs": [],
            "displayMode": "list",
            "placement": "bottom",
            "showLegend": True
            },
            "orientation": "horizontal",
            "showValue": "auto",
            "stacking": "normal",
            "tooltip": {
            "hideZeros": False,
            "mode": "single",
            "sort": "none"
            },
            "xTickLabelRotation": 0,
            "xTickLabelSpacing": 0
        },
        "pluginVersion": "12.0.0",
        "targets": [
            {
            "datasource": {
                "type": "grafana-postgresql-datasource",
                "uid": f"{self.datasource_uid}"
            },
            "editorMode": "code",
            "format": "table",
            "rawQuery": True,
            "rawSql": f"{raw_sql}",
            "refId": "A",
            "table": f"{table}"
            }
        ],
        "title": f"{title}",
        "transformations": [
            {
            "id": "filterFieldsByName",
            "options": {}
            }
        ],
        "type": f"{chart_type}"
        }

        return panel_json
    
    # -- IV Curve Plot --
    def generate_IV_curve_panel(self, title: str, content: str) -> dict:
        """Generate the panel specifially for IV_curve plot.
        """
        # generate the panel json:
        panel_json = {
        "fieldConfig": {
            "defaults": {},
            "overrides": []
        },
        "gridPos": {        
            "h": 14,
            "w": 14,
            "x": 0,
            "y": 0
        },
        "id": 7,
        "options": {
            "code": {
            "language": "plaintext",
            "showLineNumbers": False,
            "showMiniMap": False
            },
            "content": content,
            "mode": "markdown"
        },
        "pluginVersion": "12.0.0",
        "title": title,
        "type": "text"
        }

        return panel_json

    def generate_plot(self):
        """Generate the IV_curve Plot.
        """
        loop = asyncio.get_event_loop()

        # functions for interating with db
        async def connect_db():
            return await asyncpg.create_pool(
                host = db_host,
                database = db_name,
                user = db_user,
                password = db_password
            )

        pool = loop.run_until_complete(connect_db())

        async def fetch_modules(pool):
            query = """SELECT * FROM module_info;"""
            async with pool.acquire() as conn:
                return await conn.fetch(query)

        async def fetch_iv(pool, moduleserial):
            query = f"""SELECT *  
                        FROM module_iv_test                                                                  
                        WHERE REPLACE(module_name,'-','') = '{moduleserial}'                                       
                        ORDER BY date_test, time_test;"""
            async with pool.acquire() as conn:
                return await conn.fetch(query)


        def select_iv(moduleserial, modulestatus, dry=True, roomtemp=True):
            result = loop.run_until_complete(fetch_iv(pool, moduleserial))
            
            runs = []
            for r in result:
                RH = float(r['rel_hum'])
                T = float(r['temp_c'])
                req1 = (RH <= 12) if dry else (RH >= 20)
                req2 = (T >= 10 and T <= 30) if roomtemp else (T <= -20)
                if req1 and req2 and r['status_desc'] == modulestatus:
                    runs.append(r)

            return runs

        N_MODULE_SHOW = 15

        result = loop.run_until_complete(fetch_modules(pool))

        def modserkey(module):
            return int(module['module_no'])

        result.sort(key=modserkey)
        module_serials = [mod['module_name'] for mod in result]
        modules = module_serials[-N_MODULE_SHOW:]

        fig, ax = plt.subplots(figsize=(16, 12))

        datetoday = str(datetime.datetime.now()).split(' ')[0]

        def sortkey(curve):
            return curve['meas_i'][-1]/curve['program_v'][-1]

        dry = True
        for module in modules:

            curvedata = select_iv(module, 'Completely Encapsulated', dry=dry, roomtemp=True)

            if len(curvedata) == 0:
                curvedata = select_iv(module, 'Frontside Encapsulated', dry=dry, roomtemp=True)

            if len(curvedata) > 0:
                # get best curve
                curvedata.sort(reverse=True, key = sortkey)
                
                meas_v = curvedata[-1]['meas_v']
                meas_i = curvedata[-1]['meas_i']

                plt.plot(meas_v, meas_i, label=module)
                        
        ax.set_yscale('log')
        dryname = 'Dry' if dry else 'Ambient'
        ax.set_title(f'{dryname} Module IV Curves [Log Scale]', fontsize=30)
        ax.set_xlabel('Reverse Bias [V]', fontsize=25)
        ax.set_ylabel(r'Leakage Current [A]', fontsize=25)
        ax.set_ylim(1e-9, 1e-03)
        ax.set_xlim(0, 500)
        ax.xaxis.label.set_size(30)
        ax.yaxis.label.set_size(30)
        ax.tick_params(axis='both', which='major', labelsize=25)
        ax.legend(fontsize=15, loc='upper left')

        # create folder:
        os.makedirs("iv_curves_plot", exist_ok=True)
        # define path and save plot
        plt_path = f'iv_curves_plot/combined_iv_logscale_{datetoday}_{N_MODULE_SHOW}.png'
        plt.savefig(plt_path)

        return plt_path

    def convert_png_to_base64(self, image_path: str) -> str:
        """convert the png to base64
        """
        # Compress the image
        img = Image.open(image_path)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        img.save(image_path, optimize=True)

        # Generate the encoded_string
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string

    def generate_content(self, encoded_string: str) -> str:
        """generate the markdown content for text panel
        """
        content = f'<img src=\"data:image/png;base64,{encoded_string}" style="width: auto; height: auto;"/>'
        return content

    # -- Genarate Panels --
    def build_from_config(self, config_panels: list) -> list:
        """Build the panel jsons based on the given config file.
        """
        panels = []
        self.assign_gridPos(config_panels)

        # load information from config file
        for panel in config_panels:
            title = panel["title"]
            table = panel["table"]
            chart_type = panel["chart_type"]
            condition = panel["condition"]
            groupby = panel["groupby"]
            filters = panel["filters"]
            gridPos = panel["gridPos"]
            distinct = panel["distinct"]

            if chart_type == "text":
                plt_path = self.generate_plot()
                encoded_string = self.convert_png_to_base64(plt_path)
                content = self.generate_content(encoded_string)
                panel_obj = self.generate_IV_curve_panel(title, content)

            else:
                raw_sql = self.generate_sql(chart_type, table, condition, groupby, filters, distinct)
                panel_obj = self.generate_panel(title, raw_sql, table, chart_type, gridPos)

            panels.append(panel_obj)

        return panels