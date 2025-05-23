import requests
import json
import yaml

"""
Add the PostgreSQL data source to Grafana as default.
"""

# Define paths:
gf_conn_path = 'a_EverythingNeedToChange/gf_conn.yaml'
db_conn_path = 'a_EverythingNeedToChange/db_conn.yaml'

# Read the conn files:
with open(gf_conn_path, mode='r') as file:
    gf_conn = yaml.safe_load(file)
with open(db_conn_path, mode='r') as file:
    db_conn = yaml.safe_load(file)

# load information:
db_name = db_conn['dbname']
db_port = db_conn['port']
db_host = db_conn['db_hostname']
db_user = db_conn['user']
db_password = db_conn['password']
gf_api_key = gf_conn['GF_API_KEY'] # check if it is not empty
grafana_url = gf_conn['GF_URL']
gf_datasource_name = gf_conn['GF_DATA_SOURCE_NAME']
gf_datasource_uid = gf_conn['GF_DATA_SOURCE_UID']

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {gf_api_key}"
}

# payload for Postgres data source:
ds_payload = {
    "name": gf_datasource_name,
    "type": "postgres",
    "access": "proxy",
    "url": f"{db_host}:{db_port}",
    "database": db_name,
    "user": db_user,
    "secureJsonData": {
        "password": db_password
    },
    "isDefault": True,
    "editable": True,
    "uid": gf_datasource_uid,
    "jsonData": {
        "sslmode": "disable"
    }
}

# key_parameter checks:
if not gf_api_key:
    print("GF_API_KEY is not set in the gf_conn.yaml file.")
    exit(1)


# Add database source
try:
    response = requests.post(
        f"{grafana_url}/api/datasources",
        headers=headers,
        data=json.dumps(ds_payload)
    )
    
    if response.status_code in [200, 201]:
        print(f"PostgreSQL data source: {gf_datasource_name} added to Grafana as default...")
        
    elif response.status_code == 409:
        print("Datasource already exists.")

    else:
        print("Failed to add data source.")
        print("Status:", response.status_code)
        print(response.text)
        
except Exception as e:
    print("Error ocurr while adding the data source.")
    print(e)
    
    