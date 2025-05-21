import yaml
import os
from generate import*


def assign_gridPos(panels, width=8, height=6, max_cols=24):
    """Assign gridPos to each panel in the dashboard.
    """
    # initial settings
    x, y = 0, 0

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


def read_panel_info(panel):
    """Read panel information from the config file.
    """
    title = panel["title"]
    table = panel["table"]
    chart_type = panel["chart_type"]
    condition = panel["condition"]
    groupby = panel["groupby"]
    gridPos = panel["gridPos"]

    return title, table, chart_type, condition, groupby, gridPos


def save_dashboard_json(dashboard, dashboard_json, folder):
    """
    Save a dashboard JSON into Dashboards/<folder>/<dashboard_title>.json
    """
    # Get the safe title for the filename
    safe_title = dashboard["title"].replace(" ", "_")
    filename = safe_title + ".json"

    # create path
    folder_path = os.path.join("Dashboards", folder)
    os.makedirs(folder_path, exist_ok=True)  # create new Dashboards/folder

    path = os.path.join(folder_path, filename)

    # import file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dashboard_json, f, indent=2)
    
    print(f"Dashboard saved to {path}")



# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Loop for every config files
for config in filelist:
    
    # Load the dashboards
    with open(os.path.join(path, config), mode = 'r') as file:
        dashboards = yaml.safe_load(file)["dashboards"]

    # Loop for every dashboard in the config file
    for dashboard in dashboards:
        panels = dashboard["panels"]

        assign_gridPos(panels)  # Assign gridPos to each panel
        panels_array = []

        # Loop for every panel in the dashboard
        for panel in panels:
            
            title, table, chart_type, condition, groupby, gridPos = read_panel_info(panel)

            
            # Generate the sql query:
            if chart_type == "barchart":
                raw_sql = barchart_sql(table, condition, groupby)
            
            # Generate the panel json:
            panel_json = generate_panel(title, raw_sql, table, groupby, chart_type, gridPos)
            panels_array.append(panel_json)
            
        # Generate the dashboard json:
        dashboard_json = generate_dashboard(dashboard["title"], panels_array)
        
        # Export the dashboard json to a file:
        file_name = config.split(".")[0]
        save_dashboard_json(dashboard, dashboard_json, file_name)