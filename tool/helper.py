import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Any

import requests
import yaml

"""
This file contains all the helpers used in the dashboard.
    - The included helper classes/functions are:
        - GrafanaClient: all API to Grafana server
        - ConfigLoader: load the config file
        - create_uid: create a unique uid based on its title
        - information: loaded from config file
"""

# ============================================================
# === Helper Classes =========================================
# ============================================================
class ConfigLoader:
    def __init__(self, config_name: str):
        if config_name == "gf_conn":
            self.config_path = "./a_EverythingNeedToChange/gf_conn.yaml"
        elif config_name == "db_conn":
            self.config_path = "./a_EverythingNeedToChange/db_conn.yaml"
        
        self._data = self._load()
    
    def _load(self) -> dict:
        """Load the config file.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"[Config] File not found: {self.config_path}")
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file) or {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get value via dotted path.
        """
        keys = key_path.split('.')
        val = self._data
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any):
        """Set value via dotted path.
        """
        keys = key_path.split('.')
        d = self._data
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value
    
    def save(self):
        """Save the changes to the config file.
        """
        with open(self.config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)
        print(f"[Config] Saved changes to {self.config_path}")
    
    def reload(self):
        """Reload the data from the config file.
        """
        self._data = self._load()


class GrafanaClient:
    def __init__(self, api_token: str, gf_url: str):
        self.base_url = gf_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_service_account_and_token(self, sa_name: str, token_name: str, username: str, password: str) -> str:
        """Create a service account and return the API token string.
        """
        # Create service account
        sa_payload = {
            "name": sa_name,
            "role": "Admin"
        }

        sa_res = requests.post(
            f"{self.base_url}/api/serviceaccounts",
            headers={"Content-Type": "application/json"},
            auth=(username, password),
            data=json.dumps(sa_payload)
        )
        sa_res.raise_for_status()
        sa_id = sa_res.json()["id"]

        # Create token
        token_payload = {
            "name": token_name,
            "secondsToLive": 0  # forever
        }

        token_res = requests.post(
            f"{self.base_url}/api/serviceaccounts/{sa_id}/tokens",
            headers={"Content-Type": "application/json"},
            auth=(username, password),
            data=json.dumps(token_payload)
        )
        token_res.raise_for_status()
        api_key = token_res.json()["key"]
        print(f"[Grafana] Service account '{sa_name}' and API token created.")

        return sa_id, api_key

    def add_postgres_datasource(
        self, 
        name: str, uid: str,
        db_host: str, db_port: str,
        db_name: str, db_user: str, db_password: str
    ):
        """Add a PostgreSQL data source to Grafana using current API token.
        """

        payload = {
            "name": name,
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
            "uid": uid,
            "jsonData": {
                "sslmode": "disable"
            }
        }

        response = requests.post(
            f"{self.base_url}/api/datasources",
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code in [200, 201]:
            print(f"[Grafana] PostgreSQL data source '{name}' added as default... (`∀´σ)")
        elif response.status_code == 409:
            print(f"[Grafana] Data source '{name}' already exists.  (´･ω･`)")
        else:
            print(f"[Grafana] Failed to add data source: {response.status_code} ヽ(`Д´)ﾉ")
            print(response.text)
            response.raise_for_status()
    
    def create_or_get_folder(self, title: str, uid: str) -> str:
        """Create a folder if it doesn't exist, or return the existing folder's uid.
        """
        url = f"{self.base_url}/api/folders/{uid}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()['uid']
        else:
            payload = {"title": title, "uid": uid}
            response = requests.post(f"{self.base_url}/api/folders", headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()['uid']
    
    def upload_dashboard(self, dashboard_json: dict, folder_uid: str):
        """Upload a dashboard to a folder.
        """
        payload = {
            "dashboard": dashboard_json,
            "folderUid": folder_uid,
            "overwrite": True
        }
        url = f"{self.base_url}/api/dashboards/db"
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[Upload] Dashboard: {dashboard_json['title']} | Status: {response.status_code}")


# ============================================================
# === Helper Functions =======================================
# ============================================================
def create_uid(title_name: str) -> str:
    """Create a unique uid based on its title.
       - For `folder` and `dashboard`
    """
    return title_name.lower().replace(' ', '-')


# ============================================================
# === Loaded Info ============================================
# ============================================================

# -- Load YAML Configuration --
gf_conn = ConfigLoader("gf_conn")
db_conn = ConfigLoader("db_conn")

# -- gf_conn.yaml --
gf_url          = gf_conn.get('GF_URL')
api_token       = gf_conn.get('GF_API_KEY')
gf_username     = gf_conn.get('GF_USER')
gf_password     = gf_conn.get('GF_PASS')
datasource_name = gf_conn.get('GF_DATA_SOURCE_NAME')
datasource_uid  = gf_conn.get('GF_DATA_SOURCE_UID')

# -- db_conn.yaml --
db_host         = db_conn.get("db_hostname")
db_name         = db_conn.get("dbname")
db_user         = db_conn.get("user")
db_password     = db_conn.get("password")
db_port         = db_conn.get("port")
institution     = db_conn.get("institution_abbr")

# -- define GrafanaClient --
client = GrafanaClient(api_token, gf_url)