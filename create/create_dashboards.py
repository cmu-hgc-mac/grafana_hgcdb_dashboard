import yaml
import os
from generate import *

"""
This file generates all the dashboards json_file and saves them to a folder under `grafana_hgcdb_dashboard`.
    - The folders would have same names as the files in `config_folders`.
"""

# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Loop for every config files
for config in filelist:
    
    # Load the dashboards
    with open(os.path.join(path, config), mode = 'r') as file:
        dashboards = yaml.safe_load(file)["dashboards"]

    # Loop for every dashboard in a config file
    for dashboard in dashboards:
        panels = dashboard["panels"]

        assign_gridPos(panels)  # Assign gridPos to each panel
        panels_array = []
        template_list = []

        # Loop for every panel in a dashboard
        for panel in panels:

            # Load information
            title, table, chart_type, condition, groupby, gridPos = read_panel_info(panel)
            
            # # Generate the sql query
            raw_sql = generate_sql(chart_type, table, condition, groupby)   # -> from sql_builder.py
            
            # Generate the panel json
            panel_json = generate_panel(title, raw_sql, table, groupby, chart_type, gridPos)
            panels_array.append(panel_json)

            # Generate the template json
            for elem in groupby:
                filter_sql = generate_filterSQL(elem, table)
                filter_json = generate_filter(elem, filter_sql)
                template_list.append(filter_json)
            
        # Generate the dashboard json
        dashboard_json = generate_dashboard(dashboard["title"], panels_array, template_list)
        
        # Export the dashboard json to a file
        file_name = config.split(".")[0]
        save_dashboard_json(dashboard, dashboard_json, file_name)

print(" >> Dashboards generated successfully! =͟͟͞͞( 'ヮ' 三 'ヮ' =͟͟͞͞)")