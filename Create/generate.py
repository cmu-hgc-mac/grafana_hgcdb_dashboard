import requests
import json
import yaml

"""
This file contains the functions to generate everything needed for the Grafana dashboards.
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

def generate_dashboard(dashboard_title, panels):
    """
    Generates a Grafana dashboard json file based on the given panels.
    """

    dashboard_uid = dashboard_title.lower().replace(" ", "-")
    
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
            "list": []
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


# ============================================================
# === Panel Generator ========================================
# ============================================================

def generate_panel(title,raw_sql, table, groupby, chart_type, gridPos):
    """
    Generate a panel json based on the given raw_sql, table, groupby, chart_type, and gridPos.

    example of gridPos (dict):
    {
        "h": 7,
        "w": 8,
        "x": 7,
        "y": 0
      }

    """

    # load information:
    datasource_uid = gf_conn['GF_DATA_SOURCE_UID']

    # create the panel json:
    panel_json = {
      "datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": f"{datasource_uid}"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {
            "axisBorderShow": False,
            "axisCenteredZero": False,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": False,
              "tooltip": False,
              "viz": False
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green"
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
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
        "stacking": "none",
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


# ============================================================
# === SQL Builder ============================================
# ============================================================

def barchart_sql(table, condition, groupby):
    """
    Generate a barchart panel's SQL command
    """

    if condition:
        where_condition = f"WHERE {condition}"
    else:
        where_condition = ""

    panel_sql = f"""
    SELECT 
        {groupby},
    COUNT(*) AS free_count
    FROM {table}
    {where_condition}
    GROUP BY {groupby}
    ORDER BY free_count DESC;
    """
    
    return panel_sql