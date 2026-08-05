from tool.helper import *

class MMTSLoggingBuilder:
    def __init__(self, datasource_uid, timezone='America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("MMTS Environment Logging")
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
                    "id": 1,
                    "title": "RTD-01 ~ RTD-08 Temperature",
                    "description": "",
                    "links": [],
                    "gridPos": {
                        "h": 9,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "linear",
                                "barAlignment": 0,
                                "barWidthFactor": 0.6,
                                "lineWidth": 2,
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "spanNulls": False,
                                "insertNulls": False,
                                "showPoints": "auto",
                                "showValues": False,
                                "pointSize": 5,
                                "stacking": {
                                    "mode": "none",
                                    "group": "A"
                                },
                                "axisPlacement": "auto",
                                "axisLabel": "Temperature (°C)",
                                "axisColorMode": "text",
                                "axisBorderShow": False,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "axisCenteredZero": False,
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "color": {
                                "mode": "palette-classic"
                            },
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "value": None,
                                        "color": "green"
                                    },
                                    {
                                        "value": 80,
                                        "color": "red"
                                    }
                                ]
                            }
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-01"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "red",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-02"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "orange",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-03"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "yellow",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-04"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "green",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-05"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "blue",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-06"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "purple",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-07"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "cyan",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "RTD-08"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "pink",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Chiller-01"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Chiller-ReadoutTemp"
                                    },
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "dark-blue",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Chiller-T"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Target Temp"
                                    },
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "dark-red",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "options": {
                        "tooltip": {
                            "mode": "multi",
                            "sort": "none",
                            "hideZeros": False
                        },
                        "legend": {
                            "showLegend": True,
                            "displayMode": "list",
                            "placement": "bottom",
                            "calcs": []
                        },
                        "annotations": {
                            "multiLane": False,
                            "clustering": -1
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "type": "timeseries",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": self.datasource_uid
                            },
                            "editorMode": "code",
                            "format": "time_series",
                            "rawQuery": True,
                            "rawSql": f"""SELECT
  log_timestamp AT TIME ZONE '{self.timezone}' AS "time",
  device_name::text AS metric,
  value
FROM mmts_sensors_logging
WHERE
  $__timeFilter(log_timestamp AT TIME ZONE '{self.timezone}')
  AND device_name IN ('RTD-01','RTD-02','RTD-03','RTD-04','RTD-05','RTD-06','RTD-07','RTD-08','Chiller-01','Chiller-T')
  AND mmts_sensors_logging.metric = 'temperature_C'
ORDER BY 1, 2;""",
                            "refId": "A",
                            "hidden": False,
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
                            },
                            "table": "measurement"
                        }
                    ]
                },
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "id": 2,
                    "title": "Dewpoint",
                    "description": "",
                    "links": [],
                    "gridPos": {
                        "h": 9,
                        "w": 24,
                        "x": 0,
                        "y": 9
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "linear",
                                "barAlignment": 0,
                                "barWidthFactor": 0.6,
                                "lineWidth": 2,
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "spanNulls": False,
                                "insertNulls": False,
                                "showPoints": "auto",
                                "showValues": False,
                                "pointSize": 1,
                                "stacking": {
                                    "mode": "none",
                                    "group": "A"
                                },
                                "axisPlacement": "auto",
                                "axisLabel": "Dewpoint (°C)",
                                "axisColorMode": "text",
                                "axisBorderShow": False,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "axisCenteredZero": False,
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                },
                                "thresholdsStyle": {
                                    "mode": "dashed"
                                }
                            },
                            "color": {
                                "mode": "palette-classic"
                            },
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "value": None,
                                        "color": "green"
                                    },
                                    {
                                        "value": -40,
                                        "color": "dark-red"
                                    }
                                ]
                            }
                        },
                        "overrides": []
                    },
                    "options": {
                        "tooltip": {
                            "mode": "single",
                            "sort": "none",
                            "hideZeros": False
                        },
                        "legend": {
                            "showLegend": True,
                            "displayMode": "list",
                            "placement": "bottom",
                            "calcs": []
                        },
                        "annotations": {
                            "multiLane": False,
                            "clustering": -1
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "type": "timeseries",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": self.datasource_uid
                            },
                            "editorMode": "code",
                            "format": "time_series",
                            "rawQuery": True,
                            "rawSql": f"""SELECT
  log_timestamp AT TIME ZONE '{self.timezone}' AS "time",
  device_name::text AS metric,
  value
FROM mmts_sensors_logging
WHERE
  $__timeFilter(log_timestamp AT TIME ZONE '{self.timezone}')
  AND device_name IN ('DMT-01','DMT-02')
  AND metric = 'dewpoint_C'
ORDER BY 1, 2;""",
                            "refId": "A",
                            "hidden": False,
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
                    ]
                },
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "id": 3,
                    "title": "Status",
                    "description": "",
                    "links": [],
                    "gridPos": {
                        "h": 9,
                        "w": 24,
                        "x": 0,
                        "y": 18
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "linear",
                                "barAlignment": 0,
                                "barWidthFactor": 0.6,
                                "lineWidth": 1,
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "spanNulls": False,
                                "insertNulls": False,
                                "showPoints": "auto",
                                "showValues": False,
                                "pointSize": 5,
                                "stacking": {
                                    "mode": "none",
                                    "group": "A"
                                },
                                "axisPlacement": "auto",
                                "axisLabel": "",
                                "axisColorMode": "text",
                                "axisBorderShow": False,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "axisCenteredZero": False,
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "color": {
                                "mode": "palette-classic"
                            },
                            "mappings": [
                                {
                                    "type": "value",
                                    "options": {
                                        "0": {
                                            "text": "Door Open",
                                            "index": 0
                                        },
                                        "1": {
                                            "text": "Standby",
                                            "index": 1
                                        },
                                        "2": {
                                            "text": "Countdown-Warming",
                                            "index": 2
                                        },
                                        "3": {
                                            "text": "Warming-up",
                                            "index": 3
                                        },
                                        "4": {
                                            "text": "Countdown-cooling",
                                            "index": 4
                                        },
                                        "5": {
                                            "text": "Cooling Down",
                                            "index": 5
                                        }
                                    }
                                }
                            ],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "value": None,
                                        "color": "green"
                                    }
                                ]
                            }
                        },
                        "overrides": []
                    },
                    "options": {
                        "tooltip": {
                            "mode": "single",
                            "sort": "none",
                            "hideZeros": False
                        },
                        "legend": {
                            "showLegend": True,
                            "displayMode": "list",
                            "placement": "bottom",
                            "calcs": []
                        },
                        "annotations": {
                            "multiLane": False,
                            "clustering": -1
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "type": "timeseries",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": self.datasource_uid
                            },
                            "editorMode": "code",
                            "format": "time_series",
                            "rawQuery": True,
                            "rawSql": f"""SELECT
  log_timestamp AT TIME ZONE '{self.timezone}' AS "time",
  value::int AS "System Status"
FROM mmts_sensors_logging
WHERE
  $__timeFilter(log_timestamp AT TIME ZONE '{self.timezone}')
  AND device_name IN ('System Status')
  AND mmts_sensors_logging.metric = 'system_C'
ORDER BY 1;""",
                            "refId": "A",
                            "hidden": False,
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
                    ]
                },
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "id": 4,
                    "title": "Cycle Count by Batch",
                    "description": "",
                    "links": [],
                    "gridPos": {
                        "h": 9,
                        "w": 24,
                        "x": 0,
                        "y": 27
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "show": "points",
                                "pointSize": {
                                    "fixed": 5,
                                    "min": 16,
                                    "max": 60
                                },
                                "pointShape": "circle",
                                "pointStrokeWidth": 1,
                                "fillOpacity": 50,
                                "axisPlacement": "auto",
                                "axisLabel": "",
                                "axisColorMode": "text",
                                "axisBorderShow": False,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "axisCenteredZero": False,
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                }
                            },
                            "color": {
                                "mode": "palette-classic"
                            },
                            "mappings": []
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "time"
                                },
                                "properties": [
                                    {
                                        "id": "custom.axisLabel",
                                        "value": "Batch Time"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "cycle_count"
                                },
                                "properties": [
                                    {
                                        "id": "custom.axisLabel",
                                        "value": "Cycle Count"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "module_size"
                                },
                                "properties": [
                                    {
                                        "id": "custom.hideFrom",
                                        "value": {
                                            "tooltip": True,
                                            "viz": False,
                                            "legend": True
                                        }
                                    },
                                    {
                                        "id": "min",
                                        "value": 1
                                    },
                                    {
                                        "id": "max",
                                        "value": 8
                                    }
                                ]
                            }
                        ]
                    },
                    "transformations": [],
                    "options": {
                        "mapping": "auto",
                        "series": [
                            {
                                "x": {
                                    "matcher": {
                                        "id": "byName",
                                        "options": "time"
                                    }
                                },
                                "y": {
                                    "matcher": {
                                        "id": "byName",
                                        "options": "cycle_count"
                                    }
                                },
                                "size": {
                                    "matcher": {
                                        "id": "byName",
                                        "options": "module_size"
                                    }
                                }
                            }
                        ],
                        "tooltip": {
                            "mode": "all",
                            "sort": "none",
                            "hideZeros": False
                        },
                        "legend": {
                            "showLegend": True,
                            "displayMode": "list",
                            "placement": "bottom",
                            "calcs": []
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "type": "xychart",
                    "targets": [
                        {
                            "datasource": {
                                "type": "grafana-postgresql-datasource",
                                "uid": self.datasource_uid
                            },
                            "editorMode": "code",
                            "format": "table",
                            "rawQuery": True,
                            "rawSql": f"""SELECT
  to_timestamp(t.batch_name, 'YYYYMMDD-HH24MISS') AS "time",
  cycle_count,
  cardinality(module_names) AS module_count,
  sqrt(cardinality(module_names)) AS module_size
FROM mmts_batch_logging t
WHERE
  $__timeFilter(t.log_timestamp)
  AND t.batch_name ~ '^[0-9]{{8}}-[0-9]{{6}}$'
UNION ALL
SELECT $__timeFrom() AS "time", NULL, NULL, NULL
UNION ALL
SELECT $__timeTo() AS "time", NULL, NULL, NULL
ORDER BY 1;""",
                            "refId": "A",
                            "hidden": False,
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
                    ]
                }
            ],
            "refresh": "5m",
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": []
            },
            "time": {
                "from": "now-7d",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "MMTS Environment Logging",
            "uid": self.dashboard_uid,
            "version": 1
        }

        return dashboard_json