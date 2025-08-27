from tool.helper import *
from tool.builders.sql_builder import ChartSQLFactory
from tool.builders.other_builder import IVCurveBuilder

"""
This file defines the class for building the panels json file in Grafana.
    - General Panels
    - IV Curve Plot
"""

class PanelBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.IVCurveBuilder = IVCurveBuilder(datasource_uid)
    
    # -- Regular Panels --
    def generate_sql(self, chart_type: str, table: str, condition: str, groupby: list, filters: list, distinct: bool, inputs: list) -> str:
        """Generate the SQL command from ChartSQLFactory. -> sql_builder.py
        """
        # Get Generator
        generator = ChartSQLFactory.get_generator(chart_type)

        # Generate SQL command
        panel_sql = generator.generate_sql(table, condition, groupby, filters, distinct, inputs)

        return panel_sql

    def assign_gridPos(self, dashboard_title: str, config_panels: list, max_cols=24) -> list:
        """Assign gridPos to each panel in the dashboard. 
        """
        # initial settings
        x, y = 0, 0

        # set up the size of each panel
        num_panels = len(config_panels)

        # set up the max number of panels per line:
        if dashboard_title.startswith("Free") or "Module Assembly" in dashboard_title or 'IV_Curve Plot' in dashboard_title:
            max_num = 1
        elif dashboard_title == "Module Info" or "Environment Monitoring" in dashboard_title:
            max_num = 2
        else: 
            max_num = 3

        # assign width and hight    
        if num_panels <= max_num:
            width = max_cols // num_panels
        else:
            width = max_cols // max_num

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

    def get_info(self, panel: dict, chart_type: str) -> tuple:
        """Get the information from the panel config by chart_type.
        """
        if chart_type == "xychart":
            filters = panel.get("filters", None)
            temp_condition = panel.get("temp_condition", None)
            rel_hum_condition = panel.get("rel_hum_condition", None)
            gridPos = panel.get("gridPos")
            
            return filters, temp_condition, rel_hum_condition, gridPos
        
        else:
            title = panel.get("title")
            table = panel.get("table")
            condition = panel.get("condition")
            groupby = panel.get("groupby")
            filters = panel.get("filters")
            gridPos = panel.get("gridPos")
            distinct = panel.get("distinct")
            return title, table, condition, groupby, filters, gridPos, distinct
    
    def generate_general_panel(self, title: str, raw_sql: str, table: str, chart_type: str, gridPos: dict) -> dict:
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
            },
            {
            "id": "partitionByValues",
            "options": {
                "fields": [
                    "log_location"
                ],
                "keepFields": False
              }
            }
        ],
        "type": f"{chart_type}"
        }

        return panel_json

    # -- Genarate Panels --
    def generate_panels_json(self, dashboard_title: str, config_panels: list) -> list:
        """Build the panel jsons based on the given config file.
        """
        panels = []
        self.assign_gridPos(dashboard_title, config_panels)

        # load information from config file
        for panel in config_panels:
            title = panel["title"]
            chart_type = panel["chart_type"]

            try:
                if chart_type == "xychart":
                    filters, temp_condition, rel_hum_condition, gridPos = self.get_info(panel, chart_type)    # get conditions for SQL
                    raw_sql = self.IVCurveBuilder.IV_curve_panel_sql(filters, temp_condition, rel_hum_condition)    # generate SQL
                    override = self.IVCurveBuilder.IV_curve_panel_override()   # generate override for xy axises
                    panel_json = self.IVCurveBuilder.generate_IV_curve_panel_new(title, raw_sql, override, gridPos)

                else:
                    title, table, condition, groupby, filters, gridPos, distinct = self.get_info(panel, chart_type)
                    inputs = panel.get("inputs", None)
                    raw_sql = self.generate_sql(chart_type, table, condition, groupby, filters, distinct, inputs)
                    panel_json = self.generate_general_panel(title, raw_sql, table, chart_type, gridPos)

                panels.append(panel_json)

            except Exception as e:
                print(f"[ERROR] Failed to generate panel '{title}' | Reason: {e}")
                print(f"[WARNING] Skip panel: {title}")

        return panels