from tool.helper import *

class MMTSBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("MMTS Info")
        self.timezone = f"{timezone}"

    def generate_dashboard_json(self):
        dashboard_json = {
            "annotations": {
                "list": [
                {
                    "builtIn": 1,
                    "datasource": {
                    "type": "grafana",
                    "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "links": [],
            "panels": [
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {},
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 24,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {},
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    # TODO: replace with real MMTS table/columns once schema is available
                    "rawSql": "SELECT 1 AS placeholder;",
                    "refId": "A",
                    "sql": {
                        "columns": [
                        {
                            "parameters": [],
                            "type": "function"
                        }
                        ],
                        "groupBy": [
                        {
                            "property": {
                            "type": "string"
                            },
                            "type": "groupBy"
                        }
                        ],
                        "limit": 50
                    }
                    }
                ],
                "title": "MMTS Placeholder",
                "type": "table"
                }
            ],
            "preload": False,
            "refresh": "",
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": []
            },
            "time": {
                "from": "now-6M",
                "to": "now"
            },
            "timepicker": {},
            "timezone": self.timezone,
            "title": "MMTS Info",
            "uid": self.dashboard_uid,
            "version": 1
        }

        return dashboard_json
