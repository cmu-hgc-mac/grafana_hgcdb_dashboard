import yaml
import os
from generate import*

"""
This file creates the folders from config_folders. 
    - Each folder would be named by replacing '_' to ' ' of the yaml_filename.
"""

# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Loop for generations of folders
for i, config in enumerate(filelist):
    folder_name = config.split(".")[0].replace("_", " ")    # rename the folder
    folder_id = i   # unique id for each folder
    generate_folder(folder_name, folder_id)
    
print("Folders are created! (ゝ∀･)")


