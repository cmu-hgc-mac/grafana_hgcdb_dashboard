import os
import json

from tool.helper import *

"""
This file defines classes for building other features for Grafana, including:
    - Filters
    - Alerts
"""

class FilterBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
    
    def generate_filter(self, filter_name: str, filter_sql: str) -> dict:
        """Generate a template json based on the given .
        """
        # generate the filter json:
        filter_json = {
                "current": {
                "text": [
                "All"
                ],
                "value": [
                "$__all"
                ]
                },
                "datasource": {
                "type": "postgres",
                "uid": f"{self.datasource_uid}"
                },
                "includeAll": True,
                "multi": True,
                "name": filter_name,
                "options": [],
                "query": filter_sql,
                "refresh": 1,   # refresh everytime when dashboard is loaded
                "type": "query"
            }

        return filter_json
    
    def generate_filterSQL(self, filter_name: str, filters_table: str) -> str:
        """Generate a template SQL command based on the given filter name.
        """
        # check filter type:
        if filter_name == "status":
            filter_sql = f"""
            SELECT DISTINCT 
            CASE WHEN shipped_datetime IS NULL THEN 'not shipped' ELSE 'shipped' END AS status 
            FROM {filters_table}
            ORDER BY status
            """
        else:
            filter_sql = f"""
            SELECT DISTINCT {filter_name} FROM {filters_table} ORDER BY {filter_name}
            """

        return filter_sql
    
    def build_template_list(self, filters: dict, exist_filter: set) -> list:
        """Build all filters based on the given filter_dict.
        """
        filters_table_list = list(filters.keys())
        template_list = []

        for filters_table in filters_table_list:
            for elem in filters[filters_table]:
                if elem in exist_filter:
                    continue    # filter exists
                elif elem == "assembled" or elem.endswith("time") or elem.endswith("date"):
                    continue    # filter not used in dashboard
            
                exist_filter.add(elem)

                # generate the filter's json
                filter_sql = self.generate_filterSQL(elem, filters_table)
                filter_json = self.generate_filter(elem, filter_sql)
                template_list.append(filter_json)
        
        return template_list


class AlertBuilder:
    def __init__(self, datasource_uid: str):
        self.datasource_uid = datasource_uid

    def generate_alerts(self, alert: dict):
        """ Build all alerts based on the given alert_dict.
        """ 
        # generate alert json
        alert_sql = self._generate_alertSQL(alert['parameter'], alert['table'])
        alert_json = self.generate_alert_rule(alert_sql, alert, alert['dashboard'])
        
        return alert_json

    def generate_alert_rule(self, alertSQL: str, alertInfo: dict, dashboard_title: str) -> dict:
        """Generate a json of the alert rule based on the given info
        """
        # get dashboard uid
        dashboard_uid = create_uid(dashboard_title)

        # generate alert json
        alert_json =  {
            "title": f"ALERT: {alertInfo['title']}",
            "ruleGroup": alertInfo['title'],
            "datasource_uid": self.datasource_uid,
            "noDataState": "Alerting",
            "execErrState": "Alerting",
            "for": alertInfo['duration'],
            "orgId": 1,
            "condition": "B",
            "annotations": {
                "summary": alertInfo['summary']
            },
            "labels": {
                "dashboard_uid": dashboard_uid,
                "auto": alertInfo['labels']
            },
            "data": [
                {
                    "refId": "A",
                    "queryType": "SQL",
                    "relativeTimeRange": { "from": 600, "to": 0 }, # read the data in the time interval from 10 min before
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
                    "datasourceUid": "-100",
                    "model": {
                        "conditions": [
                            {
                                "evaluator": { "type": alertInfo["logicType"], "params": [alertInfo['threshold']] },
                                "operator": { "type": "and" },
                                "query": { "params": ["A"] },
                                "reducer": { "type": "last", "params": [] },
                                "type": "query"
                            }
                        ],
                        "refId": "B",
                        "type": "classic_conditions",
                        "datasource": { "type": "__expr__", "uid": "-100" },
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
        
        folder_uid_map = gf_conn.get("GF_ALERT_FOLDER_UIDS", {})
        if folder_name not in folder_uid_map:
            raise ValueError(f"Alert Folder '{folder_name}' not found in Grafana.")
        folder_uid = folder_uid_map[folder_name]

        with open(file_path, 'r', encoding='utf-8') as file:
            alert_json = json.load(file)

        # upload alerts
        try:
            client.upload_alert_json(alert_json, folder_uid)

        except requests.RequestException as e:
            print(f"[ERROR] Failed to upload alert '{file_name}': {e}")
            raise
