import os
import requests
import json
import yaml
import subprocess
from create.generate import upload_dashboards
from time import sleep

"""
This file does EVERYTHING for you ;)
"""

def main():
    # Run preSteps in order
    subprocess.run(["python", "./preSteps/get_api_key.py"], check=True)
    sleep(0.5)    # wait for token to generate
    subprocess.run(["python", "./preSteps/add_datasource.py"], check=True)
    subprocess.run(["python", "./preSteps/modify_defaultsIni.py"], check=True)

    # Everything Need To Generate
    subprocess.run(["python", "create/create_folders.py"], check=True)
    sleep(0.5)    # wait for folders to add
    subprocess.run(["python", "create/create_dashboards.py"], check=True)

    # Upload dashboards
    folder_list = os.listdir("./Dashboards")
    for folder in folder_list:
        file_list = os.listdir(f"./Dashboards/{folder}")
        for file in file_list:
            if file.endswith(".json"):
                file_path = f"./Dashboards/{folder}/{file}"
                upload_dashboards(file_path)


# Allow Run
if __name__ == '__main__':
    main()