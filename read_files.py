import yaml
import os
from create_panels import *

# Get Information of dashboards and panels
with open('dashboard_config.yaml', mode = 'r') as file:
    config = yaml.safe_load(file)

dashboards = config["dashboards"]

for dashboard in dashboards:
    panels = dashboard["panels"]
    for panel in panels:
        table = panel["table"]
        condition = panel["condition"]
        groupby = panel["groupby"]
        filters = panel["filters"]
        print(create_Bar(table, condition, groupby, filters))



