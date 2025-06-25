import os
import re
import shutil

import csv
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
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._data = self._load()
    
    # -- Connection Confiuration Functions --
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
        datasource_name: str, datasource_uid: str,
        db_host: str, db_port: str,
        db_name: str, db_user: str, db_password: str
    ):
        """Add a PostgreSQL data source to Grafana using current API token.
        """
        payload = {
            "name": datasource_name,
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
            "uid": datasource_uid,
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
            print(f"[Grafana] PostgreSQL data source '{datasource_name}' added as default... (`∀´σ) \n")
        elif response.status_code == 409:
            print(f"[Grafana] Data source '{datasource_name}' already exists.  (´･ω･`) \n")
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
    
    def upload_alert_json(self, alert_json: dict, alert_uid: str):
        """Upload an alert-rule to a folder. 
           - Update if the alert rule uid exist.
        """
        # Upload alert rule
        url = f"{self.base_url}/api/v1/provisioning/alert-rules"
        response = requests.post(url, headers=self.headers, json=alert_json)
        print(f"[Upload] {alert_json['title']} | Status: {response.status_code}")

        # print out error message
        if response.status_code not in [200, 201]:
            if response.status_code == 409:     # alert uid exist
                print(f"[ERROR] {alert_json['title']} already exist. Trying update... (つД`)/")
                update_url = f"{self.base_url}/api/v1/provisioning/alert-rules/{alert_uid}"
                update_response = requests.put(update_url, headers=self.headers, json=alert_json)
                print(f"[Update] {alert_json['title']} | Status: {update_response.status_code}")
                if update_response.status_code != 200:
                    print(f"[Update] {alert_json['title']} failed | Error: {update_response.text}")
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
    
    def get_all_alert_rules(self) -> list:
        """Get all alert rules from Grafana. Output all the uids.
        """
        # Get the list of all alert rules
        url = f"{self.base_url}/api/v1/provisioning/alert-rules"
        response = requests.get(url, headers=self.headers)

        # Convert the response
        data_json = json.loads(response.text)

        # Output result
        alert_uids = []
        for rule in data_json:
            alert_uids.append(rule['uid'])

        return alert_uids
    
    def create_contact_point(self, name: str, addresses: list):
        """ Create email contact points.
            - Also, check if there exists contact point with the same name, 
              if so, delete the existing one and upload a new one.
        """
        uid = create_uid(name)

        existing_cps = self.list_contact_points_uid()
        to_delete_uid = None

        for cp_uid in existing_cps:
            if cp_uid == uid:
                to_delete_uid = cp_uid
                print(f"Found existing contact point: {name} (UID: {cp_uid}) — will delete")
                break

        if to_delete_uid:
            self.delete_contact_point(to_delete_uid)

        payload = {
            "name": name,
            "type": "email",
            "uid": uid,
            "settings": {
                "addresses": ",".join(addresses)
            }
        }

        url = f"{self.base_url}/api/v1/provisioning/contact-points"
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 202:
            print(f"[Create] {response.status_code} | Contact Point {name} successfully created.(=ﾟωﾟ)ﾉ")
        else:
            print(f"[Create] {response.status_code} | {response.text}")

    def list_contact_points_uid(self):
        """ This function asks grafana to return all the uids for contact points.
        """

        url = f"{self.base_url}/api/v1/provisioning/contact-points"
        response = requests.get(url, headers=self.headers)

        # Convert the response
        data_json = json.loads(response.text)

        # Output result
        contacts_uids = []
        for rule in data_json:
            contacts_uids.append(rule['uid'])

        return contacts_uids

    def delete_contact_point(self, uid, fallback_receiver: str = "grafana-default-email"):
        """ Delete one contact point with uid.
        """
        tree = self.get_policy_tree()
        routes = tree.get("routes", [])
        if tree.get("receiver") == uid:
            tree["receiver"] = fallback_receiver
            print(f"[Update] Root receiver changed from {uid} → {fallback_receiver}")
        #filter the route with the contact point that we want to delete
        new_routes = [r for r in routes if r.get("receiver") != uid]

        if len(new_routes) < len(routes):
            tree["routes"] = new_routes
            self.put_policy_tree(tree)
            print(f"[Delete] removed {uid} from routes")
        else:
            print(f"[Delete] No policy used {uid}")

        url = f"{self.base_url}/api/v1/provisioning/contact-points/{uid}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code in [200, 202, 204]:
            print(f"[Delete] Deleted contact point UID: {uid}")
        else:
            print(f"[Delete] Failed to delete UID {uid} | {response.status_code} | {response.text}")

    def delete_all_contact_points(self):
        """Delete all contact points that are deletable via API.
        """
        url = f"{self.base_url}/api/v1/provisioning/contact-points"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"[Error] Failed to fetch contact points | {response.status_code} | {response.text}")
            return

        contact_points = response.json()

        for cp in contact_points:
            uid = cp.get("uid")

            if not uid:
                print(f"[Skip] Skipping unnamed or malformed contact point: {cp}")
                continue

            self.delete_contact_point(uid)

    def get_policy_tree(self):
        """Get current policy tree
        """
        url = f"{self.base_url}/api/v1/provisioning/policies"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def put_policy_tree(self, tree: dict):
        """Update policy tree
        """
        url = f"{self.base_url}/api/v1/provisioning/policies"
        response = requests.put(url, headers=self.headers, json=tree)
        response.raise_for_status()

        if response.status_code in [204,202]:
            print("[Update] Notification policies successfully updated.")
        else:
            print(f"[Update] Failed to set up notification system|{response.status_code}|{response.text}")

    def delete_notification_policy_tree(self):
        """Delete the entire notification policy tree.
        """
        url = f"{self.base_url}/api/v1/provisioning/policies"
        response = requests.delete(url, headers=self.headers)

        if response.status_code in [200, 202, 204]:
            print("[Delete] Notification policy tree deleted successfully.")
        else:
            print(f"[Delete] Failed to delete policy tree | {response.status_code} | {response.text}")
            response.raise_for_status()


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

