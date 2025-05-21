import yaml
import requests
import json

"""
This function creates a service account and get the API key to connect to Grafana.
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
gf_url = gf_conn['GF_URL']
gf_username = gf_conn['GF_USER']
gf_password = gf_conn['GF_PASS']
db_name = db_conn['dbname']
institution = db_conn['institution_abbr']

headers = {
    'Content-Type': 'application/json',
}


# Create service account
sa_payload = {
    "name": f"{institution}-service-account",
    "role": "Admin"
}

try:
    create_response = requests.post(
        f"{gf_url}/api/serviceaccounts",
        headers=headers,
        auth=(gf_username, gf_password),
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
    exit(1)


# Get the token/API key:
token_payload = {
    "name": f"{institution}-sa-token",
    "secondsToLive": 0  # default: allow to be valid forever
}

try:
    token_response = requests.post(
        f"{gf_url}/api/serviceaccounts/{service_account_id}/tokens",
        headers=headers,
        auth=(gf_username, gf_password),
        data=json.dumps(token_payload)
    )

    print("Token created successfully...", token_response.status_code)

    token = token_response.json() 
    token_key = token['key']
    print(f"API key: {token_key}")

except Exception as e:
    print("Failed to create token.")
    print(e)
    exit(1)


# Update gf_conn.yaml: 
gf_conn.update({
    'GF_SA_ID': service_account_id,
    'GF_SA_NAME': f"{institution}-service-account",
    'GF_API_KEY': token_key,
    'GF_DATA_SOURCE_NAME': str(f"{institution}-{db_name}".upper()),
    'GF_DATA_SOURCE_UID': str(f"{institution}-{db_name}".lower())
})

with open(gf_conn_path, 'w') as file:
    yaml.dump(gf_conn, file)
    print(f"Auto update for gf_conn.yaml successfully...")

