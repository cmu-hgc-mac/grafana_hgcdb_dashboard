import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from tool.helper import *
from tool.panel_builder import PanelBuilder
from tool.other_builder import FilterBuilder
from tool.dashboard_builder import DashboardBuilder

"""
This script generates all the dashboards json_file, saves them to a folder under `grafana_hgcdb_dashboard`, and uploads them to grafana.
    - The folders would have same names as the files in `config_folders`.
"""

# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Define the builder
panel_builder = PanelBuilder(GF_DS_UID)
filter_builder = FilterBuilder(GF_DS_UID)
dashboard_builder = DashboardBuilder()

# Loop for every config files
for config in filelist:

    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue
    
    # Load the dashboards
    with open(os.path.join(path, config), mode = 'r') as file:
        dashboards = yaml.safe_load(file)["dashboards"]

    # Loop for every dashboard in a config file
    for dashboard in dashboards:
        config_panels = dashboard["panels"]
        dashboard_title = dashboard["title"]

        # assign_gridPos(panels)  # Assign gridPos to each panel
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

print(" >> Dashboards generated successfully! =͟͟͞͞( 'ヮ' 三 'ヮ' =͟͟͞͞) \n")


# Upload dashboards
folder_list = os.listdir("./Dashboards")
for folder in folder_list:
    file_list = os.listdir(f"./Dashboards/{folder}")
    for file_name in file_list:
        if file_name.endswith(".json"):
            file_path = f"./Dashboards/{folder}/{file_name}"
            dashboard_builder.upload_dashboards(file_path)

print(" >> Dashboards uploaded! ᕕ( ᐛ )ᕗ \n")

# Remove dashboards json files
remove_folder("Dashboards", DASHBOARDS_FOLDER_PATH)
remove_folder("IV_curves_plot", IV_PLOTS_FOLDER_PATH)
print(" >> Dashboards json files removed! o(≧v≦)o \n")