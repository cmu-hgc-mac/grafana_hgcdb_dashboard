import yaml
import os
from generate import*

# Define the path of the config folders
path = "./config_folders"
filelist = os.listdir(path)

# Loop for generations of folders
for i, config in enumerate(filelist):
    folder_name = config.split(".")[0].replace("_", " ")
    folder_id = i
    generate_folder(folder_name, folder_id)
    


