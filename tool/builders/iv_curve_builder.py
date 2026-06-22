from tool.helper import *
from tool.builders.sql_builder import BaseSQLGenerator


class IVCurveBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.SQLgenerator = BaseSQLGenerator()

    # -- IV Curve Plot Version 2.0 --
    def IV_curve_panel_filter(self, filters: dict) -> str:
        """Build the WHERE clause for IV curve plot based on the given filters.
        """
        module_where_clauses = []
        iv_where_clauses = []

        for filter_table, _ in filters.items():
            if filter_table == "module_info":
                for elem in filters[filter_table]:
                    arg = self.SQLgenerator._build_filter_argument(elem, filter_table)
                    module_where_clauses.append(arg)
                    module_where_arg = " AND ".join(module_where_clauses)
            elif filter_table == "module_qc_summary":
                for elem in filters[filter_table]:
                    arg = self.SQLgenerator._build_filter_argument(elem, "latest_qc_summary")
                        # filter_table rename due to the distinct fetch for `module_qc_summary` table
                    iv_where_clauses.append(arg)
                    iv_where_arg = " AND ".join(iv_where_clauses)

        return module_where_arg, iv_where_arg

    def IV_curve_panel_sql(self, filters: dict, temp_condition: str, rel_hum_condition: str, N_MODULE_SHOW="${N_MODULE_SHOW}") -> str:
        """Generate the SQL command for IV curve plot based on temp_condition and rel_hum_condition.
           Core filtering logic: Andrew C. Roberts
        """
        # build the WHERE clause
        module_where_arg, iv_where_arg = self.IV_curve_panel_filter(filters)

        # generate the SQL command
        raw_sql = rf"""
        WITH latest_qc_summary AS (
            SELECT DISTINCT ON (module_name) *
            FROM module_qc_summary
            ORDER BY module_name, mod_qc_no DESC
        ),

        latest_iv_test AS (
            SELECT DISTINCT ON (module_name) *
            FROM module_iv_test
            WHERE $__timeFilter(module_iv_test.date_test)
            AND meas_v IS NOT NULL AND meas_i IS NOT NULL
            AND {temp_condition}
            AND {rel_hum_condition}
            AND temp_c ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND rel_hum ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND (status_desc = 'Completely Encapsulated' OR status_desc = 'Frontside Encapsulated' OR status_desc = 'Bolted')
            AND array_length(meas_v, 1) = array_length(meas_i, 1)
            ORDER BY module_name, date_test DESC
        ),

        selected_modules AS (
        SELECT
            module_info.module_name
        FROM module_info
        JOIN latest_iv_test ON module_info.module_name = latest_iv_test.module_name
        LEFT JOIN latest_qc_summary ON module_info.module_name = latest_qc_summary.module_name
        WHERE {module_where_arg}
            AND {iv_where_arg}
        ORDER BY module_info.module_no DESC
        LIMIT {N_MODULE_SHOW}
        ),

        filtered_iv AS (
        SELECT *,
            meas_i[array_length(meas_i, 1)] AS i_last
        FROM module_iv_test
        WHERE
            module_name IN (SELECT module_name FROM selected_modules)
        ),

        best_per_module AS (
        SELECT DISTINCT ON (filtered_iv.module_name) *
        FROM filtered_iv
        WHERE $__timeFilter(filtered_iv.date_test)
            AND meas_v IS NOT NULL AND meas_i IS NOT NULL
            AND {temp_condition}
            AND {rel_hum_condition}
            AND temp_c ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND rel_hum ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND (status_desc = 'Completely Encapsulated' OR status_desc = 'Frontside Encapsulated' OR status_desc = 'Bolted')
            AND array_length(meas_v, 1) = array_length(meas_i, 1)
        ORDER BY filtered_iv.module_name, i_last ASC
        ),

        unnested AS (
        SELECT
            module_name,
            ABS(v) as v,
            i
        FROM best_per_module,
        UNNEST(meas_v, meas_i) AS t(v, i)
        )

        SELECT *
        FROM unnested
        ORDER BY module_name ASC;
        """

        return raw_sql

    def IV_curve_panel_override(self) -> list:
        """Override the default config for IV curve plot.
        """
        override = [
            {
                "matcher": {
                "id": "byName",
                "options": "i"
                },
                "properties": [
                {
                    "id": "custom.axisPlacement",
                    "value": "left"
                },
                {
                    "id": "custom.scaleDistribution",
                    "value": {
                    "log": 10,
                    "type": "log"
                    }
                },
                {
                    "id": "max",
                    "value": 1e-03
                },
                {
                    "id": "min",
                    "value": 1e-09
                },
                {
                    "id": "unit",
                    "value": "sci"
                },
                {
                    "id": "custom.axisLabel",
                    "value": "Leakage Current [A]"
                }
                ]
            },
            {
                "matcher": {
                "id": "byName",
                "options": "v"
                },
                "properties": [
                {
                    "id": "max",
                    "value": 500
                },
                {
                    "id": "min",
                    "value": 0
                },
                {
                    "id": "custom.axisLabel",
                    "value": "Reverse Bias [V]"
                }
                ]
            }
        ]

        return override

    def generate_IV_curve_panel_new(self, title: str, raw_sql: str, override: list, gridPos: dict) -> dict:
        """A new version of IV curve panel JSON.
        """
        panel_json = {
        "id": 1,
        "type": "xychart",
        "title": f"{title}",
        "gridPos": gridPos,
        "fieldConfig": {
            "defaults": {
            "custom": {
                "show": "lines+points",
                "pointSize": {
                "fixed": 2
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
            "mappings": [],
            },
            "overrides": override
        },
        "transformations": [
            {
            "id": "partitionByValues",
            "options": {
                "fields": [
                "module_name"
                ],
                "keepFields": True
            }
            }
        ],
        "pluginVersion": "12.0.0",
        "targets": [
            {
            "datasource": {
                "type": "grafana-postgresql-datasource",
                "uid": f"{self.datasource_uid}"
            },
            "editorMode": "code",
            "format": "table",
            "rawQuery": True,
            "rawSql": f"{raw_sql}",
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
        "datasource": {
            "type": "grafana-postgresql-datasource",
            "uid": f"{self.datasource_uid}"
        },
        "options": {
            "mapping": "auto",
            "series": [
            {
                "x": {
                "matcher": {
                    "id": "byName",
                    "options": "v"
                }
                },
                "y": {
                "matcher": {
                    "id": "byName",
                    "options": "i"
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
            "placement": "right",
            "calcs": []
            }
        }
        }

        return panel_json
