import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helper import *

"""
Create a service account and get the API key to connect to Grafana.
"""

sa_name = f"{institution}-service-account"
token_name = f"{institution}-sa-token"

# Create service account
sa_id, api_key = client.create_service_account_and_token(sa_name, token_name, gf_username, gf_password)

# Update gf_conn
gf_conn.set('GF_SA_ID', sa_id)
gf_conn.set('GF_SA_NAME', sa_name)
gf_conn.set('GF_API_KEY', api_key)
gf_conn.set('GF_DATA_SOURCE_NAME', str(f"{institution}-{db_name}".upper()))
gf_conn.set('GF_DATA_SOURCE_UID', "mac-postgres-db")

gf_conn.save()
gf_conn.reload()

print(f"Auto update for gf_conn.yaml successfully! ヾ(´ωﾟ｀)")