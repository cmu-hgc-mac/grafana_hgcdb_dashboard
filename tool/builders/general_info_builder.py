from tool.helper import *
class GeneralInfoBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("General Info")
        self.timezone = f"{timezone}"
        self.bp_material = "{bp_material}"
        self.resolution = "{resolution}"
        self.roc_version = "{roc_version}"
        self.sen_thickness = "{sen_thickness}"
        self.geometry = "{geometry}"
        self.grade = "{grade}"

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
                    "defaults": {
                    "color": {
                        "mode": "thresholds"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "lineWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
                    },
                    "decimals": 0,
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                        {
                            "color": "green"
                        }
                        ]
                    }
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "none",
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    },
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                },
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
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_info\n                ORDER BY module_name, module_no DESC\n                ),\n\n                temp_table_1 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_qc_summary\n                ORDER BY module_name, mod_qc_no DESC\n                )\n        SELECT \n            temp_table_0.bp_material::text || '/' || temp_table_0.resolution::text || '/' || temp_table_0.roc_version::text || '/' || temp_table_0.sen_thickness::text || '/' || temp_table_0.geometry::text AS label,\n            COUNT(*) AS count\n        FROM temp_table_0\n        LEFT JOIN temp_table_1 ON temp_table_0.module_name = temp_table_1.module_name\n        WHERE \n                ('All' = ANY(ARRAY[${bp_material}]) OR \n                (temp_table_0.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR \n                temp_table_0.bp_material::text = ANY(ARRAY[${bp_material}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${roc_version}]) OR \n                (temp_table_0.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR \n                temp_table_0.roc_version::text = ANY(ARRAY[${roc_version}]))\n          AND \n                ('All' = ANY(ARRAY[${sen_thickness}]) OR \n                (temp_table_0.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR \n                temp_table_0.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND $__timeFilter(temp_table_0.assembled AT TIME ZONE 'America/New_York')\n          AND \n                ('All' = ANY(ARRAY[${final_grade}]) OR \n                (temp_table_1.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${final_grade}])) OR \n                temp_table_1.final_grade::text = ANY(ARRAY[${final_grade}]))\n          AND bp_material IS NOT NULL AND resolution IS NOT NULL AND roc_version IS NOT NULL AND geometry IS NOT NULL\n        GROUP BY label\n        ORDER BY label;",
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
                "title": "Module Info",
                "type": "barchart"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        }
                    },
                    "decimals": 0,
                    "mappings": []
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 6,
                    "x": 12,
                    "y": 0
                },
                "id": 2,
                "options": {
                    "legend": {
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "pieType": "pie",
                    "reduceOptions": {
                    "calcs": [
                        "lastNotNull"
                    ],
                    "fields": "",
                    "values": False
                    },
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    }
                },
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
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_info\n                ORDER BY module_name, module_no DESC\n                ),\n\n                temp_table_1 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_qc_summary\n                ORDER BY module_name, mod_qc_no DESC\n                )\n        SELECT \n            COUNT(*) FILTER (WHERE final_grade = 'A') AS grade_a,\n            COUNT(*) FILTER (WHERE final_grade = 'B') AS grade_b,\n            COUNT(*) FILTER (WHERE final_grade = 'C') AS grade_c,\n            COUNT(*) FILTER (WHERE final_grade = 'F') AS grade_f\n        FROM temp_table_0\n        LEFT JOIN temp_table_1 ON temp_table_0.module_name = temp_table_1.module_name\n        WHERE \n                ('All' = ANY(ARRAY[${bp_material}]) OR \n                (temp_table_0.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR \n                temp_table_0.bp_material::text = ANY(ARRAY[${bp_material}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${roc_version}]) OR \n                (temp_table_0.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR \n                temp_table_0.roc_version::text = ANY(ARRAY[${roc_version}]))\n          AND \n                ('All' = ANY(ARRAY[${sen_thickness}]) OR \n                (temp_table_0.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR \n                temp_table_0.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND $__timeFilter(temp_table_0.assembled AT TIME ZONE 'America/New_York')\n          AND \n                ('All' = ANY(ARRAY[${final_grade}]) OR \n                (temp_table_1.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${final_grade}])) OR \n                temp_table_1.final_grade::text = ANY(ARRAY[${final_grade}]))\n          AND bp_material IS NOT NULL AND resolution IS NOT NULL AND roc_version IS NOT NULL AND geometry IS NOT NULL",
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
                "title": "Module Grades",
                "type": "piechart"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        }
                    },
                    "decimals": 0,
                    "mappings": []
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 6,
                    "x": 18,
                    "y": 0
                },
                "id": 5,
                "options": {
                    "legend": {
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "pieType": "pie",
                    "reduceOptions": {
                    "calcs": [
                        "lastNotNull"
                    ],
                    "fields": "",
                    "values": False
                    },
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    }
                },
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
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_info\n                ORDER BY module_name, module_no DESC\n                ),\n\n                temp_table_1 AS (\n                SELECT DISTINCT ON (module_name) *\n                FROM module_qc_summary\n                ORDER BY module_name, mod_qc_no DESC\n                )\n        SELECT \n            COUNT(*) FILTER (WHERE shipped_datetime IS NULL) AS not_shipped,\n            COUNT(*) FILTER (WHERE shipped_datetime IS NOT NULL) AS shipped\n        FROM temp_table_0\n        LEFT JOIN temp_table_1 ON temp_table_0.module_name = temp_table_1.module_name\n        WHERE \n                ('All' = ANY(ARRAY[${bp_material}]) OR \n                (temp_table_0.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR \n                temp_table_0.bp_material::text = ANY(ARRAY[${bp_material}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${roc_version}]) OR \n                (temp_table_0.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR \n                temp_table_0.roc_version::text = ANY(ARRAY[${roc_version}]))\n          AND \n                ('All' = ANY(ARRAY[${sen_thickness}]) OR \n                (temp_table_0.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR \n                temp_table_0.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND $__timeFilter(temp_table_0.assembled AT TIME ZONE 'America/New_York')\n          AND \n                ('All' = ANY(ARRAY[${final_grade}]) OR \n                (temp_table_1.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${final_grade}])) OR \n                temp_table_1.final_grade::text = ANY(ARRAY[${final_grade}]))\n          AND bp_material IS NOT NULL AND resolution IS NOT NULL AND roc_version IS NOT NULL AND geometry IS NOT NULL",
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
                "title": "Module Shipping",
                "type": "piechart"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "barAlignment": 0,
                        "barWidthFactor": 0.6,
                        "drawStyle": "line",
                        "fillOpacity": 0,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "insertNulls": False,
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "pointSize": 5,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "showPoints": "auto",
                        "spanNulls": False,
                        "stacking": {
                        "group": "A",
                        "mode": "none"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
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
                    "h": 8,
                    "w": 12,
                    "x": 0,
                    "y": 8
                },
                "id": 3,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    }
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH\ndaily_module AS (\n    SELECT\n        DATE(module_info.assembled AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS count\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         module_info.bp_material::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           module_info.resolution::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           module_info.roc_version::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           module_info.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           module_info.geometry::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(module_info.assembled)\n      AND module_info.assembled IS NOT NULL\n    GROUP BY 1\n),\n\ndaily_proto AS (\n    SELECT\n        DATE(proto_assembly.ass_run_date AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS count\n    FROM proto_assembly\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END)::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END)::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(proto_assembly.ass_run_date)\n      AND proto_assembly.ass_run_date IS NOT NULL\n    GROUP BY 1\n)\n\nSELECT\n    (COALESCE(m.local_date, p.local_date)::timestamp + interval '12 hour') AS \"time\",\n    p.count AS proto_assembly,\n    m.count AS module_assembly\nFROM daily_module m\nFULL OUTER JOIN daily_proto p\n    ON m.local_date = p.local_date\nORDER BY \"time\";",
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
                "title": "Module Assembly (Daily)",
                "type": "timeseries"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "barAlignment": 0,
                        "barWidthFactor": 0.6,
                        "drawStyle": "line",
                        "fillOpacity": 0,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "insertNulls": False,
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "pointSize": 5,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "showPoints": "auto",
                        "spanNulls": False,
                        "stacking": {
                        "group": "A",
                        "mode": "none"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
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
                    "h": 8,
                    "w": 12,
                    "x": 12,
                    "y": 8
                },
                "id": 4,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    }
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH\ndaily_module AS (\n    SELECT\n        DATE(module_info.assembled AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS cnt\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         module_info.bp_material::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           module_info.resolution::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           module_info.roc_version::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           module_info.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           module_info.geometry::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(module_info.assembled)\n      AND module_info.assembled IS NOT NULL\n    GROUP BY 1\n),\n\ncum_module AS (\n    SELECT\n        local_date,\n        SUM(cnt) OVER (\n            ORDER BY local_date\n            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n        ) AS module_total\n    FROM daily_module\n),\n\ndaily_proto AS (\n    SELECT\n        DATE(proto_assembly.ass_run_date AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS cnt\n    FROM proto_assembly\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END)::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END)::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(proto_assembly.ass_run_date)\n      AND proto_assembly.ass_run_date IS NOT NULL\n    GROUP BY 1\n),\n\ncum_proto AS (\n    SELECT\n        local_date,\n        SUM(cnt) OVER (\n            ORDER BY local_date\n            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n        ) AS proto_total\n    FROM daily_proto\n)\n\nSELECT\n    (COALESCE(m.local_date, p.local_date)::timestamp + interval '12 hour') AS \"time\",\n    p.proto_total AS proto_assembly,\n    m.module_total AS module_assembly\nFROM cum_module m\nFULL OUTER JOIN cum_proto p\n    ON m.local_date = p.local_date\nORDER BY \"time\";",
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
                "title": "Module Assembly (Cumulative)",
                "type": "timeseries"
                },
                {
                "fieldConfig": {
                    "defaults": {},
                    "overrides": []
                },
                "gridPos": {
                    "h": 1,
                    "w": 24,
                    "x": 0,
                    "y": 24
                },
                "id": 6,
                "options": {
                    "code": {
                    "language": "plaintext",
                    "showLineNumbers": False,
                    "showMiniMap": False
                    },
                    "content": "",
                    "mode": "markdown"
                },
                "pluginVersion": "12.0.0",
                "title": "",
                "type": "text"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "lineWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
                    },
                    "decimals": 0,
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
                    "h": 9,
                    "w": 8,
                    "x": 0,
                    "y": 25
                },
                "id": 7,
                "options": {
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "none",
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    },
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (bp_name) *\n                FROM baseplate\n                ORDER BY bp_name, bp_no DESC\n                ),\n\n                temp_table_1 AS (\n                SELECT DISTINCT ON (bp_name) *\n                FROM bp_inspect\n                ORDER BY bp_name, bp_row_no DESC\n                )\n        SELECT \n            temp_table_0.bp_material::text || '/' || temp_table_0.resolution::text || '/' || temp_table_0.geometry::text AS label,\n            COUNT(*) AS count\n        FROM temp_table_0\n        LEFT JOIN temp_table_1 ON temp_table_0.bp_name = temp_table_1.bp_name\n        WHERE \n                ('All' = ANY(ARRAY[${bp_material}]) OR\n                  (temp_table_0.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n                  (\n                  CASE temp_table_0.bp_material\n                        WHEN 'Ti' THEN 'Titanium'\n                        WHEN 'CF' THEN 'Carbon Fiber' \n                        ELSE temp_table_0.bp_material::text\n                  END\n                  ) = ANY(ARRAY[${bp_material}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND proto_no IS NULL\n        GROUP BY label\n        ORDER BY label;",
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
                "title": "Free Baseplates",
                "type": "barchart"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "lineWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
                    },
                    "decimals": 0,
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
                    "h": 9,
                    "w": 8,
                    "x": 8,
                    "y": 25
                },
                "id": 9,
                "options": {
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "none",
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    },
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (hxb_name) *\n                FROM hexaboard\n                ORDER BY hxb_name, hxb_no DESC\n                ),\n\n                temp_table_1 AS (\n                SELECT DISTINCT ON (hxb_name) *\n                FROM hxb_pedestal_test\n                ORDER BY hxb_name, hxb_pedtest_no DESC\n                )\n        SELECT \n            temp_table_0.roc_version::text || '/' || temp_table_0.resolution::text || '/' || temp_table_0.geometry::text AS label,\n            COUNT(*) AS count\n        FROM temp_table_0\n        LEFT JOIN temp_table_1 ON temp_table_0.hxb_name = temp_table_1.hxb_name\n        WHERE \n                ('All' = ANY(ARRAY[${roc_version}]) OR \n                (temp_table_0.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR \n                temp_table_0.roc_version::text = ANY(ARRAY[${roc_version}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND module_no is NULL\n        GROUP BY label\n        ORDER BY label;",
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
                "title": "Free Hexaboards",
                "type": "barchart"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "lineWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
                    },
                    "decimals": 0,
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
                    "h": 9,
                    "w": 8,
                    "x": 16,
                    "y": 25
                },
                "id": 8,
                "options": {
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "none",
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    },
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH\n                temp_table_0 AS (\n                SELECT DISTINCT ON (sen_name) *\n                FROM sensor\n                ORDER BY sen_name, sen_no DESC\n                )\n        SELECT \n            temp_table_0.thickness::text || '/' || temp_table_0.resolution::text || '/' || temp_table_0.geometry::text AS label,\n            COUNT(*) AS count\n        FROM temp_table_0\n        \n        WHERE \n                ('All' = ANY(ARRAY[${sen_thickness}]) OR \n                (temp_table_0.thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR \n                temp_table_0.thickness::text = ANY(ARRAY[${sen_thickness}]))\n          AND \n                ('All' = ANY(ARRAY[${resolution}]) OR \n                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR \n                temp_table_0.resolution::text = ANY(ARRAY[${resolution}]))\n          AND \n                ('All' = ANY(ARRAY[${geometry}]) OR \n                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR \n                temp_table_0.geometry::text = ANY(ARRAY[${geometry}]))\n          AND proto_no IS NULL\n        GROUP BY label\n        ORDER BY label;",
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
                "title": "Free Sensors",
                "type": "barchart"
                },
                {
                "fieldConfig": {
                    "defaults": {},
                    "overrides": []
                },
                "gridPos": {
                    "h": 1,
                    "w": 24,
                    "x": 0,
                    "y": 34
                },
                "id": 10,
                "options": {
                    "code": {
                    "language": "plaintext",
                    "showLineNumbers": False,
                    "showMiniMap": False
                    },
                    "content": "",
                    "mode": "markdown"
                },
                "pluginVersion": "12.0.0",
                "title": "",
                "type": "text"
                },
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "lineWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "thresholdsStyle": {
                        "mode": "off"
                        }
                    },
                    "decimals": 0,
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
                    "h": 9,
                    "w": 24,
                    "x": 0,
                    "y": 35
                },
                "id": 11,
                "options": {
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "none",
                    "tooltip": {
                    "hideZeros": False,
                    "mode": "single",
                    "sort": "none"
                    },
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                },
                "pluginVersion": "12.0.0",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH filtered_module_info AS (\n    SELECT\n        module_name\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n            (bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n            bp_material::text = ANY(ARRAY[${bp_material}]))\n        AND\n            ('All' = ANY(ARRAY[${resolution}]) OR\n            (resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n            resolution::text = ANY(ARRAY[${resolution}]))\n        AND\n            ('All' = ANY(ARRAY[${roc_version}]) OR\n            (roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n            roc_version::text = ANY(ARRAY[${roc_version}]))\n        AND\n            ('All' = ANY(ARRAY[${sen_thickness}]) OR\n            (sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n            sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n        AND\n            ('All' = ANY(ARRAY[${geometry}]) OR\n            (geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n            geometry::text = ANY(ARRAY[${geometry}]))\n        AND $__timeFilter(assembled)\n),\ntemp_table_0 AS (\n    SELECT DISTINCT ON (q.module_name)\n        q.module_name,\n        q.final_grade,\n        q.count_bad_cells\n    FROM module_qc_summary q\n    LEFT JOIN filtered_module_info f\n        ON q.module_name = f.module_name\n    WHERE f.module_name IS NOT NULL\n    ORDER BY q.module_name, q.mod_qc_no DESC\n)\nSELECT\n    COALESCE(temp_table_0.count_bad_cells::text, 'F') AS label,\n    COUNT(*) AS count\nFROM temp_table_0\nWHERE\n    ('All' = ANY(ARRAY[${final_grade}]) OR\n     (temp_table_0.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${final_grade}])) OR\n     temp_table_0.final_grade::text = ANY(ARRAY[${final_grade}]))\n    AND final_grade IS NOT NULL\nGROUP BY temp_table_0.count_bad_cells\nORDER BY temp_table_0.count_bad_cells::int;",
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
                "title": "Count for bad cells",
                "type": "barchart"
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
                        "align": "center",
                        "cellOptions": {
                        "type": "auto"
                        },
                        "inspect": False,
                        "width": 100
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "A+B (Installable)"
                        },
                        "properties": [
                        {
                            "id": "custom.width",
                            "value": 160
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "Total Graded"
                        },
                        "properties": [
                        {
                            "id": "custom.width",
                            "value": 140
                        }
                        ]
                    }
                    ]
                },
                "gridPos": {
                    "h": 8,
                    "w": 24,
                    "x": 0,
                    "y": 16
                },
                "options": {
                    "cellHeight": "sm",
                    "footer": {
                    "countRows": False,
                    "fields": "",
                    "reducer": ["sum"],
                    "show": False
                    },
                    "showHeader": True
                },
                "pluginVersion": "12.0.1",
                "targets": [
                    {
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "WITH filtered_module_info AS (\n    SELECT\n        module_name\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n            (bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n            bp_material::text = ANY(ARRAY[${bp_material}]))\n        AND\n            ('All' = ANY(ARRAY[${resolution}]) OR\n            (resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n            resolution::text = ANY(ARRAY[${resolution}]))\n        AND\n            ('All' = ANY(ARRAY[${roc_version}]) OR\n            (roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n            roc_version::text = ANY(ARRAY[${roc_version}]))\n        AND\n            ('All' = ANY(ARRAY[${sen_thickness}]) OR\n            (sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n            sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n        AND\n            ('All' = ANY(ARRAY[${geometry}]) OR\n            (geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n            geometry::text = ANY(ARRAY[${geometry}]))\n        AND $__timeFilter(assembled)\n        AND assembled IS NOT NULL\n),\nlatest_qc AS (\n    SELECT DISTINCT ON (q.module_name)\n        q.module_name,\n        q.final_grade\n    FROM module_qc_summary q\n    JOIN filtered_module_info f ON q.module_name = f.module_name\n    ORDER BY q.module_name, q.mod_qc_no DESC\n),\nseries_data AS (\n    SELECT\n        SUBSTRING(f.module_name, 4, 6) AS \"Series\",\n        COUNT(*) AS \"Total Graded\",\n        COUNT(CASE WHEN lq.final_grade = 'A' THEN 1 END) AS \"A\",\n        COUNT(CASE WHEN lq.final_grade = 'B' THEN 1 END) AS \"B\",\n        COUNT(CASE WHEN lq.final_grade = 'C' THEN 1 END) AS \"C\",\n        COUNT(CASE WHEN lq.final_grade = 'F' THEN 1 END) AS \"F\",\n        COUNT(CASE WHEN lq.final_grade IN ('A', 'B') THEN 1 END) AS \"A+B (Installable)\"\n    FROM filtered_module_info f\n    JOIN latest_qc lq ON f.module_name = lq.module_name\n    WHERE\n        ('All' = ANY(ARRAY[${final_grade}]) OR\n         (lq.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${final_grade}])) OR\n         lq.final_grade::text = ANY(ARRAY[${final_grade}]))\n    GROUP BY SUBSTRING(f.module_name, 4, 6)\n)\nSELECT \"Series\", \"Total Graded\", \"A\", \"B\", \"C\", \"F\", \"A+B (Installable)\", \"% Installable\" FROM (\n    SELECT\n        \"Series\",\n        \"Total Graded\",\n        \"A\",\n        \"B\",\n        \"C\",\n        \"F\",\n        \"A+B (Installable)\",\n        CASE WHEN \"Total Graded\" = 0 THEN '0.0%' ELSE ROUND(\"A+B (Installable)\" * 100.0 / \"Total Graded\", 1)::text || '%' END AS \"% Installable\",\n        0 AS sort_order\n    FROM series_data\n    UNION ALL\n    SELECT\n        'All',\n        SUM(\"Total Graded\"),\n        SUM(\"A\"),\n        SUM(\"B\"),\n        SUM(\"C\"),\n        SUM(\"F\"),\n        SUM(\"A+B (Installable)\"),\n        CASE WHEN SUM(\"Total Graded\") = 0 THEN '0.0%' ELSE ROUND(SUM(\"A+B (Installable)\") * 100.0 / SUM(\"Total Graded\"), 1)::text || '%' END,\n        1\n    FROM series_data\n) AS combined\nORDER BY sort_order, \"Series\";",
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
                "title": "Grade Summary by Series",
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
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "includeAll": True,
                    "multi": True,
                    "name": "bp_material",
                    "options": [],
                    "query": "\n            SELECT DISTINCT bp_material::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY bp_material\n            ",
                    "refresh": 1,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "includeAll": True,
                    "multi": True,
                    "name": "resolution",
                    "options": [],
                    "query": "\n            SELECT DISTINCT resolution::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY resolution\n            ",
                    "refresh": 1,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "includeAll": True,
                    "multi": True,
                    "name": "roc_version",
                    "options": [],
                    "query": "\n            SELECT DISTINCT roc_version::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY roc_version\n            ",
                    "refresh": 1,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "includeAll": True,
                    "multi": True,
                    "name": "sen_thickness",
                    "options": [],
                    "query": "\n            SELECT DISTINCT sen_thickness::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY sen_thickness\n            ",
                    "refresh": 1,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "includeAll": True,
                    "multi": True,
                    "name": "geometry",
                    "options": [],
                    "query": "\n            SELECT DISTINCT geometry::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY geometry\n            ",
                    "refresh": 1,
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": [
                        "$__all"
                    ]
                    },
                    "datasource": {
                    "type": "postgres",
                    "uid": self.datasource_uid
                    },
                    "definition": "\n            SELECT DISTINCT final_grade::text FROM module_qc_summary \n            UNION\n            SELECT 'NULL'\n            ORDER BY final_grade\n            ",
                    "includeAll": True,
                    "multi": True,
                    "name": "final_grade",
                    "options": [],
                    "query": "\n            SELECT DISTINCT final_grade::text FROM module_qc_summary \n            UNION\n            SELECT 'NULL'\n            ORDER BY final_grade\n            ",
                    "refresh": 1,
                    "type": "query"
                }
                ]
            },
            "time": {
                "from": "now-30d",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "General Info",
            "uid": "general-info",
            "version": 16
            }

        return dashboard_json
