import os
import requests
import json
import yaml


def upload_dashboards(file_path):
    """Uploads the dashboard JSON file to Grafana.
    """

    # Load information from gf_conn.yaml
    with open('a_EverythingNeedToChange/gf_conn.yaml', 'r') as file:
        gf_conn = yaml.safe_load(file)

    GRAFANA_URL = gf_conn['GF_URL']
    API_TOKEN = gf_conn['GF_API_KEY']
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Get folder UID
    filelist = os.listdir("./config_folders")   # Get everything in the config_folders directory
    folder_name = os.path.basename(os.path.dirname(file_path))  # Get the folder's name from the file path
    num = filelist.index(folder_name)  # Get the index of the folder's name in the filelist
    folder_uid = gf_conn[f'GF_FOLDER_UID{num}']

    # Load dashboard JSON
    def load_dashboard_json(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    dashboard = load_dashboard_json(file_path)

    # Build payload 
    payload = {
        "dashboard": dashboard,
        "folderUid": f'{folder_uid}',
        "overwrite": True
    }

    # Upload dashboard
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=headers,
        data=json.dumps(payload)
    )

    # Print output response
    print("Upload status:", response.status_code)
    print("Response text:", response.text)



def main():
    os.system("python preSteps/get_api_key.py")
    os.system("python preSteps/add_datasource.py")
    os.system("python preSteps/modify_defasultsIni.py")
    os.system("python Create/create_folders.py")
    os.system("python Create/create_dashboards.py")

    # Upload dashboards:
    folder_list = os.listdir("./Dashboards")
    for folder in folder_list:
        file_list = os.listdir(f"./Dashboards/{folder}")
        for file in file_list:
            if file.endswith(".json"):
                file_path = f"./Dashboards/{folder}/{file}"
                upload_dashboards(file_path)

if __name__ == '__main__':
    main()