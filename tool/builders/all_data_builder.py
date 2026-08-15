import os

from tool.helper import *

"""
This file defines the class for building the "All Data" dashboard in Grafana.
    - A single table panel with a dropdown to pick any table (from tool/postgres_tables)
      and view/search/sort its raw contents.
"""

class AllDataBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("All Data")

    def get_table_names(self) -> list:
        """List all available table names from the postgres_tables schema folder.
        """
        table_names = sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(DB_INFO_PATH)
            if f.endswith(".csv")
        )
        return table_names

    def generate_dashboard_json(self) -> dict:
        """Generate the dashboard JSON for the "All Data" table viewer.
        """
        table_names = self.get_table_names()
        default_table = table_names[0] if table_names else ""

        table_options = [
            {"selected": table_name == default_table, "text": table_name, "value": table_name}
            for table_name in table_names
        ]

        default_query = f"SELECT * FROM {default_table} LIMIT 100" if default_table else ""

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
            "id": None,
            "links": [],
            "panels": [
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": f"{self.datasource_uid}"
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "thresholds"
                            },
                            "custom": {
                                "align": "auto",
                                "cellOptions": {
                                    "type": "auto"
                                },
                                "filterable": True,
                                "inspect": False
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green"
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            }
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 24,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "id": 1,
                    "options": {
                        "cellHeight": "sm",
                        "footer": {
                            "countRows": False,
                            "fields": "",
                            "reducer": [
                                "sum"
                            ],
                            "show": False
                        },
                        "showHeader": True,
                        "sortBy": []
                    },
                    "pluginVersion": "12.0.1",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": f"{self.datasource_uid}"
                            },
                            "editorMode": "code",
                            "format": "table",
                            "rawQuery": True,
                            "rawSql": "SELECT * FROM ${table_name:raw}",
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
                    "title": "All Data",
                    "type": "table"
                },
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": f"{self.datasource_uid}"
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "thresholds"
                            },
                            "custom": {
                                "align": "auto",
                                "cellOptions": {
                                    "type": "auto"
                                },
                                "filterable": True,
                                "inspect": False
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green"
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            }
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 24,
                        "w": 24,
                        "x": 0,
                        "y": 24
                    },
                    "id": 2,
                    "options": {
                        "cellHeight": "sm",
                        "footer": {
                            "countRows": False,
                            "fields": "",
                            "reducer": [
                                "sum"
                            ],
                            "show": False
                        },
                        "showHeader": True,
                        "sortBy": []
                    },
                    "pluginVersion": "12.0.1",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": f"{self.datasource_uid}"
                            },
                            "editorMode": "code",
                            "format": "table",
                            "rawQuery": True,
                            "rawSql": "${custom_query:raw}",
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
                    "title": "Custom Query",
                    "type": "table"
                }
            ],
            "preload": False,
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                    {
                        "current": {
                            "text": default_table,
                            "value": default_table
                        },
                        "hide": 0,
                        "includeAll": False,
                        "label": "Table",
                        "multi": False,
                        "name": "table_name",
                        "options": table_options,
                        "query": ",".join(table_names),
                        "queryValue": "",
                        "skipUrlSync": False,
                        "type": "custom"
                    },
                    {
                        "current": {
                            "text": default_query,
                            "value": default_query
                        },
                        "hide": 0,
                        "label": "Custom SQL Query",
                        "name": "custom_query",
                        "options": [
                            {
                                "selected": True,
                                "text": default_query,
                                "value": default_query
                            }
                        ],
                        "query": default_query,
                        "skipUrlSync": False,
                        "type": "textbox"
                    }
                ]
            },
            "time": {
                "from": "now-30d",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "All Data",
            "uid": f"{self.dashboard_uid}",
            "version": 1
        }

        return dashboard_json
