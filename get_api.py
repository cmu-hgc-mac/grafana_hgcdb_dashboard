import yaml
import requests
import json

"""
This function is used to create a service account and get the API key to connect to Grafana.
"""

def get_api(grafana_conn_path='a_EverythingNeedToChange/gf_conn.yaml',
                db_conn_path='a_EverythingNeedToChange/db_conn.yaml'):

    # Read the conn files:
    with open(grafana_conn_path, mode='r') as file:
        gf_conn = yaml.safe_load(file)

    with open(db_conn_path, mode='r') as file:
        db_conn = yaml.safe_load(file)

    # load information: 
    GRAFANA_URL = gf_conn['GF_URL']
    USERNAME = gf_conn['GF_USER']
    PASSWORD = gf_conn['GF_PASS']
    host = db_conn['db_hostname']
    db_name = db_conn['dbname']
    headers = {
        'Content-Type': 'application/json',
    }


    # Create service account
    payload = {
        "name": f"{host}-service-account",
        "role": "Admin"
    }

    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/serviceaccounts",
            headers=headers,
            auth=(USERNAME, PASSWORD),
            data=json.dumps(payload)
        )

        print("Service account created successfully...", response.status_code)

        service_account = response.json()
        service_account_id = service_account['id']
        print(f"Service account ID: {service_account_id}")

    except Exception as e:
        print("Failed to create service account.")
        print(e)
        return None


    # Get the token/API key:
    token_payload = {
        "name": f"{host}-sa-token",
        "secondsToLive": 0 # default: allow to be valid forever
    }

    try:
        token_response = requests.post(
            f"{GRAFANA_URL}/api/serviceaccounts/{service_account_id}/tokens",
            headers=headers,
            auth=(USERNAME, PASSWORD),
            data=json.dumps(token_payload)
        )

        print("Token created successfully...", token_response.status_code)

        token = token_response.json() 
        token_key = token['key']
        print(f"API key: {token_key}")

    except Exception as e:
        print("Failed to create token.")
        print(e)
        return None
    

    # Update gf_conn.yaml: 
    gf_conn.update({
        'GF_SA_ID': service_account_id,
        'GF_SA_NAME': f"{host}-service-account",
        'GF_API_KEY': token_key,
        'GF_DATA_SOURCE_NAME': db_name
    })

    with open(grafana_conn_path, 'w') as file:
        yaml.dump(gf_conn, file)
        print(f"Updated {grafana_config_path} with service account and API key...")



# Run the function:
get_api_key()