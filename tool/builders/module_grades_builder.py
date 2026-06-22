from tool.helper import *
class ModuleGradesBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = "module-grades"
        self.timezone = f"{timezone}"
        self.bp_material = "{bp_material}"
        self.resolution = "{resolution}"
        self.roc_version = "{roc_version}"
        self.sen_thickness = "{sen_thickness}"
        self.geometry = "{geometry}"
        self.final_grade = "{final_grade}"
        self.module_name = "{module_name}"
        self.show_latest_only = "{show_latest_only}"
        self.uninstallable_only = "{uninstallable_only}"
        self.show_grade_changed_modules = "{show_grade_changed_modules}"

        self.table_sql = f"""WITH ranked AS (
SELECT
    module_info.module_no,
    module_qc_summary.mod_qc_no,
    module_qc_summary.module_name,
    CASE WHEN
        NOT (LOWER(COALESCE(module_qc_summary.proto_corner_colorgrades::text, '')) LIKE '%red%')
        AND NOT (LOWER(COALESCE(module_qc_summary.module_corner_colorgrades::text, '')) LIKE '%red%')
        AND module_qc_summary.final_grade IS DISTINCT FROM 'F'
        AND module_qc_summary.proto_grade IS DISTINCT FROM 'F'
        AND module_qc_summary.module_grade IS DISTINCT FROM 'F'
        AND module_qc_summary.iv_grade IS DISTINCT FROM 'F'
        AND module_qc_summary.readout_grade IS DISTINCT FROM 'F'
    THEN 'green' ELSE 'red' END AS installation_status,
    module_qc_summary.final_grade::text,
    module_qc_summary.proto_grade::text,
    module_qc_summary.module_grade::text,
    module_qc_summary.iv_grade::text,
    module_qc_summary.readout_grade::text,
    module_qc_summary.proto_corner_colorgrades::text AS proto_corner_colorgrades,
    module_qc_summary.module_corner_colorgrades::text AS module_corner_colorgrades,
    module_qc_summary.comments_all::text,
    module_qc_summary.grade_timestamp::text
FROM module_qc_summary
JOIN module_info ON module_qc_summary.module_name = module_info.module_name
WHERE
    ('${self.module_name}' = '' OR module_qc_summary.module_name ILIKE '%' || '${self.module_name}' || '%')
  AND
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
  AND
    ('All' = ANY(ARRAY[${self.final_grade}]) OR
     (module_qc_summary.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${self.final_grade}])) OR
     module_qc_summary.final_grade::text = ANY(ARRAY[${self.final_grade}]))
  AND $__timeFilter(module_info.assembled AT TIME ZONE '{self.timezone}')
  AND module_info.bp_material IS NOT NULL
  AND module_info.resolution IS NOT NULL
  AND module_info.roc_version IS NOT NULL
  AND module_info.geometry IS NOT NULL
),
latest AS (
    SELECT DISTINCT ON (module_name) *
    FROM ranked
    ORDER BY module_name, mod_qc_no DESC
),
latest_uninstallable_modules AS (
    SELECT module_name FROM latest WHERE installation_status = 'red'
),
grade_order AS (
    SELECT module_name,
        MIN(CASE final_grade WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'F' THEN 4 END) AS best_grade_rank,
        MAX(CASE final_grade WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'F' THEN 4 END) AS worst_grade_rank
    FROM ranked
    WHERE final_grade IS NOT NULL
    GROUP BY module_name
),
deteriorated_modules AS (
    SELECT module_name FROM grade_order WHERE worst_grade_rank > best_grade_rank
)
SELECT * FROM (
    SELECT * FROM ranked WHERE '${self.show_latest_only}' = 'false'
    UNION ALL
    SELECT * FROM latest WHERE '${self.show_latest_only}' = 'true'
) combined
WHERE ('${self.uninstallable_only}' = 'false'
   OR combined.module_name IN (SELECT module_name FROM latest_uninstallable_modules))
  AND ('${self.show_grade_changed_modules}' = 'false'
   OR combined.module_name IN (SELECT module_name FROM deteriorated_modules))
ORDER BY module_no DESC, mod_qc_no DESC"""

    def _grade_color_override(self, column_name):
        """Return a fieldConfig override that color-codes A=green, B=yellow, C=orange, F=red, null=transparent."""
        return {
            "matcher": {
                "id": "byName",
                "options": column_name
            },
            "properties": [
                {
                    "id": "mappings",
                    "value": [
                        {
                            "options": {
                                "A": {"color": "green", "index": 0},
                                "B": {"color": "yellow", "index": 1},
                                "C": {"color": "orange", "index": 2},
                                "F": {"color": "red", "index": 3}
                            },
                            "type": "value"
                        },
                        {
                            "options": {
                                "match": "null",
                                "result": {"color": "transparent", "index": 4}
                            },
                            "type": "special"
                        }
                    ]
                },
                {
                    "id": "custom.cellOptions",
                    "value": {"type": "color-background"}
                }
            ]
        }

    def generate_dashboard_json(self):
        grade_columns = [
            "final_grade",
            "proto_grade",
            "module_grade",
            "iv_grade",
            "readout_grade",
        ]

        rename_map = {
            "final_grade": "Final Grade",
            "proto_grade": "Proto Mech Grade",
            "module_grade": "Module Mech Grade",
            "iv_grade": "IV Grade",
            "readout_grade": "Readout Grade",
            "proto_corner_colorgrades": "Proto Corner Colorgrades",
            "module_corner_colorgrades": "Module Corner Colorgrades",
            "comments_all": "Comments",
        }

        colorgrade_columns = [
            "proto_corner_colorgrades",
            "module_corner_colorgrades",
        ]

        overrides = []

        # Rename plain columns (no color needed)
        plain_rename = {k: v for k, v in rename_map.items() if k not in colorgrade_columns}
        for col, label in plain_rename.items():
            overrides.append({
                "matcher": {"id": "byName", "options": col},
                "properties": [{"id": "displayName", "value": label}]
            })

        # Fixed-width columns
        overrides.append({
            "matcher": {"id": "byName", "options": "module_no"},
            "properties": [{"id": "custom.width", "value": 80}]
        })
        overrides.append({
            "matcher": {"id": "byName", "options": "mod_qc_no"},
            "properties": [{"id": "custom.width", "value": 80}]
        })
        overrides.append({
            "matcher": {"id": "byName", "options": "module_name"},
            "properties": [{"id": "custom.width", "value": 161}]
        })
        # installation_status: narrow colored indicator column (green=installable, red=not)
        overrides.append({
            "matcher": {"id": "byName", "options": "installation_status"},
            "properties": [
                {"id": "custom.width", "value": 20},
                {"id": "displayName", "value": ""},
                {"id": "custom.cellOptions", "value": {"type": "color-background"}},
                {
                    "id": "mappings",
                    "value": [
                        {
                            "options": {
                                "green": {"color": "green", "index": 0, "text": ""},
                                "red":   {"color": "red",   "index": 1, "text": "X"}
                            },
                            "type": "value"
                        }
                    ]
                }
            ]
        })

        # Color-code each grade column
        for col in grade_columns:
            overrides.append(self._grade_color_override(col))

        # Colorgrade columns: rename + color in one override so byName matches before any rename applies
        colorgrade_regex_props = [
            {
                "id": "mappings",
                "value": [
                    {
                        "options": {
                            "pattern": ".*[Rr][Ee][Dd].*",
                            "result": {"color": "red", "index": 0}
                        },
                        "type": "regex"
                    },
                    {
                        "options": {
                            "pattern": ".*[Pp][Uu][Rr][Pp][Ll][Ee].*",
                            "result": {"color": "purple", "index": 1}
                        },
                        "type": "regex"
                    },
                    {
                        "options": {
                            "pattern": ".*[Yy][Ee][Ll][Ll][Oo][Ww].*",
                            "result": {"color": "yellow", "index": 2}
                        },
                        "type": "regex"
                    },
                    {
                        "options": {
                            "match": "null",
                            "result": {"color": "transparent", "index": 3}
                        },
                        "type": "special"
                    },
                    {
                        "options": {
                            "pattern": ".+",
                            "result": {"color": "green", "index": 4}
                        },
                        "type": "regex"
                    }
                ]
            },
            {"id": "custom.cellOptions", "value": {"type": "color-background"}}
        ]
        for col in colorgrade_columns:
            label = rename_map[col]
            overrides.append({
                "matcher": {"id": "byName", "options": col},
                "properties": [
                    {"id": "displayName", "value": label},
                    *colorgrade_regex_props
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
                                "align": "auto",
                                "cellOptions": {"type": "auto"},
                                "inspect": False
                            },
                            "decimals": 0,
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green"},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        },
                        "overrides": overrides
                    },
                    "gridPos": {"h": 20, "w": 24, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "cellHeight": "sm",
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
                    "title": "Module Grades",
                    "type": "table"
                }
            ],
            "preload": False,
            "refresh": "5m",
            "schemaVersion": 41,
            "tags": [],
            "templating": {
                "list": [
                    {
                        "current": {"text": "", "value": ""},
                        "label": "module_name",
                        "name": "module_name",
                        "options": [{"selected": True, "text": "", "value": ""}],
                        "query": "",
                        "type": "textbox"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "bp_material",
                        "options": [],
                        "query": "\n            SELECT DISTINCT bp_material::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY bp_material\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "resolution",
                        "options": [],
                        "query": "\n            SELECT DISTINCT resolution::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY resolution\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "roc_version",
                        "options": [],
                        "query": "\n            SELECT DISTINCT roc_version::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY roc_version\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "sen_thickness",
                        "options": [],
                        "query": "\n            SELECT DISTINCT sen_thickness::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY sen_thickness\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "geometry",
                        "options": [],
                        "query": "\n            SELECT DISTINCT geometry::text FROM module_info \n            UNION\n            SELECT 'NULL'\n            ORDER BY geometry\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "All", "value": ["$__all"]},
                        "datasource": {"type": "postgres", "uid": self.datasource_uid},
                        "includeAll": True,
                        "multi": True,
                        "name": "final_grade",
                        "options": [],
                        "query": "\n            SELECT DISTINCT final_grade::text FROM module_qc_summary \n            UNION\n            SELECT 'NULL'\n            ORDER BY final_grade\n            ",
                        "refresh": 1,
                        "type": "query"
                    },
                    {
                        "current": {"text": "true", "value": "true"},
                        "label": "Show Latest Only",
                        "name": "show_latest_only",
                        "options": [
                            {"selected": False, "text": "false", "value": "false"},
                            {"selected": True,  "text": "true",  "value": "true"}
                        ],
                        "query": "false,true",
                        "type": "custom"
                    },
                    {
                        "current": {"text": "false", "value": "false"},
                        "label": "Uninstallable Only",
                        "name": "uninstallable_only",
                        "options": [
                            {"selected": True,  "text": "false", "value": "false"},
                            {"selected": False, "text": "true",  "value": "true"}
                        ],
                        "query": "false,true",
                        "type": "custom"
                    },
                    {
                        "current": {"text": "false", "value": "false"},
                        "label": "Show Grade Changed Modules",
                        "name": "show_grade_changed_modules",
                        "options": [
                            {"selected": True,  "text": "false", "value": "false"},
                            {"selected": False, "text": "true",  "value": "true"}
                        ],
                        "query": "false,true",
                        "type": "custom"
                    }
                ]
            },
            "time": {
                "from": "now-10y",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": "Module Grades",
            "uid": self.dashboard_uid
        }

        return dashboard_json
