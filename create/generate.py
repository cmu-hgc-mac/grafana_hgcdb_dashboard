import requests
import json
import yaml
import os
from create.sql_builder import ChartSQLFactory
from helper import *

"""
This file contains all the functions that are needed to generate everything for the Grafana dashboards.
"""

# -- Load YAML Configuration --
gf_conn = ConfigLoader("gf_conn")
db_conn = ConfigLoader("db_conn")

grafana_url = gf_conn.get('GF_URL')
api_token = gf_conn.get('GF_API_KEY')
datasource_uid = gf_conn.get('GF_DATA_SOURCE_UID')
username = gf_conn.get('GF_USER')
password = gf_conn.get('GF_PASS')

# -- define GrafanaClient --
client = GrafanaClient(api_token, grafana_url)

# ============================================================
# === Folder Generator =======================================
# ============================================================

def generate_folder(folder_name: str):
    """Create Grafana folder or fetch if it already exists. Update UID map.
    """
    if folder_name == "General":  # default folder: no UID
        print("Skipping folder creation: 'General' is default folder with no UID.")
        return ""

    folder_uid = create_uid(folder_name)

    # create or fetch folder
    try:
        uid = client.create_or_get_folder(folder_name, folder_uid)
    except requests.RequestException as e:
        print(f"[ERROR] Failed to create or fetch folder '{folder_name}': {e}")
        raise

    # Update UID map
    if gf_conn.get("GF_FOLDER_UIDS") is None:
        gf_conn.set["GF_FOLDER_UIDS", {}]

    gf_conn.set(f"GF_FOLDER_UIDS.{folder_name}", uid)

    gf_conn.save()


# ============================================================
# === Dashboard Generator ====================================
# ============================================================

def generate_dashboard(dashboard_title: str, panels: list, template_list: list) -> dict:
    """Generates a Grafana dashboard json file based on the given panels.
    """
    # get dashboard_uid
    dashboard_uid = create_uid(dashboard_title)

    # define the time range
    if dashboard_title == "Enviorment Monitoring":
      time_range = "now-24h"
    else:
      time_range = "now-1y"
    
    # generate the dashboard json
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": panels,
        "refresh": "5m",
        "schemaVersion": 41,
        "tags": [],
        "templating": {
            "list": template_list
        },
        "time": {
            "from": time_range,
            "to": "now"
        },
        "timepicker": {},
        "timezone": "browser",
        "title": dashboard_title,
        "uid": dashboard_uid,
        "version": 1
    }

    return dashboard


def save_dashboard_json(dashboard: dict, dashboard_json: dict, folder: str):
    """Save a dashboard JSON into Dashboards/<folder>/<dashboard_title>.json.
    """
    # Get the safe title for the filename
    safe_title = dashboard["title"].replace(" ", "_")
    filename = safe_title + ".json"

    # create path
    folder_path = os.path.join("Dashboards", folder)
    os.makedirs(folder_path, exist_ok=True)  # create the new Dashboards/folder

    path = os.path.join(folder_path, filename)

    # import file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dashboard_json, f, indent=2)
    
    print(f"Dashboard saved to {path}")


def upload_dashboards(file_path: str):
    """Upload one dashboard JSON file into Grafana folder.
    """
    # reload gf_conn.yaml
    new_gf_conn = gf_conn._load()

    # get folder and file name
    folder_name = os.path.basename(os.path.dirname(file_path)).replace("_", " ")
    file_name = os.path.basename(file_path).split(".")[0].replace("_", " ")

    if folder_name == "General":  # main dashboards: empty uid
        folder_uid = ""
    else:
        folder_uid_map = new_gf_conn.get("GF_FOLDER_UIDS", {})
        if folder_name not in folder_uid_map:
            raise ValueError(f"Folder '{folder_name}' not in GF_FOLDER_UIDS")
        folder_uid = folder_uid_map[folder_name]

    with open(file_path, 'r', encoding='utf-8') as file:
        dashboard_json = json.load(file)

    # upload dashboard
    try:
      client.upload_dashboard(dashboard_json, folder_uid)
    except requests.RequestException as e:
      print(f"[ERROR] Failed to upload dashboard '{file_name}': {e}")
      raise


# ============================================================
# === Panel Generator ========================================
# ============================================================

def generate_panel(title: str, raw_sql: str, table: str, groupby: str, chart_type: str, gridPos: dict) -> dict:
    """Generate a panel json based on the given raw_sql, table, groupby, chart_type, and gridPos.
    """
    # generate the panel json:
    panel_json = {
      "datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": f"{datasource_uid}"
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
            "uid": f"{datasource_uid}"
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


def generate_IV_curve_panel(title: str, content: str, gridPos: dict) -> dict:
    """Generate the panel specifially for IV_curve
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


def assign_gridPos(panels: list, max_cols=24) -> list:
    """Assign gridPos to each panel in the dashboard. 
    """
    # initial settings
    x, y = 0, 0

    # set up the size of each panel
    num_panels = len(panels)

    if num_panels <= 3:
      width = max_cols // num_panels
    else:
      width = 8     # max 3 in a row

    height = width // 2 + 2

    # assign gridPos to each panel
    for panel in panels:
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

    return panels


def read_panel_info(panel: dict) -> tuple:
    """Read panel information from the config file.
    """
    # load information:
    title = panel["title"]
    table = panel["table"]
    chart_type = panel["chart_type"]
    condition = panel["condition"]
    groupby = panel["groupby"]
    gridPos = panel["gridPos"]
    filters = panel["filters"]
    distinct = panel["distinct"]

    return title, table, chart_type, condition, groupby, gridPos, filters, distinct


def generate_sql(chart_type: str, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
    """Generate the SQL command from ChartSQLFactory. -> sql_builder.py
    """
    # Get Generator
    generator = ChartSQLFactory.get_generator(chart_type)

    # Generate SQL command
    panel_sql = generator.generate_sql(table, condition, groupby, filters, distinct)

    return panel_sql
    

# ============================================================
# === Template Generator =====================================
# ============================================================

def generate_filter(filter_name: str, filter_sql: str) -> dict:
  """Generate a template json based on the given .
  """
  # generate the filter json:
  filter_json = {
        "current": {
        "text": [
          "All"
          ],
        "value": [
          "$__all"
          ]
        },
        "datasource": {
        "type": "postgres",
        "uid": f"{datasource_uid}"
        },
        "includeAll": True,
        "multi": True,
        "name": filter_name,
        "options": [],
        "query": filter_sql,
        "refresh": 1,   # refresh everytime when dashboard is loaded
        "type": "query"
      }

  return filter_json


def generate_filterSQL(filter_name: str, filters_table: str) -> str:
  """Generate a template SQL command based on the given filter name.
  """
  # check filter type:
  if filter_name == "status":
    filter_sql = f"""
      SELECT DISTINCT 
      CASE WHEN shipped_datetime IS NULL THEN 'not shipped' ELSE 'shipped' END AS status 
      FROM {filters_table}
      ORDER BY status
      """
  else:
    filter_sql = f"""
      SELECT DISTINCT {filter_name} FROM {filters_table} ORDER BY {filter_name}
      """

  return filter_sql
  