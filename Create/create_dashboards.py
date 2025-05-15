import yaml
import os

# Open the config file:
with open('dashboard_config.yaml', mode = 'r') as file:
    config = yaml.safe_load(file)

dashboards = config["dashboards"]