from tool.helper import *

"""
This file defines the class for building the alert json file in Grafana and upload the alert.
Author: Xinyue (Joyce) Zhuang
"""

class AlertBuilder:
    def __init__(self, datasource_uid: str):
        self.datasource_uid = datasource_uid

    def generate_alerts(self, alert: dict, folder_name: str):
        """Build all alerts based on the given alert_dict.
        """ 
        # generate alert json
        alert_sql = self._generate_alertSQL(alert['parameter'], alert['table'])
        alert_json = self.generate_alert_rule(alert_sql, alert, alert['dashboard'], folder_name)
        
        return alert_json

    def generate_alert_rule(self, alertSQL: str, alertInfo: dict, dashboard_title: str, folder_name: str) -> dict:
        """Generate a json of the alert rule based on the given info
        """
        folderName = folder_name.replace("_", " ")

        # get dashboard uid
        dashboard_uid = create_uid(dashboard_title)

        # get alert rule uid
        alert_uid = create_uid(f"ALERT {alertInfo['title']}")

        # get folder uid
        if folderName == "General":  # invalid folder
            raise ValueError("[Error] Alert rule in invalid folder: General folder can not store alert rule.")
        else:
            folder_uid_map = gf_conn.get("GF_FOLDER_UIDS", {})
            if folderName not in folder_uid_map:
                raise ValueError(f"Dashboard Folder '{folderName}' not in GF_FOLDER_UIDS")
            folder_uid = folder_uid_map[folderName]

        # generate alert json
        alert_json =  {
            "title": f"ALERT: {alertInfo['title']}",
            "uid": alert_uid,
            "ruleGroup": alertInfo['title'],
            "folderUID": folder_uid,
            "condition": "C",
            "orgId": 1,
            "for": alertInfo["duration"],
            "interval": alertInfo["interval"],
            "noDataState": "NoData",
            "execErrState": "Error",
            "annotations": {
                "summary": "Auto-imported from UI"
            },
            "labels":alertInfo["labels"],
            "data": [
                {
                "refId": "A",
                "relativeTimeRange": {
                    "from": 600,
                    "to": 0
                },
                "datasourceUid": self.datasource_uid,
                "model": {
                    "refId": "A",
                    "format": "time_series",
                    "rawQuery": "true",
                    "rawSql": alertSQL
                }
                },
                {
                "refId": "B",
                "relativeTimeRange": {
                    "from": 0,
                    "to": 0
                },
                "datasourceUid": "__expr__",
                "model": {
                    "expression": "A",
                    "type": "reduce",
                    "reducer": "last",
                    "refId": "B"
                }
                },
                {
                "refId": "C",
                "relativeTimeRange": {
                    "from": 0,
                    "to": 0
                },
                "datasourceUid": "__expr__",
                "model": {
                    "expression": "B",
                    "type": "threshold",
                    "refId": "C",
                    "conditions": [
                    {
                        "type": "query",
                        "evaluator": {
                        "type": alertInfo["logicType"],
                        "params": alertInfo["threshold"]
                        },
                        "operator": {
                        "type": "and"
                        },
                        "query": {
                        "params": ["C"]
                        },
                        "reducer": {
                        "type": "last",
                        "params": []
                        }
                    }
                    ]
                }
                }
            ]
            } 

        return alert_json
    
    def _generate_alertSQL(self, parameter: str, source: str) -> str:
        alertSQL = f"""
        SELECT
            {parameter}
        FROM
            {source}
        LIMIT 1;
        """
        return alertSQL
    
    def save_alerts_json(self, alert: dict, alert_json: dict, folder: str):
        """Save alerts JSON into Alerts/<alerts_title>.json
        """ 
        # generate safe title for the filename
        safe_title = alert["title"].replace(" ", "_")
        filename = safe_title + ".json"

        # create path
        folder_path = os.path.join("Alerts", folder)
        os.makedirs(folder_path, exist_ok=True)

        path = os.path.join(folder_path, filename)

        # import file
        with open(path, "w", encoding="utf-8") as f:
            json.dump(alert_json, f, indent=2)

        print(f"Alerts saved to {path}")

    def upload_alerts(self, file_path: str):
        """Upload one alert JSON file into Grafana folder.
        """
        # reload gf_conn.yaml
        gf_conn.reload()

        # get folder and file name
        folder_name = os.path.basename(os.path.dirname(file_path)).replace("_", " ")
        file_name = os.path.basename(file_path).split(".")[0].replace("_", " ")
        
        # get folder uid
        if folder_name == "General":  # main dashboards: empty uid
            folder_uid = ""
        else:
            folder_uid_map = gf_conn.get("GF_FOLDER_UIDS", {})
            if folder_name not in folder_uid_map:
                raise ValueError(f"Dashboard Folder '{folder_name}' not in GF_FOLDER_UIDS")
            folder_uid = folder_uid_map[folder_name]

        with open(file_path, 'r', encoding='utf-8') as file:
            alert_json = json.load(file)

        # upload alerts
        try:
            client.upload_alert_json(alert_json, alert_json["uid"])

        except requests.RequestException as e:
            print(f"[ERROR] Failed to upload alert '{file_name}': {e}")
            raise