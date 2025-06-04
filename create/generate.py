import requests
import json
import yaml
import os
from create.sql_builder import ChartSQLFactory

"""
This file contains all the functions that are needed to generate everything for the Grafana dashboards.
"""

# -- Load YAML Configuration --

gf_conn_path='a_EverythingNeedToChange/gf_conn.yaml'
db_conn_path='a_EverythingNeedToChange/db_conn.yaml'

# Read the conn files:
with open(gf_conn_path, mode='r') as file:
    gf_conn = yaml.safe_load(file)

with open(db_conn_path, mode='r') as file:
    db_conn = yaml.safe_load(file)


# ============================================================
# === Folder Generator =======================================
# ============================================================

def generate_folder(folder_name: str):
    """Create Grafana folder or fetch if it already exists. Update UID map.
    """

    grafana_url = gf_conn['GF_URL']
    username = gf_conn['GF_USER']
    password = gf_conn['GF_PASS']
    headers = {"Content-Type": "application/json"}
    folder_uid = folder_name.lower().replace(" ", "-")

    # Check if folder exists
    response = requests.get(f"{grafana_url}/api/folders/{folder_uid}", headers=headers, auth=(username, password))
    if response.status_code == 200:
        print(f"Folder '{folder_name}' exists.")
        uid = response.json()['uid']
    else:
        # Create folder
        payload = {"title": folder_name, "uid": folder_uid}
        response = requests.post(f"{grafana_url}/api/folders", headers=headers, auth=(username, password), data=json.dumps(payload))
        response.raise_for_status()
        uid = response.json()['uid']
        print(f"Created folder '{folder_name}' with UID {uid}")

    # Update UID map
    if "GF_FOLDER_UIDS" not in gf_conn:
        gf_conn["GF_FOLDER_UIDS"] = {}
    gf_conn["GF_FOLDER_UIDS"][folder_name] = uid

    with open(gf_conn_path, "w") as f:
        yaml.dump(gf_conn, f)
        print(f"Updated gf_conn.yaml with folder '{folder_name}'.")


# ============================================================
# === Dashboard Generator ====================================
# ============================================================

def generate_dashboard(dashboard_title: str, panels: list, template_list: list) -> dict:
    """
    Generates a Grafana dashboard json file based on the given panels.
    """

    # load information
    dashboard_uid = dashboard_title.lower().replace(" ", "-")
    
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
            "from": "now-1y",
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

    #reload gf_conn.yaml
    with open(gf_conn_path, mode='r') as file:
      new_gf_conn = yaml.safe_load(file)

    grafana_url = new_gf_conn['GF_URL']
    api_token = new_gf_conn['GF_API_KEY']
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    folder_name = os.path.basename(os.path.dirname(file_path)).replace("_", " ")
    file_name = os.path.basename(file_path).split(".")[0].replace("_", " ")
    folder_uid_map = new_gf_conn.get("GF_FOLDER_UIDS", {})

    if folder_name not in folder_uid_map:
        raise ValueError(f"Folder '{folder_name}' not in GF_FOLDER_UIDS")

    folder_uid = folder_uid_map[folder_name]

    with open(file_path, 'r', encoding='utf-8') as file:
        dashboard = json.load(file)

    payload = {
        "dashboard": dashboard,
        "folderUid": folder_uid,
        "overwrite": True
    }

    response = requests.post(
        f"{grafana_url}/api/dashboards/db",
        headers=headers,
        data=json.dumps(payload)
    )

    print(f"[{folder_name}]: {file_name}  Upload status: {response.status_code}")


# ============================================================
# === Panel Generator ========================================
# ============================================================

def generate_panel(title: str, raw_sql: str, table: str, groupby: str, chart_type: str, gridPos: dict) -> dict:
    """Generate a panel json based on the given raw_sql, table, groupby, chart_type, and gridPos.
    """

    # load information:
    datasource_uid = gf_conn['GF_DATA_SOURCE_UID']

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

    title = panel["title"]
    table = panel["table"]
    chart_type = panel["chart_type"]
    condition = panel["condition"]
    groupby = panel["groupby"]
    gridPos = panel["gridPos"]
    filters = panel["filters"]
    filters_table = panel["filters_table"]
    distinct = panel["distinct"]

    return title, table, chart_type, condition, groupby, gridPos, filters, filters_table, distinct


def generate_sql(chart_type: str, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
    """Generate the SQL command from ChartSQLFactory. -> sql_builder.py
    """

    # Get Generator
    generator = ChartSQLFactory.get_generator(chart_type)

    # Generate SQL command
    panel_sql = generator.generate_sql(table, condition, groupby, filters, filters_table, distinct)

    return panel_sql
    

# ============================================================
# === Template Generator =====================================
# ============================================================

def generate_filter(filter_name: str, filter_sql: str) -> dict:
  """Generate a template json based on the given .
  """

  # load information:
  datasource_uid = gf_conn['GF_DATA_SOURCE_UID']

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
