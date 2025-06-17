import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from tool.helper import *

"""
This script generates the folders from config_dashboard_folders to Grafana. 
    - Each folder would be named by replacing '_' to ' ' of the yaml_filename.
    - Dashboards in `General.yaml` will be upload to the general folder in Grafana
"""

def generate_folder(folder_name: str):
    """Create Grafana folder or fetch if it already exists. Update UID map.
    """
    if folder_name == "General":  # default folder: no UID
        print("[Folder] Skipping folder creation: 'General' is default folder with no UID.")
        return ""
    else:
        folder_uid = create_uid(folder_name)

    # create or fetch folder
    try:
        uid = client.create_or_get_folder(folder_name, folder_uid)
        gf_conn.set(f"GF_FOLDER_UIDS.{folder_name}", uid)
        gf_conn.save()
        print(f"[Folder] Created or verified [DASHBOARD] folder '{folder_name}'")

    except requests.RequestException as e:
        print(f"[ERROR] Failed to create or fetch [DASHBOARD] folder '{folder_name}': {e}")
        raise


# Load all .yaml files in config_dashboard_folders/
filelist = os.listdir(CONFIG_FOLDER_PATH)

for config in filelist:
    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue

    folder_name = config.split(".")[0].replace("_", " ")
    generate_folder(folder_name)

print(" >> Dashboard Folders are in Grafana! (ゝ∀･) \n")