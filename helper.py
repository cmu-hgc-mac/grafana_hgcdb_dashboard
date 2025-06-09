import yaml
import os
import requests
from typing import Any

"""
This file contains all the helpers used in the dashboard.
    - The included helper classes/functions are:
        - GrafanaClient: all API to Grafana server
        - ConfigLoader: load the config file
        - create_uid: create a unique uid based on its title
        - information: loaded from config file
"""

class GrafanaClient:
    def __init__(self, api_token: str, grafana_url: str):
        self.base_url = grafana_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_or_get_folder(self, title: str, uid: str) -> str:
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
        payload = {
            "dashboard": dashboard_json,
            "folderUid": folder_uid,
            "overwrite": True
        }
        url = f"{self.base_url}/api/dashboards/db"
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[Upload] Dashboard: {dashboard_json['title']} | Status: {response.status_code}")


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
        with open(self.config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)
        print(f"[Config] Saved changes to {self.config_path}")


def create_uid(title_name: str) -> str:
    """Create a unique uid based on its title.
       - For `folder` and `dashboard`
    """
    return title_name.lower().replace(' ', '-')


# -- Load YAML Configuration --
gf_conn = ConfigLoader("gf_conn")
db_conn = ConfigLoader("db_conn")

grafana_url = gf_conn.get('GF_URL')
api_token = gf_conn.get('GF_API_KEY')
datasource_uid = gf_conn.get('GF_DATA_SOURCE_UID')

DBHostname = db_conn.get("db_hostname")
DBDatabase = db_conn.get("dbname")
DBUsername = db_conn.get("user")
DBPassword = db_conn.get("password")

# -- define GrafanaClient --
client = GrafanaClient(api_token, grafana_url)

