from tool.helper import *
class OffsetPlotsBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("Offset Plots")
        self.timezone = f"{timezone}"
        self.bp_material = "{bp_material}"
        self.resolution = "{resolution}"
        self.roc_version = "{roc_version}"
        self.sen_thickness = "{sen_thickness}"
        self.geometry = "{geometry}"
        self.grade = "{grade}"
        self.put_position = "{put_position}"
        self.ass_tray_id = "{ass_tray_id}"

        self.module_filter_sql = f"""
        LEFT JOIN module_info ON module_inspect.module_name = module_info.module_name
        LEFT JOIN proto_assembly ON module_info.proto_name = proto_assembly.proto_name
        WHERE 
                ('All' = ANY(ARRAY[${self.bp_material}]) OR 
                (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${self.bp_material}])) OR 
                module_info.bp_material::text = ANY(ARRAY[${self.bp_material}]))
          AND 
                ('All' = ANY(ARRAY[${self.resolution}]) OR 
                (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${self.resolution}])) OR 
                module_info.resolution::text = ANY(ARRAY[${self.resolution}]))
          AND 
                ('All' = ANY(ARRAY[${self.roc_version}]) OR 
                (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${self.roc_version}])) OR 
                module_info.roc_version::text = ANY(ARRAY[${self.roc_version}]))
          AND 
                ('All' = ANY(ARRAY[${self.sen_thickness}]) OR 
                (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${self.sen_thickness}])) OR 
                module_info.sen_thickness::text = ANY(ARRAY[${self.sen_thickness}]))
          AND 
                ('All' = ANY(ARRAY[${self.geometry}]) OR 
                (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${self.geometry}])) OR 
                module_info.geometry::text = ANY(ARRAY[${self.geometry}]))
          AND (module_inspect.date_inspect::timestamp + module_inspect.time_inspect::time)
                BETWEEN ($__timeFrom() AT TIME ZONE '{self.timezone}')
                    AND ($__timeTo()   AT TIME ZONE '{self.timezone}')
          AND 
                ('All' = ANY(ARRAY[${self.grade}]) OR 
                (module_inspect.grade IS NULL AND 'NULL' = ANY(ARRAY[${self.grade}])) OR 
                module_inspect.grade::text = ANY(ARRAY[${self.grade}]))
          AND 
                ('All' = ANY(ARRAY[${self.put_position}]) OR 
                (proto_assembly.put_position IS NULL AND 'NULL' = ANY(ARRAY[${self.put_position}])) OR 
                proto_assembly.put_position::text = ANY(ARRAY[${self.put_position}]))
          AND
                ('All' = ANY(ARRAY[${self.ass_tray_id}]) OR
                (proto_assembly.ass_tray_id IS NULL AND 'NULL' = ANY(ARRAY[${self.ass_tray_id}])) OR
                proto_assembly.ass_tray_id::text = ANY(ARRAY[${self.ass_tray_id}]))
        """

        self.proto_filter_sql = f"""
        LEFT JOIN module_info ON proto_inspect.proto_name = module_info.proto_name
        LEFT JOIN proto_assembly ON module_info.proto_name = proto_assembly.proto_name
        WHERE 
                ('All' = ANY(ARRAY[${self.bp_material}]) OR 
                (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${self.bp_material}])) OR 
                module_info.bp_material::text = ANY(ARRAY[${self.bp_material}]))
          AND 
                ('All' = ANY(ARRAY[${self.resolution}]) OR 
                (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${self.resolution}])) OR 
                module_info.resolution::text = ANY(ARRAY[${self.resolution}]))
          AND 
                ('All' = ANY(ARRAY[${self.roc_version}]) OR 
                (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${self.roc_version}])) OR 
                module_info.roc_version::text = ANY(ARRAY[${self.roc_version}]))
          AND 
                ('All' = ANY(ARRAY[${self.sen_thickness}]) OR 
                (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${self.sen_thickness}])) OR 
                module_info.sen_thickness::text = ANY(ARRAY[${self.sen_thickness}]))
          AND 
                ('All' = ANY(ARRAY[${self.geometry}]) OR 
                (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${self.geometry}])) OR 
                module_info.geometry::text = ANY(ARRAY[${self.geometry}]))
          AND (proto_inspect.date_inspect::timestamp + proto_inspect.time_inspect::time)
                BETWEEN ($__timeFrom() AT TIME ZONE '{self.timezone}')
                    AND ($__timeTo()   AT TIME ZONE '{self.timezone}')
          AND 
                ('All' = ANY(ARRAY[${self.grade}]) OR 
                (proto_inspect.grade IS NULL AND 'NULL' = ANY(ARRAY[${self.grade}])) OR 
                proto_inspect.grade::text = ANY(ARRAY[${self.grade}]))
          AND 
                ('All' = ANY(ARRAY[${self.put_position}]) OR 
                (proto_assembly.put_position IS NULL AND 'NULL' = ANY(ARRAY[${self.put_position}])) OR 
                proto_assembly.put_position::text = ANY(ARRAY[${self.put_position}]))
          AND
                ('All' = ANY(ARRAY[${self.ass_tray_id}]) OR
                (proto_assembly.ass_tray_id IS NULL AND 'NULL' = ANY(ARRAY[${self.ass_tray_id}])) OR
                proto_assembly.ass_tray_id::text = ANY(ARRAY[${self.ass_tray_id}]))
        """

        self.module_offset_sql = """
        SELECT x_offset_mu, y_offset_mu, module_inspect.module_name
        FROM module_inspect 
        """ + self.module_filter_sql

        self.proto_offset_sql = """
        SELECT x_offset_mu, y_offset_mu, proto_inspect.proto_name
        FROM proto_inspect
        """ + self.proto_filter_sql

        self.module_offset_range_sql = """
        WITH range AS (
            SELECT GREATEST(MAX(ABS(x_offset_mu)), MAX(ABS(y_offset_mu))) AS r
            FROM module_inspect
            """ + self.module_filter_sql + """
        )
        SELECT r AS x_offset_mu, r AS y_offset_mu FROM range
        UNION ALL
        SELECT -r AS x_offset_mu, -r AS y_offset_mu FROM range
        """

        self.proto_offset_range_sql = """
        WITH range AS (
            SELECT GREATEST(MAX(ABS(x_offset_mu)), MAX(ABS(y_offset_mu))) AS r
            FROM proto_inspect
            """ + self.proto_filter_sql + """
        )
        SELECT r AS x_offset_mu, r AS y_offset_mu FROM range
        UNION ALL
        SELECT -r AS x_offset_mu, -r AS y_offset_mu FROM range
        """

        self.module_avg_thickness_sql = """
        SELECT module_inspect.avg_thickness
        FROM module_inspect
        """ + self.module_filter_sql

        self.proto_avg_thickness_sql = """
        SELECT proto_inspect.avg_thickness
        FROM proto_inspect
        """ + self.proto_filter_sql

        self.module_angular_offset_sql = """
        SELECT module_inspect.ang_offset_deg
        FROM module_inspect
        """ + self.module_filter_sql

        self.proto_angular_offset_sql = """
        SELECT proto_inspect.ang_offset_deg
        FROM proto_inspect
        """ + self.proto_filter_sql

        self.module_ang_vs_zero_sql = """
        SELECT module_inspect.ang_offset_deg, 0.05 AS y_zero, module_inspect.module_name
        FROM module_inspect
        """ + self.module_filter_sql

        self.proto_ang_vs_zero_sql = """
        SELECT proto_inspect.ang_offset_deg, 0 AS y_zero, proto_inspect.proto_name
        FROM proto_inspect
        """ + self.proto_filter_sql

        self.module_ang_range_sql = """
        WITH range AS (
            SELECT MAX(ABS(ang_offset_deg)) AS r
            FROM module_inspect
            """ + self.module_filter_sql + """
        )
        SELECT r AS ang_offset_deg, 0 AS y_zero FROM range
        UNION ALL
        SELECT -r AS ang_offset_deg, 0 AS y_zero FROM range
        """

        self.proto_ang_range_sql = """
        WITH range AS (
            SELECT MAX(ABS(ang_offset_deg)) AS r
            FROM proto_inspect
            """ + self.proto_filter_sql + """
        )
        SELECT r AS ang_offset_deg, 0 AS y_zero FROM range
        UNION ALL
        SELECT -r AS ang_offset_deg, 0 AS y_zero FROM range
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

    ### Module XY Offset
                {
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
                },
                "gridPos": {
                    "h": 14,
                    "w": 12,
                    "x": 0,
                    "y": 28
                },
                "id": 1,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "mapping": "auto",
                    "series": [
                    {}
                    ],
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
                    "rawSql": self.module_offset_sql,
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-75,-75),(-75,75),(75,75),(75,-75),(-75,-75)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "B"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-110,-110),(-110,110),(110,110),(110,-110),(-110,-110)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "C"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0,0)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "D"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.module_offset_range_sql,
                    "refId": "E"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": True,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 50,
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "pointShape": "circle",
                        "pointSize": {
                        "fixed": 5
                        },
                        "pointStrokeWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "show": "points"
                    },
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "A"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "module"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "x_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "x_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "y_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "y_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "B"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "blue",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "75 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "C"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "red",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "110 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "D"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "white",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Tray"
                        },
                        {
                            "id": "custom.show",
                            "value": "points"
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 10}
                        },
                        {
                            "id": "custom.pointShape",
                            "value": "circle"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "E"
                        },
                        "properties": [
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": True,
                            "viz": True
                            }
                        }
                        ]
                    }
                    ]
                },
                "title": "Module Offset",
                "type": "xychart"
                },

    ### Proto XY Offset
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
                        "axisCenteredZero": True,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 50,
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "pointShape": "circle",
                        "pointSize": {
                        "fixed": 5
                        },
                        "pointStrokeWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "show": "points"
                    },
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "A"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "proto-module"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "x_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "x_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "y_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "y_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "B"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "blue",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "75 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "C"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "red",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "110 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "D"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "white",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Tray"
                        },
                        {
                            "id": "custom.show",
                            "value": "points"
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 10}
                        },
                        {
                            "id": "custom.pointShape",
                            "value": "circle"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "E"
                        },
                        "properties": [
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": True,
                            "viz": True
                            }
                        }
                        ]
                    }
                    ]
                },
                "gridPos": {
                    "h": 14,
                    "w": 12,
                    "x": 12,
                    "y": 28
                },
                "id": 2,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "mapping": "auto",
                    "series": [
                    {}
                    ],
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
                    "rawSql": self.proto_offset_sql,
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-75,-75),(-75,75),(75,75),(75,-75),(-75,-75)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "B"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-110,-110),(-110,110),(110,110),(110,-110),(-110,-110)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "C"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0,0)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "D"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.proto_offset_range_sql,
                    "refId": "E"
                    }
                ],
                "title": "Proto-Module Offset",
                "type": "xychart"
                },

    ### Combined Proto + Module Offset
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
                        "axisCenteredZero": True,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 50,
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "pointShape": "circle",
                        "pointSize": {
                        "fixed": 5
                        },
                        "pointStrokeWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "show": "points"
                    },
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "A"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "Sensor w.r.t Tray"
                        },
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
                        "id": "byFrameRefID",
                        "options": "B"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "Hxb w.r.t Tray"
                        },
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
                        "options": "x_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "x_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "y_offset_mu"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "y_offset_mu"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "C"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "blue",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "75 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "D"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "red",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "110 μm"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "E"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "white",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Tray"
                        },
                        {
                            "id": "custom.show",
                            "value": "points"
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 10}
                        },
                        {
                            "id": "custom.pointShape",
                            "value": "circle"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "F"
                        },
                        "properties": [
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": True,
                            "viz": True
                            }
                        }
                        ]
                    }
                    ]
                },
                "gridPos": {
                    "h": 14,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "id": 100,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "mapping": "auto",
                    "series": [
                    {}
                    ],
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
                    "rawSql": self.proto_offset_sql,
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.module_offset_sql,
                    "refId": "B",
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-75,-75),(-75,75),(75,75),(75,-75),(-75,-75)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "C"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-110,-110),(-110,110),(110,110),(110,-110),(-110,-110)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "D"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0,0)) AS t(x_offset_mu, y_offset_mu)",
                    "refId": "E"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.proto_offset_range_sql,
                    "refId": "F"
                    }
                ],
                "title": "X-Y offsets for modules and protomodules",
                "type": "xychart"
                },

    ### Combined Proto + Module Offset (copy)
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
                        "axisCenteredZero": True,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "fillOpacity": 50,
                        "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                        },
                        "pointShape": "circle",
                        "pointSize": {
                        "fixed": 5
                        },
                        "pointStrokeWidth": 1,
                        "scaleDistribution": {
                        "type": "linear"
                        },
                        "show": "points"
                    },
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "A"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "Sensor w.r.t Tray"
                        },
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
                        "id": "byFrameRefID",
                        "options": "B"
                        },
                        "properties": [
                        {
                            "id": "displayName",
                            "value": "Hxb w.r.t Tray"
                        },
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
                        "options": "ang_offset_deg"
                        },
                        "properties": [
                        {
                            "id": "custom.axisLabel",
                            "value": "ang_offset_deg"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "y_zero"
                        },
                        "properties": [
                        {
                            "id": "custom.axisPlacement",
                            "value": "hidden"
                        },
                        {
                            "id": "custom.axisGridShow",
                            "value": False
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "C"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "blue",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "±0.04°"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "D"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "blue",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        },
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": False,
                            "viz": False
                            }
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "E2"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "red",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "±0.1°"
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "F2"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "red",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "custom.show",
                            "value": "lines"
                        },
                        {
                            "id": "custom.fillOpacity",
                            "value": 0
                        },
                        {
                            "id": "custom.lineWidth",
                            "value": 2
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 0}
                        },
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": False,
                            "viz": False
                            }
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "E"
                        },
                        "properties": [
                        {
                            "id": "color",
                            "value": {
                            "fixedColor": "white",
                            "mode": "fixed"
                            }
                        },
                        {
                            "id": "displayName",
                            "value": "Tray"
                        },
                        {
                            "id": "custom.show",
                            "value": "points"
                        },
                        {
                            "id": "custom.pointSize",
                            "value": {"fixed": 10}
                        },
                        {
                            "id": "custom.pointShape",
                            "value": "circle"
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byFrameRefID",
                        "options": "F"
                        },
                        "properties": [
                        {
                            "id": "custom.hideFrom",
                            "value": {
                            "legend": True,
                            "tooltip": True,
                            "viz": True
                            }
                        }
                        ]
                    }
                    ]
                },
                "gridPos": {
                    "h": 14,
                    "w": 12,
                    "x": 12,
                    "y": 0
                },
                "id": 101,
                "options": {
                    "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                    },
                    "mapping": "auto",
                    "series": [
                    {}
                    ],
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
                    "rawSql": self.proto_ang_vs_zero_sql,
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.module_ang_vs_zero_sql,
                    "refId": "B",
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
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0.04, 1), (0.04, -1)) AS t(ang_offset_deg, y_zero)",
                    "refId": "C"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-0.04, 1), (-0.04, -1)) AS t(ang_offset_deg, y_zero)",
                    "refId": "D"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0.1, 1), (0.1, -1)) AS t(ang_offset_deg, y_zero)",
                    "refId": "E2"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (-0.1, 1), (-0.1, -1)) AS t(ang_offset_deg, y_zero)",
                    "refId": "F2"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "SELECT * FROM (VALUES (0, 0)) AS t(ang_offset_deg, y_zero)",
                    "refId": "E"
                    },
                    {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": self.datasource_uid
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": self.proto_ang_range_sql,
                    "refId": "F"
                    }
                ],
                "title": "Angular (deg) offsets for modules and protomodules",
                "type": "xychart"
                },

    ### Module Average Thickness (mm)
                {
                "id": 3,
                "type": "histogram",
                "title": "Module Average Thickness (mm)",
                "gridPos": {
                    "x": 0,
                    "y": 12,
                    "h": 8,
                    "w": 12
                },
                "fieldConfig": {
                    "defaults": {
                    "custom": {
                        "stacking": {
                        "mode": "none",
                        "group": "A"
                        },
                        "lineWidth": 1,
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "tooltip": False,
                        "viz": False,
                        "legend": False
                        }
                    },
                    "color": {
                        "mode": "palette-classic"
                    },
                    "mappings": [],
                    },
                    "overrides": []
                },
                "transformations": [
                    {
                    "id": "filterFieldsByName",
                    "options": {}
                    },
                    {
                    "id": "partitionByValues",
                    "options": {
                        "fields": [
                        "log_location"
                        ],
                        "keepFields": False
                    }
                    }
                ],
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
                    "rawSql": self.module_avg_thickness_sql,
                    "refId": "A",
                    }
                ],
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
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
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "normal",
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                }
                },
                
    ### Proto Average Thickness (mm)
                {
                "id": 4,
                "type": "histogram",
                "title": "Proto Average Thickness (mm)",
                "gridPos": {
                    "x": 12,
                    "y": 12,
                    "h": 8,
                    "w": 12
                },
                "fieldConfig": {
                    "defaults": {
                    "custom": {
                        "stacking": {
                        "mode": "none",
                        "group": "A"
                        },
                        "lineWidth": 1,
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "tooltip": False,
                        "viz": False,
                        "legend": False
                        }
                    },
                    "color": {
                        "mode": "palette-classic"
                    },
                    "mappings": [],
                    },
                    "overrides": []
                },
                "transformations": [
                    {
                    "id": "filterFieldsByName",
                    "options": {}
                    },
                    {
                    "id": "partitionByValues",
                    "options": {
                        "fields": [
                        "log_location"
                        ],
                        "keepFields": False
                    }
                    }
                ],
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
                    "rawSql": self.proto_avg_thickness_sql,
                    "refId": "A",
                    }
                ],
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
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
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "normal",
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                }
                },

    ### Module Angular Offset
                {
                "id": 5,
                "type": "histogram",
                "title": "Module Angular Offset",
                "gridPos": {
                    "x": 0,
                    "y": 20,
                    "h": 8,
                    "w": 12
                },
                "fieldConfig": {
                    "defaults": {
                    "custom": {
                        "stacking": {
                        "mode": "none",
                        "group": "A"
                        },
                        "lineWidth": 1,
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "tooltip": False,
                        "viz": False,
                        "legend": False
                        }
                    },
                    "color": {
                        "mode": "palette-classic"
                    },
                    "mappings": [],
                    },
                    "overrides": []
                },
                "transformations": [
                    {
                    "id": "filterFieldsByName",
                    "options": {}
                    },
                    {
                    "id": "partitionByValues",
                    "options": {
                        "fields": [
                        "log_location"
                        ],
                        "keepFields": False
                    }
                    }
                ],
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
                    "rawSql": self.module_angular_offset_sql,
                    "refId": "A",
                    }
                ],
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
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
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "normal",
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                }
                }, 
    
    ### Proto Angular Offset
                {
                "id": 6,
                "type": "histogram",
                "title": "Proto Angular Offset",
                "gridPos": {
                    "x": 12,
                    "y": 20,
                    "h": 8,
                    "w": 12
                },
                "fieldConfig": {
                    "defaults": {
                    "custom": {
                        "stacking": {
                        "mode": "none",
                        "group": "A"
                        },
                        "lineWidth": 1,
                        "fillOpacity": 80,
                        "gradientMode": "none",
                        "hideFrom": {
                        "tooltip": False,
                        "viz": False,
                        "legend": False
                        }
                    },
                    "color": {
                        "mode": "palette-classic"
                    },
                    "mappings": [],
                    },
                    "overrides": []
                },
                "transformations": [
                    {
                    "id": "filterFieldsByName",
                    "options": {}
                    },
                    {
                    "id": "partitionByValues",
                    "options": {
                        "fields": [
                        "log_location"
                        ],
                        "keepFields": False
                    }
                    }
                ],
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
                    "rawSql": self.proto_angular_offset_sql,
                    "refId": "A",
                    }
                ],
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": self.datasource_uid
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
                    "barRadius": 0,
                    "barWidth": 0.97,
                    "fullHighlight": False,
                    "groupWidth": 0.7,
                    "orientation": "horizontal",
                    "showValue": "auto",
                    "stacking": "normal",
                    "xTickLabelRotation": 0,
                    "xTickLabelSpacing": 0
                }
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
                    "includeAll": True,
                    "multi": True,
                    "name": "grade",
                    "options": [],
                    "query": "\n            SELECT DISTINCT grade::text FROM module_inspect \n            UNION\n            SELECT 'NULL'\n            ORDER BY grade\n            ",
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
                    "name": "put_position",
                    "options": [],
                    "query": "\n            SELECT DISTINCT put_position::text FROM proto_assembly \n            UNION\n            SELECT 'NULL'\n            ORDER BY put_position\n            ",
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
                    "name": "ass_tray_id",
                    "options": [],
                    "query": "\n            SELECT DISTINCT ass_tray_id::text FROM proto_assembly \n            UNION\n            SELECT 'NULL'\n            ORDER BY ass_tray_id\n            ",
                    "refresh": 1,
                    "type": "query"
                }
                ]
            },
            "time": {
                "from": "now-1y",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "Offset Plots",
            "uid": f"{self.dashboard_uid}",
            "version": 1
        }

        return dashboard_json
