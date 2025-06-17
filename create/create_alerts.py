import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from tool.helper import *
from tool.alert_builder import AlertBuilder

"""
This script generates all alert JSON files, saves them to a folder under `grafana_hgcdb_dashboard`, and uploads them to Grafana.
Author: Xinyue (Joyce) Zhuang
"""

# Define the path of the config folders
filelist = os.listdir(CONFIG_FOLDER_PATH)

# Define the builder
alert_builder = AlertBuilder(GF_DS_UID)

# Loop for every config files
for config in filelist:

    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue
    
    # Load the alerts
    with open(os.path.join(CONFIG_FOLDER_PATH, config), mode = 'r') as file:
        tot_config = yaml.safe_load(file)
        # check if alerts exist:
        if "alert" not in tot_config:
            continue
        alerts = tot_config["alert"]
    
    # Loop for every panel in a dashboard
    for alert in alerts:
        # Generate the alert json
        folder_name = config.split(".")[0].replace("_", " ")
        alert_json = alert_builder.generate_alerts(alert, folder_name)

        # Export the dashbaord json to a file
        file_name = config.split(".")[0]
        alert_builder.save_alerts_json(alert, alert_json, file_name)

print(" >> Alerts generated successfully! ↙(`ヮ´ )↗ \n")


# Upload alerts
folder_list = os.listdir("./Alerts")
for folder in folder_list:
    file_list = os.listdir(f"./Alerts/{folder}")
    for file_name in file_list:
        if file_name.endswith(".json"):
            file_path = f"./Alerts/{folder}/{file_name}"
            try:
                alert_builder.upload_alerts(file_path)
            except Exception as e:
                print(f"[SKIPPED] Error uploading alert rule: {file_name} | Status: {e}")

print(" >> Alerts json files uploaded! (*ˉ︶ˉ*) \n")

# Clear GF_FOLDER_UIDS and GF_ALERT_UIDS map:
gf_conn.set("GF_FOLDER_UIDS", {})
gf_conn.set("GF_ALERT_UIDS", {})
gf_conn.save()
gf_conn.reload()
print(" >> GF_FOLDER_UIDS and GF_ALERT_UIDS map cleared! (๑•̀ㅂ•́)و✧ \n")

# Delete the alert files
remove_folder("Alerts", ALERTS_FOLDER_PATH)
print(" >> Alerts json files removed! o(≧v≦)o \n")