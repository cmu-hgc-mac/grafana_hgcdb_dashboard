from tool.helper import *

class MMTSBatchLoggingBuilder:
    def __init__(self, datasource_uid, timezone='America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("MMTS Batch Logging")
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
                    "title": "Cycle Count by Batch",
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
                            "rawSql": f"""WITH filtered AS (
  SELECT
    to_timestamp(t.batch_name, 'YYYYMMDD-HH24MISS') AS "time",
    cycle_count,
    cardinality(module_names) AS module_count,
    sqrt(cardinality(module_names)) AS module_size
  FROM mmts_batch_logging t
  WHERE
    $__timeFilter(t.log_timestamp)
    AND ('${{module_name}}' = '' OR EXISTS (
      SELECT 1
      FROM unnest(t.module_names) AS elem
      WHERE elem ILIKE '%' || '${{module_name}}' || '%'
    ))
    AND ('${{batch_name}}' = '' OR t.batch_name ILIKE '%' || '${{batch_name}}' || '%')
),
single_point AS (
  SELECT (SELECT COUNT(*) FROM filtered) = 1 AS is_single
)
SELECT "time", cycle_count, module_count, module_size
FROM filtered
UNION ALL
SELECT $__timeFrom() AS "time", NULL, NULL, NULL
UNION ALL
SELECT $__timeTo() AS "time", NULL, NULL, NULL
UNION ALL
SELECT NULL, NULL, NULL, 0
FROM single_point WHERE is_single
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
                    "id": 2,
                    "title": "Batches",
                    "description": "",
                    "links": [],
                    "gridPos": {
                        "h": 15,
                        "w": 24,
                        "x": 0,
                        "y": 9
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "align": "auto",
                                "cellOptions": {
                                    "type": "auto"
                                },
                                "inspect": False
                            },
                            "color": {
                                "mode": "thresholds"
                            },
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
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "cycle_count"
                                },
                                "properties": [
                                    {
                                        "id": "custom.width",
                                        "value": 70
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "modcount"
                                },
                                "properties": [
                                    {
                                        "id": "custom.width",
                                        "value": 70
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "description"
                                },
                                "properties": [
                                    {
                                        "id": "custom.width",
                                        "value": 300
                                    },
                                    {
                                        "id": "custom.cellOptions",
                                        "value": {
                                            "type": "auto",
                                            "wrapText": True
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "module_names"
                                },
                                "properties": [
                                    {
                                        "id": "custom.width",
                                        "value": 300
                                    },
                                    {
                                        "id": "custom.cellOptions",
                                        "value": {
                                            "type": "auto",
                                            "wrapText": True
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "station_names"
                                },
                                "properties": [
                                    {
                                        "id": "custom.width",
                                        "value": 300
                                    },
                                    {
                                        "id": "custom.cellOptions",
                                        "value": {
                                            "type": "auto",
                                            "wrapText": True
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "options": {
                        "showHeader": True,
                        "cellHeight": "sm",
                        "footer": {
                            "show": False,
                            "reducer": ["sum"],
                            "countRows": False,
                            "fields": ""
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "type": "table",
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
  batch_name,
  cycle_count,
  cardinality(module_names) AS modcount,
  description,
  status_safety_alarm,
  status_dry_air_pressure,
  status_alcohol_content,
  status_chiller_alarm,
  array_to_string(module_names, ', ') AS module_names,
  array_to_string(station_names, ', ') AS station_names,
  other_electrical_startup_tests,
  log_timestamp AT TIME ZONE '{self.timezone}' AS log_timestamp,
  timestamp_utc
FROM mmts_batch_logging t
WHERE
  ('${{module_name}}' = '' OR EXISTS (
    SELECT 1
    FROM unnest(t.module_names) AS elem
    WHERE elem ILIKE '%' || '${{module_name}}' || '%'
  ))
  AND ('${{batch_name}}' = '' OR t.batch_name ILIKE '%' || '${{batch_name}}' || '%')
ORDER BY batch_name DESC;""",
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
            "refresh": "",
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                    {
                        "current": {
                            "text": "",
                            "value": ""
                        },
                        "label": "module_name",
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
                        "current": {
                            "text": "",
                            "value": ""
                        },
                        "label": "batch_name",
                        "name": "batch_name",
                        "options": [
                            {
                                "selected": True,
                                "text": "",
                                "value": ""
                            }
                        ],
                        "query": "",
                        "type": "textbox"
                    }
                ]
            },
            "time": {
                "from": "now-90d",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "MMTS Batch Logging",
            "uid": self.dashboard_uid,
            "version": 1
        }

        return dashboard_json
