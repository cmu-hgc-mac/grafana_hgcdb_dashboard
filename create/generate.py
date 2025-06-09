import requests
import json
import yaml
import os
from create.sql_builder import ChartSQLFactory
from helper import *

"""
This file contains all the functions that are needed to generate everything for the Grafana dashboards.
"""

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
