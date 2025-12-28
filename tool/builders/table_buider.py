from tool.helper import *

"""
This file defines the class for building the table panel in Grafana dashboards.
"""

class TableBuilder:
    def __init__(self, datasource_uid: str):
        self.datasource_uid = datasource_uid

    def build_table_panel(self, panel_config: dict) -> dict:
        """Build a table panel based on the given panel configuration.
        """
        table_panel = {
            "type": "table",
            "title": panel_config.get("title", "Table Panel"),
            "datasource": {
                "type": "grafana-graphql-datasource",
                "uid": self.datasource_uid
            },
            "targets": panel_config.get("targets", []),
            "options": panel_config.get("options", {}),
            "fieldConfig": panel_config.get("fieldConfig", {}),
            "gridPos": panel_config.get("gridPos", {"h": 8, "w": 12, "x": 0, "y": 0}),
        }
        return table_panel
    