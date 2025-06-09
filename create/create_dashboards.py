import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from generate import *
from panel_builder import *
from other_builder import *

"""
This file generates all the dashboards json_file and saves them to a folder under `grafana_hgcdb_dashboard`.
    - The folders would have same names as the files in `config_folders`.
"""

# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Define the builder
panel_builder = PanelBuilder(datasource_uid)
filter_builder = FilterBuilder(datasource_uid)

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

        # assign_gridPos(panels)  # Assign gridPos to each panel
        panels_array = []
        template_list = []
        exist_filter = set()    # avoid adding same filters

        # Loop for every panel in a dashboard
        for panel in config_panels:
            # Generate the template json
            filters = panel["filters"]
            if filters:
                template_list.extend(filter_builder.build_template_list(filters, exist_filter))
            
        panels_array = panel_builder.build_from_config(config_panels)
            
        # Generate the dashboard json
        dashboard_json = generate_dashboard(dashboard["title"], panels_array, template_list)
        
        # Export the dashboard json to a file
        file_name = config.split(".")[0]
        save_dashboard_json(dashboard, dashboard_json, file_name)

print(" >> Dashboards generated successfully! =͟͟͞͞( 'ヮ' 三 'ヮ' =͟͟͞͞) \n")