def get_distinct_column_name(table_name: str) -> str:
    """Get the name of the distinct column in the given table.
    """
    with open(f"{DB_INFO_PATH}/{table_name}.csv", 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            return list(row.keys())[0]


# ============================================================
# === Loaded Info ============================================
# ============================================================

# -- Path --
SETTING_FOLDER_PATH     = "./a_EverythingNeedToChange"
CONFIG_FOLDER_PATH      = "./config_folders"
# DB_INFO_PATH            = "../HGC_DB_postgres/dbase_info/postgres_tables"
DB_INFO_PATH            = "./tool/postgres_tables"
DASHBOARDS_FOLDER_PATH  = "./Dashboards"
IV_PLOTS_FOLDER_PATH    = "./IV_curves_plot"
ALERTS_FOLDER_PATH      = "./Alerts"
CONTACT_FOLDER_PATH     = f"{CONFIG_FOLDER_PATH}/contact_configs"

DB_CONN_PATH            = f"{SETTING_FOLDER_PATH}/db_conn.yaml"
GF_CONN_PATH            = f"{SETTING_FOLDER_PATH}/gf_conn.yaml"

# -- load YAML Configuration --
db_conn = ConfigLoader(DB_CONN_PATH)
gf_conn = ConfigLoader(GF_CONN_PATH)

# -- Grafana Connection Info --
GF_PORT         = gf_conn.get('GF_PORT')
GF_URL          = f"http://127.0.0.1:{GF_PORT}"
GF_API_KEY      = gf_conn.get('GF_API_KEY')
GF_USER         = gf_conn.get('GF_USER')
GF_PASS         = gf_conn.get('GF_PASS')
GF_DS_NAME      = gf_conn.get('GF_DATA_SOURCE_NAME')
GF_DS_UID       = gf_conn.get('GF_DATA_SOURCE_UID')

# -- PostgreSQL Connection Info --
DB_HOST         = db_conn.get("db_hostname")
DB_NAME         = db_conn.get("dbname")
DB_USER         = db_conn.get("user")
DB_PASSWORD     = db_conn.get("password")
DB_PORT         = db_conn.get("port")
INSTITUTION     = db_conn.get("institution_abbr").upper()

# -- HGCDB Info --
TIME_COLUMNS = [
    "date_encap", "time_encap", # back_endcap, front_endcap
    "date_bond", "time_bond",   # back_wirebond, front_wirebond
    "date_inspect", "time_inspect", # bp_inspect, hxb_inspect, module_inspect, proto_inspect
    "bp_received", "bp_inspected",  # baseplate
    "hxb_received", "hxb_inspected", "hxb_tested", # hexaboard
    "sen_received", # sensor
    "date_verify_received", # hexaboard, sensor, baseplate
    "xml_gen_datetime",
    "date_test", "time_test", # hxb_pedestal_test, mod_hxb_other_test, module_iv_test, module_pedestal_test
    "ass_run_date", "ass_time_begin", "ass_time_end", "cure_date_end", "cure_time_end", # module_assembly, proto_assembly
    "assembled", "inspected", "wb_front", "wb_back", "encap_front", "encap_back", 
        "inspect_sec", "test_iv", "test_ped", "packed_datetime", "shipped_datetime",  # module_info
    "log_timestamp" # particulate_counts, temp_humidity
]

PREFIX = {
    "baseplate": "bp",
    "hexaboard": "hxb",
    "sensor": "sen",
}

# table list that should use `no` as distinct postfix
POSTFIX = [
    "baseplate",
    "sensor"
]

# number of modules show:
N_MODULE_SHOW = 15

# -- Set time_zone --
INSTITUTION_TIMEZONES = {
    "CMU": "America/New_York",
    "IHEP": "Asia/Shanghai",
    "NTU": "Asia/Taipei",
    "TTU": "America/Chicago",
    "TIFR": "Asia/Kolkata",
    "UCSB": "America/Los_Angeles"
}
TIME_ZONE = INSTITUTION_TIMEZONES[INSTITUTION]

# -- Set GrafanaClient --
client = GrafanaClient(GF_API_KEY, GF_URL)
