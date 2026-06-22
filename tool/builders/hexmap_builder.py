from tool.helper import *
class HexmapPlotsBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("Hexmap Plots")

        self.mean_hex_map_base64 = "${mean_hex_map}"
        self.std_hex_map_base64 = "${std_hex_map}"

        self.mean_hexmap_md = f'<img src=\"data:image/png;base64,{self.mean_hex_map_base64}" style="width: auto; height: auto;"/>'
        self.std_hexmap_md = f'<img src=\"data:image/png;base64,{self.std_hex_map_base64}" style="width: auto; height: auto;"/>'

        self.mean_hexmap_sql = """
        SELECT encode(adc_mean_hexmap, 'base64') AS hex_img
        FROM module_pedestal_plots
        WHERE module_name = '${module_name}'
            AND ('All' = ANY(ARRAY[${status_desc}]) OR 
            (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR 
            module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))
        ORDER BY mod_plottest_no DESC;
        """

        self.std_hexmap_sql = """
        SELECT encode(adc_std_hexmap, 'base64') AS hex_img
        FROM module_pedestal_plots
        WHERE module_name = '${module_name}'
            AND ('All' = ANY(ARRAY[${status_desc}]) OR 
            (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR 
            module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))
        ORDER BY mod_plottest_no DESC;
        """

    ######################################
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
                "fieldConfig": {
                    "defaults": {},
                    "overrides": []
                },
                "gridPos": {
                    "h": 18,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "code": {
                    "language": "plaintext",
                    "showLineNumbers": False,
                    "showMiniMap": False
                    },
                    "content": self.mean_hexmap_md,
                    "mode": "markdown"
                },
                "pluginVersion": "12.0.0",
                "repeat": "mean_hex_map",
                "repeatDirection": "v",
                "title": "Pedestal Hexmap",
                "type": "text"
                },
                {
                "fieldConfig": {
                    "defaults": {},
                    "overrides": []
                },
                "gridPos": {
                    "h": 18,
                    "w": 12,
                    "x": 12,
                    "y": 0
                },
                "id": 2,
                "options": {
                    "code": {
                    "language": "plaintext",
                    "showLineNumbers": False,
                    "showMiniMap": False
                    },
                    "content": self.std_hexmap_md,
                    "mode": "markdown"
                },
                "pluginVersion": "12.0.0",
                "repeat": "std_hex_map",
                "repeatDirection": "v",
                "title": "Noise Hexmap",
                "type": "text"
                }
            ],
            "preload": False,
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                {
                    "current": {
                    "text": "",
                    "value": ""
                    },
                    "label": "Serial Name",
                    "name": "module_name",
                    "options": [
                    {
                        "selected": True,
                        "text": "",
                        "value": ""
                    }
                    ],
                    "query": "",
                    "type": "textbox"
                },
                {
                    "allowCustomValue": True,
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                        "type": "postgres",
                        "uid": f"{self.datasource_uid}"
                    },
                    "description": "",
                    "includeAll": True,
                    "label": "Status",
                    "multi": True,
                    "name": "status_desc",
                    "options": [],
                    "query": "SELECT status_desc\nFROM module_pedestal_plots\nGROUP BY status_desc\nORDER BY COUNT(*) DESC;",
                    "refresh": 1,
                    "regex": "",
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": "$__all"
                    },
                    "hide": 2,
                    "includeAll": True,
                    "multi": True,
                    "name": "mean_hex_map",
                    "options": [],
                    "query": self.mean_hexmap_sql,
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": True,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": "$__all"
                    },
                    "hide": 2,
                    "includeAll": True,
                    "multi": True,
                    "name": "std_hex_map",
                    "options": [],
                    "query": self.std_hexmap_sql,
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": True,
                    "type": "query"
                }
                ]
            },
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "Hexmap Plots",
            "uid": f"{self.dashboard_uid}",
            "version": 1
        }

        return dashboard_json

