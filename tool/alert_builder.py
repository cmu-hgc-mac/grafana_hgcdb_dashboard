from tool.helper import *

"""
This file defines the class for building the alert json file in Grafana and upload the alert.
"""

class AlertBuilder:
    def __init__(self, datasource_uid: str):
        self.datasource_uid = datasource_uid

    def generate_alerts(self, alert: dict):
        """Build all alerts based on the given alert_dict.
        """ 
        # generate alert json
        alert_sql = self._generate_alertSQL(alert['parameter'], alert['table'])
        alert_json = self.generate_alert_rule(alert_sql, alert, alert['dashboard'])
        
        return alert_json

    def generate_alert_rule(self, alertSQL: str, alertInfo: dict, dashboard_title: str) -> dict:
        # Folder uid should be added to the alert json, new para input for it
        """Generate a json of the alert rule based on the given info
        """
        # get dashboard uid
        dashboard_uid = create_uid(dashboard_title)

        # generate alert json
        alert_json =  {
            "title": f"ALERT: {alertInfo['title']}",
            "ruleGroup": alertInfo['title'],
            "noDataState": "Alerting",
            "execErrState": "Alerting",
            "for": alertInfo['duration'],
            "orgId": 1,
            "condition": "B",
            "annotations": {
                "summary": alertInfo['summary']
            },
            "labels": alertInfo['labels'],
            "data": [
                {
                    "refId": "A",
                    "queryType": "",
                    "relativeTimeRange": { 
                        "from": 600, 
                        "to": 0 
                    }, # read the data in the time interval from 10 min before
                    "datasourceUid": self.datasource_uid,
                    "model": {
                        "rawSql": alertSQL,
                        "refId": "A",
                        "intervalMs": 1000,
                        "maxDataPoints": 43200,
                        "hide": False, 
                        "format": "table"
                    }
                },
                {
                    "refId": "B",
                    "queryType": "",
                    "relativeTimeRange": { "from": 0, "to": 0 },
                    "datasourceUid": self.datasource_uid,
                    "model": {
                        "conditions": [
                            {
                                "evaluator": { 
                                    "type": alertInfo["logicType"], 
                                    "params": [alertInfo['threshold']] 
                                },
                                "operator": { "type": "and" },
                                "query": { "params": ["A"] },
                                "reducer": { "type": "last", "params": [] },
                                "type": "query"
                            }
                        ],
                        "type": "classic_conditions",
                        "hide": False,
                        "intervalMs": 1000,
                        "maxDataPoints": 43200
                    }
                }
            ]
        }

        return alert_json
    
    def _generate_alertSQL(self, parameter: str, source: str) -> str:
        alertSQL = f"""
        SELECT
            $__time(time) AS time,
            {parameter} AS value
        FROM
            {source}
        WHERE
            $__timeFilter(time)
            AND temperature IS NOT NULL
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
                raise ValueError(f"Dashboard Folder '{folder_name}' not in GF_DASHBOARD_FOLDER_UIDS")
            folder_uid = folder_uid_map[folder_name]

        with open(file_path, 'r', encoding='utf-8') as file:
            alert_json = json.load(file)

        # upload alerts
        try:
            # Add function to check if the alert already exists
                # alerts cannot be overwritten
            client.upload_alert_json(alert_json)

        except requests.RequestException as e:
            print(f"[ERROR] Failed to upload alert '{file_name}': {e}")
            raise