import requests
import json
import yaml

"""
This function is used to create a folder in Grafana for each institution.
"""

def create_folder(gf_conn_path='a_EverythingNeedToChange/gf_conn.yaml',
                db_conn_path='a_EverythingNeedToChange/db_conn.yaml'):
   
    # Read the conn files:
    with open(gf_conn_path, mode='r') as file:
        gf_conn = yaml.safe_load(file)

    with open(db_conn_path, mode='r') as file:
        db_conn = yaml.safe_load(file)
    
    # load information
    service_account_id = gf_conn['GF_SA_ID']
    grafana_url = gf_conn['GF_URL']
    username = gf_conn['GF_USER']
    password = gf_conn['GF_PASS']
    institution = db_conn['institution_abbr'].lower()
    headers = {
        "Content-Type": "application/json"
    }

    # Create the folder:
    folder_name = f"{institution}-dashboards"
    folder_payload = {
        "title": folder_name,
        "uid": f"{institution}-fldr" 
    }

    create_folder_response = requests.post(
        f"{grafana_url}/api/folders",
        headers=headers,
        auth=(username, password),
        data=json.dumps(folder_payload)
    )
    create_folder_response.raise_for_status()
    folder_uid = create_folder_response.json()['uid']
    print(f"Created folder '{folder_name}' with UID: {folder_uid}")


    # Update gf_conn.yaml: 
    gf_conn.update({
        'GF_FOLDER_NAME': str(folder_name),
        'GF_FOLDER_UID': str(folder_uid),
    })

    with open(gf_conn_path, 'w') as file:
        yaml.dump(gf_conn, file)
        print(f" >> Auto update for gf_conn.yaml successfully...")
