import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from tool.helper import *

"""
This file creates the folders from config_dashboard_folders. 
    - Each folder would be named by replacing '_' to ' ' of the yaml_filename.
"""

def generate_folder(type: str, folder_name: str):
    """Create Grafana folder or fetch if it already exists. Update UID map.
    """
    if folder_name == "General":  # default folder: no UID
        print("[Folder] Skipping folder creation: 'General' is default folder with no UID.")
        return ""
    else:
        folder_uid = create_uid(folder_name)

    # create or fetch folder
    # for Dashboards:
    if type == "dashboard":
        try:
            uid = client.create_or_get_folder(folder_name, folder_uid)
            gf_conn.set(f"GF_DASHBOARD_FOLDER_UIDS.{folder_name}", uid)
            gf_conn.save()
            print(f"[Folder] Created or verified [DASHBOARD] folder '{folder_name}'")

        except requests.RequestException as e:
            print(f"[ERROR] Failed to create or fetch [DASHBOARD] folder '{folder_name}': {e}")
            raise

    # for Alerts:
    if type == "alert":
        uid = client.create_or_get_folder(folder_name, folder_uid)
        gf_conn.set(f"GF_ALERT_FOLDER_UIDS.{folder_name}", uid)
        gf_conn.save()
        print(f"[Folder] Created or verified [ALERT] folder '{folder_name}'")


# Load all .yaml files in config_dashboard_folders/
dashboard_folder_configs = os.listdir("./config_dashboard_folders")

for config in dashboard_folder_configs:
    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue

    folder_name = config.split(".")[0].replace("_", " ")
    generate_folder("dashboard", folder_name)

print(" >> Dashboard Folders are in Grafana! (ゝ∀･) \n")


# Load all .yaml files in config_alert_folders/
alert_folder_configs = os.listdir("./config_alert_folders")

for config in alert_folder_configs:
    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue

    folder_name = config.split(".")[0].replace("_", " ")
    generate_folder("alert", folder_name)

print(" >> Alert Folders are in Grafana! o(≧v≦)o \n")