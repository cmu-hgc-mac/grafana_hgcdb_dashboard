import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from tool.generate import generate_folder

"""
This file creates the folders from config_folders. 
    - Each folder would be named by replacing '_' to ' ' of the yaml_filename.
"""

# Load all .yaml files in config_folders/
folder_configs = os.listdir("./config_folders")

for config in folder_configs:
    # skip non-yaml files
    if not config.endswith(".yaml"):
        continue

    folder_name = config.split(".")[0].replace("_", " ")
    generate_folder(folder_name)

print(" >> Folders are in Grafana! (ゝ∀･) \n")