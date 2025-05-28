import requests
import json
import yaml
import os
from sql_builder import ChartSQLFactory

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

def generate_folder(folder_name, folder_number):
    """
    Generate a folder in Grafana based on the given folder name and number.
    """

    # load information
    service_account_id = gf_conn['GF_SA_ID']
    grafana_url = gf_conn['GF_URL']
    username = gf_conn['GF_USER']
    password = gf_conn['GF_PASS']
    headers = {
        "Content-Type": "application/json"
    }

    # Create the folder:
    folder_payload = {
        "title": folder_name,
        "uid": folder_name.lower().replace(" ", "-")
    }

    create_folder_response = requests.post(
        f"{grafana_url}/api/folders",
        headers=headers,
        auth=(username, password),
        data=json.dumps(folder_payload)
    )
    create_folder_response.raise_for_status()
    folder_uid = create_folder_response.json()['uid']
    print(f"Created folder '{folder_name}' with UID: {folder_uid}")


    # Update gf_conn.yaml: 
    gf_conn.update({
        f'GF_FOLDER_NAME{folder_number}': str(folder_name),
        f'GF_FOLDER_UID{folder_number}': str(folder_uid),
    })

    with open(gf_conn_path, 'w') as file:
        yaml.dump(gf_conn, file)
        print(f" >> Auto update for gf_conn.yaml successfully...")


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
        "refresh": "10s",
        "schemaVersion": 41,
        "tags": [],
        "templating": {
            "list": template_list
        },
        "time": {
            "from": "now-6h",
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
    """Uploads the dashboard JSON file to Grafana.
    """

    # load information
    GRAFANA_URL = gf_conn['GF_URL']
    API_TOKEN = gf_conn['GF_API_KEY']
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Get folder UID
    filelist = os.listdir("./config_folders")   # Get everything in the config_folders directory
    folder_name = os.path.basename(os.path.dirname(file_path))  # Get the folder's name from the file path
    num = filelist.index(folder_name)  # Get the index of the folder's name in the filelist
    folder_uid = gf_conn[f'GF_FOLDER_UID{num}']

    # Load dashboard JSON
    def load_dashboard_json(path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    dashboard = load_dashboard_json(file_path)

    # Build payload 
    payload = {
        "dashboard": dashboard,
        "folderUid": f'{folder_uid}',   # to the target folder
        "overwrite": True   # allow upgrade
    }

    # Upload dashboard
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=headers,
        data=json.dumps(payload)
    )

    # Print output response
    print("Upload status:", response.status_code)
    print("Response text:", response.text)


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
        "orientation": "auto",
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
    Default: 3 panles in 1 row. 
    """

    # initial settings
    x, y = 0, 0
    num_panels = len(panels)
    width = max_cols // num_panels
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
    override = panel["override"]

    return title, table, chart_type, condition, groupby, gridPos, filters, override


def generate_sql(chart_type: str, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
    """Generate the SQL command from ChartSQLFactory. -> sql_builder.py
    """

    # Get Generator
    generator = ChartSQLFactory.get_generator(chart_type)

    # Generate SQL command
    panel_sql = generator.generate_sql(table, condition, groupby, filters, override)

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
        "refresh": 1, # refresh everytime when dashboard is loaded
        "type": "query"
      }

  return filter_json


def generate_filterSQL(filter_name: str, table: str) -> str:
  """Generate a template SQL command based on the given filter name.
  """
    
  # check filter type:
  if filter_name == "status":
    filter_sql = f"""
      SELECT DISTINCT 
      CASE WHEN shipped_datetime IS NULL THEN 'not shipped' ELSE 'shipped' END AS status 
      FROM {table}
      ORDER BY status
      """
  else:
    filter_sql = f"""
      SELECT DISTINCT {filter_name} FROM {table} ORDER BY {filter_name}
      """

  return filter_sql


# ============================================================
# === Overrides Generator ====================================
# ============================================================

def generate_override(override_name: str):
  if override_name == "shipped_datetime":
    override_list = [
    {
        "matcher": {
          "id": "byName",
          "options": "shipped"
        },
        "properties": [
          {
            "id": "color",
            "value": {
              "fixedColor": "#2ECC71",
              "mode": "fixed"
            }
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "not shipped"
        },
        "properties": [
          {
            "id": "color",
            "value": {
              "fixedColor": "#E74C3C",
              "mode": "fixed"
            }
          }
        ]
      }]

    return override_list