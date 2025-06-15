import os
import re
import shutil

import json
from typing import Any

import requests
import yaml

"""
This file contains all the helpers used in the dashboard.
    - The included helper classes/functions are:
        - ConfigLoader: load and modify the config file
        - GrafanaClient: all API to Grafana server
        - create_uid: create a unique uid based on its title
        - remove_folder: remove the folder that contains all json files
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
        else:
            raise ValueError(f"Invalid config name: {config_name}")
        
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
        self.api_token = api_token
    
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
                "sslmode": "disable",
                "alerting": True
            }
        }

        # Add data source
        response = requests.post(
            f"{self.base_url}/api/datasources",
            headers=self.headers,
            data=json.dumps(payload)
        )

        if response.status_code in [200, 201]:
            print(f"[Grafana] PostgreSQL data source '{name}' added as default... (`∀´σ) \n")
        elif response.status_code == 409:
            print(f"[Grafana] Data source '{name}' already exists.  (´･ω･`) \n")
        else:
            print(f"[Grafana] Failed to add data source: {response.status_code} ヽ(`Д´)ﾉ \n")
            print(response.text)
            response.raise_for_status()
    
    def create_or_get_folder(self, folder_name: str, folder_uid: str) -> str:
        """Create a folder if it doesn't exist, or return the existing folder's uid.
        """
        title, uid = folder_name, folder_uid

        # Fetch folder
        url = f"{self.base_url}/api/folders/{uid}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:     # folder exist
            return response.json()['uid']
        elif response.status_code == 404:   # create folder
            payload = {"title": title, "uid": uid}
            response = requests.post(f"{self.base_url}/api/folders", headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()['uid']
        else:
            raise Exception(f"Error checking folder: {response.status_code} - {response.text}")

    def upload_dashboard_json(self, dashboard_json: dict, folder_uid: str):
        """Upload a dashboard to a folder.
        """
        payload = {
            "dashboard": dashboard_json,
            "folderUid": folder_uid,
            "overwrite": True
        }

        # Upload dashboard
        url = f"{self.base_url}/api/dashboards/db"
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[Upload] Dashboard: {dashboard_json['title']} | Status: {response.status_code}")

        # print out error message
        if response.status_code != 200:
            print(f"[Upload] Dashboard: {dashboard_json['title']} | Error: {response.text}")
    
    def upload_alert_json(self, alert_json: dict):
        """Upload an alert-rule to a folder. 
           - Delete if the alert-rule uid already exist and upload the new one.
        """
        # Upload alert rule
        url = f"{self.base_url}/api/v1/provisioning/alert-rules"
        response = requests.post(url, headers=self.headers, json=alert_json)
        print(f"[Upload] {alert_json['title']} | Status: {response.status_code}")

        # print out error message
        if response.status_code not in [200, 201]:
            if response.status_code == 409:     # alert uid exist
                print("[Delete] Try deleting conflict Alert rule... (つД`)/")
                self.delete_alert_rule(alert_uid)
                self.upload_alert_json(alert_json, alert_uid)   # re-upload
            else:
                print(f"[Upload] {alert_json['title']} failed | Error: {response.text}")
     
    def delete_alert_rule(self, alert_uid: str):
        """Delete the specified alert rule.
           Author: Xinyue (Joyce) Zhuang
        """
        uid = alert_uid

        # Delete alert rule
        url = f"{self.base_url}/api/v1/provisioning/alert-rules/{uid}"
        response = requests.delete(url, headers=self.headers)
        print(f"[Delete] Alert rule UID: {uid} deleted | Status: {response.status_code}")

        # print out error message
        if not (response.status_code == 200 or response.status_code == 204):
            print(f"[Delete] Alert rule UID: {uid} failed | Error: {response.text}")


# ============================================================
# === Helper Functions =======================================
# ============================================================
def create_uid(title_name: str) -> str:
    """Create a unique uid based on its title.
       - For `folder`, `dashboard`, and `alert`.
       - The uid format is `lowercase-with-dash`.
    """
    safe_uid = re.sub(r'[^a-zA-Z0-9_ ]', '', title_name).lower().replace(' ', '-')
    return safe_uid

def remove_folder(folder_name: str, folder_path: str):
    """Remove the folder with the given path.
    """
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"[Folder] Removed folder: {folder_name}")
    else:
        print(f"[Folder] Folder not found: {folder_name}")


# ============================================================
# === Loaded Info ============================================
# ============================================================

# -- Load YAML Configuration --
gf_conn = ConfigLoader("gf_conn")
db_conn = ConfigLoader("db_conn")

# -- gf_conn.yaml --
gf_port         = gf_conn.get('GF_PORT')
gf_url          = f"http://127.0.0.1:{gf_port}"
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
institution     = db_conn.get("institution_abbr").upper()

# -- define GrafanaClient --
client = GrafanaClient(api_token, gf_url)

# -- set time zone --
time_zone_dict = {
    "CMU": "America/New_York",
    "IHEP": "Asia/Shanghai",
    "NTU": "Asia/Taipei",
    "TTU": "America/Chicago",
    "TIFR": "Asia/Kolkata",
    "UCSB": "America/Los_Angeles"
}
time_zone = time_zone_dict[institution]

# -- path --
dashboards_folder_path = "./Dashboards"
iv_plots_folder_path = "./IV_curves_plot"
alerts_folder_path = "./Alerts"