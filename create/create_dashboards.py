import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from tool.helper import *
from tool import DashboardValidator
from tool import PanelBuilder, FilterBuilder, DashboardBuilder

"""
This script generates all the dashboards json_file, saves them to a folder under `grafana_hgcdb_dashboard`, and uploads them to grafana.
    - The folders would have same names as the files in `config_folders`.
"""

# Get the filelist from the config folder
filelist = os.listdir(CONFIG_FOLDER_PATH)

# Define the builder
panel_builder = PanelBuilder(GF_DS_UID)
filter_builder = FilterBuilder(GF_DS_UID)
dashboard_builder = DashboardBuilder()

# Check if succeed:
succeed = True      # assert every file generated successfully
failed_count = 0

# Loop for every config files
for config in filelist:

    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue

    # Validate the config file
    config_path = os.path.join(CONFIG_FOLDER_PATH, config)

    try:
        validator = DashboardValidator(config_path)
        print(f"\n[VALIDATING] Checking if the config file: <{config}> is valid...")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        continue

    ok = validator.run_all_checks()

    if not ok:  # skip invalid config file
        print(f"[WARNING] Validation failed for config: <{config}>. Skipping this file.\n")
        succeed = False
        failed_count += 1
        continue

    # Load the dashboards
    with open(config_path, mode = 'r') as file:
        dashboards = yaml.safe_load(file)["dashboards"]

    # Loop for every dashboard in a config file
    for dashboard in dashboards:
        config_panels = dashboard["panels"]
        dashboard_title = dashboard["title"]

        # Initialize setting
        panels_array = []
        template_list = []
        exist_filter = set()    # avoid adding same filters

        # Loop for every panel in a dashboard
        for panel in config_panels:
            # Generate the template json
            filters = panel["filters"]
            if filters:
                filter_json = filter_builder.build_template_list(filters, exist_filter)
                template_list.extend(filter_json)
            
        panels_array = panel_builder.generate_panels_json(dashboard_title, config_panels)
            
        # Generate the dashboard json
        dashboard_json = dashboard_builder.build_dashboard(dashboard_title, panels_array, template_list)
        
        # Export the dashboard json to a file
        file_name = config.split(".")[0]
        dashboard_builder.save_dashboard_json(dashboard, dashboard_json, file_name)

if succeed:
    print("\n >>>> All Dashboards json generated successfully! =͟͟͞͞( 'ヮ' 三 'ヮ' =͟͟͞͞) \n")
else:
    print(f"\n >>>> {failed_count} Dashboards json failed to generate. \n")


# Upload dashboards
try: 
    folder_list = os.listdir("./Dashboards")
    for folder in folder_list:
        file_list = os.listdir(f"./Dashboards/{folder}")
        for file_name in file_list:
            if file_name.endswith(".json"):
                file_path = f"./Dashboards/{folder}/{file_name}"
                try:
                    dashboard_builder.upload_dashboards(file_path)
                except Exception as e:
                    print(f"[SKIPPED] Error uploading dashboard: {file_name} | Status: {e}")

    print("\n >>>> Dashboards uploaded! ᕕ( ᐛ )ᕗ \n")

except:
    print("\n >>>> Dashboards upload failed. \n")
    raise 


# Remove dashboards json files
remove_folder("Dashboards", DASHBOARDS_FOLDER_PATH)
remove_folder("IV_curves_plot", IV_PLOTS_FOLDER_PATH)
print("\n >>>> Dashboards json files removed! o(≧v≦)o \n")