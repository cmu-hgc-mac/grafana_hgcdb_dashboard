import yaml
import requests
import json

"""
This function is used to create a service account and get the API key to connect to Grafana.
"""

def get_api(gf_conn_path='a_EverythingNeedToChange/gf_conn.yaml',
            db_conn_path='a_EverythingNeedToChange/db_conn.yaml'):

    # Read the conn files:
    with open(gf_conn_path, mode='r') as file:
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
    sa_payload = {
        "name": f"{host}-service-account",
        "role": "Admin"
    }

    try:
        create_response = requests.post(
            f"{GRAFANA_URL}/api/serviceaccounts",
            headers=headers,
            auth=(USERNAME, PASSWORD),
            data=json.dumps(sa_payload)
        )

        create_response.raise_for_status()

        print("Service account created successfully...", create_response.status_code)

        service_account = create_response.json()
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
        exit()
    

    # Update gf_conn.yaml: 
    gf_conn.update({
        'GF_SA_ID': service_account_id,
        'GF_SA_NAME': f"{host}-service-account",
        'GF_API_KEY': token_key,
        'GF_DATA_SOURCE_NAME': db_name
    })

    with open(grafana_conn_path, 'w') as file:
        yaml.dump(gf_conn, file)
        print(f"Updated {gf_conn_path} with service account and API key...")

"""
Unfortunatly if you failed to get the token_key, you will have to create a new service account and get a new token due to the secuirty limitation of Grafana.
"""


# Run the function:
if __name__ is '__main__':
    get_api()