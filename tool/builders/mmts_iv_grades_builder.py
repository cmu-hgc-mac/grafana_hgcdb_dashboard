from tool.helper import *

class MMTSIVGradesBuilder:
    def __init__(self, datasource_uid, timezone='America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("MMTS IV Grades by Position")
        self.timezone = f"{timezone}"

        self.table_sql = f"""
        WITH counts AS (
            SELECT
                station_name,
                grade,
                COUNT(*) AS grade_count,
                STRING_AGG(module_name, ', ' ORDER BY module_name) AS module_names
            FROM module_iv_test
            WHERE station_name ~ '^MMTS_[1-8][LCR]$'
                AND status_desc ILIKE '%bolted%'
                AND ('${{batch_name}}' = '' OR batch_name ILIKE '%' || '${{batch_name}}' || '%')
                AND ('${{iteration}}' = '' OR iteration ILIKE '%' || '${{iteration}}' || '%')
                AND ('All' = ANY(ARRAY[${{grade}}]) OR
                     (grade IS NULL AND 'NULL' = ANY(ARRAY[${{grade}}])) OR
                     grade::text = ANY(ARRAY[${{grade}}]))
            GROUP BY station_name, grade
        ),
        stacked AS (
            SELECT
                station_name,
                'Total: ' || SUM(grade_count)::text || E'\\n' || STRING_AGG(
                    COALESCE(grade, 'NULL') || ':' || grade_count::text ||
                        CASE WHEN '${{show_module_names}}' = 'true' THEN ' [' || module_names || ']' ELSE '' END,
                    E'\\n'
                    ORDER BY CASE grade WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'F' THEN 4 ELSE 5 END
                ) AS grade_counts,
                (ARRAY_AGG(grade ORDER BY grade_count DESC, grade))[1] AS dominant_grade,
                SUM(grade_count) AS total_count
            FROM counts
            GROUP BY station_name
        ),
        positions AS (
            SELECT
                row_no,
                col AS position,
                'MMTS_' || row_no::text || col AS station_name
            FROM generate_series(1, 8) AS row_no
            CROSS JOIN unnest(ARRAY['L', 'C', 'R']) AS col
        )
        SELECT
            positions.row_no AS "Row",
            MAX(CASE WHEN positions.position = 'L' THEN COALESCE(stacked.grade_counts, '') END) AS "L",
            MAX(CASE WHEN positions.position = 'C' THEN COALESCE(stacked.grade_counts, '') END) AS "C",
            MAX(CASE WHEN positions.position = 'R' THEN COALESCE(stacked.grade_counts, '') END) AS "R",
            MAX(CASE WHEN positions.position = 'L' THEN COALESCE(stacked.dominant_grade, '') END) AS "L_grade",
            MAX(CASE WHEN positions.position = 'C' THEN COALESCE(stacked.dominant_grade, '') END) AS "C_grade",
            MAX(CASE WHEN positions.position = 'R' THEN COALESCE(stacked.dominant_grade, '') END) AS "R_grade"
        FROM positions
        LEFT JOIN stacked ON stacked.station_name = positions.station_name
        GROUP BY positions.row_no
        ORDER BY positions.row_no;
        """

    def generate_dashboard_json(self):
        overrides = []

        # hide the helper dominant-grade columns; kept in the query for potential
        # future use but the visible L/C/R text already encodes the dominant grade first
        for col in ["L_grade", "C_grade", "R_grade"]:
            overrides.append({
                "matcher": {"id": "byName", "options": col},
                "properties": [
                    {"id": "custom.hidden", "value": True}
                ]
            })

        # color each L/C/R column by its own leading grade text (dominant grade appears first, e.g. "A:8 B:3")
        for col in ["L", "C", "R"]:
            overrides.append({
                "matcher": {"id": "byName", "options": col},
                "properties": [
                    {
                        "id": "mappings",
                        "value": [
                            {
                                "options": {"pattern": "(?s).*\\nA:.*", "result": {"color": "green"}},
                                "type": "regex"
                            },
                            {
                                "options": {"pattern": "(?s).*\\nB:.*", "result": {"color": "yellow"}},
                                "type": "regex"
                            },
                            {
                                "options": {"pattern": "(?s).*\\nC:.*", "result": {"color": "orange"}},
                                "type": "regex"
                            },
                            {
                                "options": {"pattern": "(?s).*\\nF:.*", "result": {"color": "red"}},
                                "type": "regex"
                            },
                            {
                                "options": {"match": "empty", "result": {"color": "transparent"}},
                                "type": "special"
                            }
                        ]
                    },
                    {
                        "id": "custom.cellOptions",
                        "value": {"type": "color-background", "wrapText": True}
                    },
                    {
                        "id": "custom.width",
                        "value": 320
                    }
                ]
            })

        overrides.append({
            "matcher": {"id": "byName", "options": "Row"},
            "properties": [
                {"id": "custom.width", "value": 60}
            ]
        })

        dashboard_json = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": {"type": "grafana", "uid": "-- Grafana --"},
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
                            "color": {"mode": "thresholds"},
                            "custom": {
                                "align": "center",
                                "cellOptions": {"type": "auto"},
                                "inspect": False
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green"}
                                ]
                            }
                        },
                        "overrides": overrides
                    },
                    "gridPos": {"h": 20, "w": 12, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "cellHeight": "xl",
                        "footer": {
                            "countRows": False,
                            "fields": "",
                            "reducer": ["sum"],
                            "show": False
                        },
                        "showHeader": True,
                        "sortBy": []
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
                            "rawSql": self.table_sql,
                            "refId": "A",
                            "sql": {
                                "columns": [{"parameters": [], "type": "function"}],
                                "groupBy": [{"property": {"type": "string"}, "type": "groupBy"}],
                                "limit": 50
                            }
                        }
                    ],
                    "title": "MMTS IV Grades by Position",
                    "type": "table"
                }
            ],
            "preload": False,
            "refresh": "",
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                    {
                        "current": {"text": "", "value": ""},
                        "label": "batch_name",
                        "name": "batch_name",
                        "options": [{"selected": True, "text": "", "value": ""}],
                        "query": "",
                        "type": "textbox"
                    },
                    {
                        "current": {"text": "", "value": ""},
                        "label": "iteration",
                        "name": "iteration",
                        "options": [{"selected": True, "text": "", "value": ""}],
                        "query": "",
                        "type": "textbox"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "includeAll": True,
                        "label": "grade",
                        "multi": True,
                        "name": "grade",
                        "options": [
                            {"selected": True, "text": "All", "value": "$__all"},
                            {"selected": False, "text": "A", "value": "A"},
                            {"selected": False, "text": "B", "value": "B"},
                            {"selected": False, "text": "C", "value": "C"},
                            {"selected": False, "text": "F", "value": "F"},
                            {"selected": False, "text": "NULL", "value": "NULL"}
                        ],
                        "query": "A,B,C,F,NULL",
                        "type": "custom"
                    },
                    {
                        "current": {"text": "false", "value": "false"},
                        "label": "Show Module Names",
                        "name": "show_module_names",
                        "options": [
                            {"selected": True, "text": "false", "value": "false"},
                            {"selected": False, "text": "true", "value": "true"}
                        ],
                        "query": "false,true",
                        "type": "custom"
                    }
                ]
            },
            "time": {
                "from": "now-90d",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "MMTS IV Grades by Position",
            "uid": self.dashboard_uid,
            "version": 1
        }

        return dashboard_json
