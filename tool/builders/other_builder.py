from tool.helper import *
from tool.builders.sql_builder import BaseSQLGenerator

"""
This file defines classes for building additional Grafana features, including:
    - Filters: With support from Wen Li.
"""

# ============================================================
# === Filert Builder =========================================
# ============================================================

class FilterBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
    
    def generate_filter(self, filter_name: str, filter_sql: str) -> dict:
        """Generate a template json based on the given .
        """
        # generate the filter json:
        filter_json = {
                "current": {
                "text": [
                "All"
                ],
                "value": [
                "$__all"
                ]
                },
                "datasource": {
                "type": "postgres",
                "uid": f"{self.datasource_uid}"
                },
                "includeAll": True,
                "multi": True,
                "name": filter_name,
                "options": [],
                "query": filter_sql,
                "refresh": 1,   # refresh everytime when dashboard is loaded
                "type": "query"
            }

        return filter_json
    
    def generate_filterSQL(self, filter_name: str, filters_table: str) -> str:
        """Generate a template SQL command based on the given filter name.
        """
        # check filter type:
        if filter_name == "shipping_status":
            filter_sql = f"""
            SELECT DISTINCT 
            CASE WHEN shipped_datetime IS NULL THEN 'not shipped' ELSE 'shipped' END AS shipping_status 
            FROM {filters_table}
            ORDER BY shipping_status
            """
        elif filter_name == "wirebond_status":
            filter_sql = f"""
            SELECT DISTINCT 
            CASE WHEN wb_front IS NULL THEN 'not front bonded' ELSE 'front bonded' END AS wirebond_status 
            FROM {filters_table}
            ORDER BY wirebond_status
            """
        elif filter_name == "iv_grade":
            filter_sql = f"""
            SELECT DISTINCT iv_grade::text FROM module_qc_summary
            UNION
            SELECT 'NULL'
            ORDER BY iv_grade
            """
        else:
            filter_sql = f"""
            SELECT DISTINCT 
                COALESCE({filter_name}::text, 'NULL') AS {filter_name} 
            FROM {filters_table} 
            ORDER BY {filter_name}
            """

        return filter_sql
    
    def build_template_list(self, filters: dict, exist_filter: set) -> list:
        """Build all filters based on the given filter_dict.
        """
        filters_table_list = list(filters.keys())
        template_list = []

        for filters_table in filters_table_list:
            for elem in filters[filters_table]:
                if elem in exist_filter:
                    continue    # filter exists
                elif elem in TIME_COLUMNS:
                    continue    # filter not used in dashboard
            
                exist_filter.add(elem)

                # generate the filter's json
                filter_sql = self.generate_filterSQL(elem, filters_table)
                filter_json = self.generate_filter(elem, filter_sql)
                template_list.append(filter_json)
        
        return template_list
    
    def build_iv_curve_filters(self, exist_filter: set) -> list:
        """Build all filters for IV curve plot.
        """
        template_list = []

        if not exist_filter:
            temp_arg = [
                        {
                "name": "N_MODULE_SHOW",
                "type": "textbox",
                "label": "Number of Modules to Show",
                "hide": 0,
                "query": "",
                "current": {
                    "text": "15",
                    "value": "15"
                },
                "options": [],
                "refresh": 0
                }
            ]
            template_list.extend(temp_arg)
            exist_filter.add("N_MODULE_SHOW")

        return template_list

# ============================================================
# === IV Curve Builder =======================================
# ============================================================

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

        selected_modules AS (
        SELECT 
            module_info.module_name
        FROM module_info
        LEFT JOIN latest_qc_summary ON module_info.module_name = latest_qc_summary.module_name
        WHERE {module_where_arg}
            AND {iv_where_arg}
            AND $__timeFilter(test_iv) 
            AND test_iv IS NOT NULL
        ORDER BY module_info.module_no DESC
        LIMIT {N_MODULE_SHOW}
        ),

        filtered_iv AS (
        SELECT *,
            meas_i[array_length(meas_i, 1)] AS i_last
        FROM module_iv_test
        WHERE
            module_name IN (SELECT module_name FROM selected_modules)
            AND meas_v IS NOT NULL AND meas_i IS NOT NULL
            AND {temp_condition}
            AND {rel_hum_condition}
            AND temp_c ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND rel_hum ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
            AND (status_desc = 'Completely Encapsulated' OR status_desc = 'Frontside Encapsulated')
            AND array_length(meas_v, 1) = array_length(meas_i, 1)
        ),

        best_per_module AS (
        SELECT DISTINCT ON (filtered_iv.module_name) *
        FROM filtered_iv
        ORDER BY filtered_iv.module_name, i_last ASC
        ),

        unnested AS (
        SELECT 
            module_name,
            v,
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
                "show": "lines",
                "pointSize": {
                "fixed": 5
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
                "keepFields": False
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
            "mode": "single",
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


# ============================================================
# === Components Look-up Form Builder ========================
# ============================================================

class ComponentsLookUpFormBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("Components Look-up Form")
        self.hxb_name = "UPPER('${hxb_name}')"
        self.bp_name = "UPPER('${bp_name}')"
        self.sen_name = "UPPER('${sen_name}')"
        self.proto_name = "UPPER('${proto_name}')"
        self.module_name = "UPPER('${module_name}')"

        self.module_info_sql = f"""
        WITH selected_module_inspect AS (
            SELECT DISTINCT ON (module_name) *
            FROM module_inspect    
            ORDER BY module_name, module_row_no DESC
        )
        SELECT
            module_info.*,
            selected_module_inspect.flatness,
            selected_module_inspect.avg_thickness,
            selected_module_inspect.x_offset_mu,
            selected_module_inspect.y_offset_mu,
            selected_module_inspect.ang_offset_deg
        FROM module_info
        LEFT JOIN selected_module_inspect ON module_info.module_name = selected_module_inspect.module_name
        WHERE  (hxb_name = {self.hxb_name})
            OR (bp_name = {self.bp_name})
            OR (sen_name = {self.sen_name})
            OR (proto_name = {self.proto_name})
            OR (module_info.module_name = {self.module_name})
        """

        self.proto_info_sql = f"""
        WITH selected_proto_inspect AS (
            SELECT DISTINCT ON (proto_name) *
            FROM proto_inspect
            ORDER BY proto_name, proto_row_no DESC
        )
        SELECT    
            proto_assembly.*,
            selected_proto_inspect.flatness,
            selected_proto_inspect.avg_thickness,
            selected_proto_inspect.x_offset_mu,
            selected_proto_inspect.y_offset_mu,
            selected_proto_inspect.ang_offset_deg
        FROM proto_assembly 
        LEFT JOIN module_info ON module_info.proto_name = proto_assembly.proto_name
        LEFT JOIN selected_proto_inspect ON module_info.proto_name = selected_proto_inspect.proto_name
        WHERE  (proto_assembly.bp_name = {self.bp_name})
            OR (proto_assembly.sen_name = {self.sen_name})
            OR (proto_assembly.proto_name = {self.proto_name})
            OR (module_info.module_name = {self.module_name})
            OR (module_info.hxb_name = {self.hxb_name})
        """

        self.sensor_info_sql = f"""
        SELECT sensor.*
        FROM sensor
        LEFT JOIN module_info ON module_info.sen_name = sensor.sen_name
        LEFT JOIN proto_assembly ON proto_assembly.sen_name = sensor.sen_name
        WHERE  (sensor.sen_name = {self.sen_name})    
            OR (proto_assembly.proto_name = {self.proto_name})
            OR (module_name = {self.module_name})
            OR (module_info.bp_name = {self.bp_name})
            OR (module_info.hxb_name = {self.hxb_name})
        """

        self.bp_info_sql = f"""
        WITH selected_bp AS (
            SELECT DISTINCT ON (bp_name) *
            FROM baseplate
            ORDER BY bp_name, bp_no DESC
        ),
            selected_bp_inspect AS (
                SELECT DISTINCT ON (bp_name) *
                FROM bp_inspect
                ORDER BY bp_name, bp_row_no DESC
        )
        SELECT
            selected_bp.*,
            selected_bp_inspect.flatness,
            selected_bp_inspect.thickness
        FROM selected_bp
        LEFT JOIN module_info ON module_info.bp_name = selected_bp.bp_name
        LEFT JOIN proto_assembly ON proto_assembly.bp_name = selected_bp.bp_name
        LEFT JOIN selected_bp_inspect ON selected_bp_inspect.bp_name = selected_bp.bp_name
        WHERE  (selected_bp.bp_name = {self.bp_name})
            OR (proto_assembly.proto_name = {self.proto_name})
            OR (module_info.module_name = {self.module_name})
            OR (module_info.hxb_name = {self.hxb_name})
            OR (module_info.sen_name = {self.sen_name})
        """
    
        self.hxb_info_sql = f"""
        WITH selected_hxb_inspect AS (
            SELECT DISTINCT ON (hxb_name) *
            FROM hxb_inspect
            ORDER BY hxb_name, hxb_row_no DESC
        )
        SELECT
            hexaboard.*,
            selected_hxb_inspect.flatness,
            selected_hxb_inspect.thickness
        FROM hexaboard
        LEFT JOIN module_info ON module_info.hxb_name = hexaboard.hxb_name
        LEFT JOIN selected_hxb_inspect ON selected_hxb_inspect.hxb_name = hexaboard.hxb_name
        WHERE  (hexaboard.hxb_name = {self.hxb_name})
            OR (module_info.module_name = {self.module_name})
            OR (module_info.proto_name = {self.proto_name})
            OR (module_info.sen_name = {self.sen_name})
            OR (module_info.bp_name = {self.bp_name})
        """

        self.module_pedestal_sql = f"""
        SELECT 
            module_pedestal_test.mod_pedtest_no,
            module_pedestal_test.module_no,
            module_pedestal_test.module_name,
            module_pedestal_test.bias_vol,
            module_pedestal_test.count_bad_cells,
            module_pedestal_test.list_dead_cells,
            module_pedestal_test.list_noisy_cells,
            module_pedestal_test.list_disconnected_cells,
            module_pedestal_test.comment,
            module_pedestal_test.rel_hum,
            module_pedestal_test.temp_c,
            module_pedestal_test.date_test,
            module_pedestal_test.time_test AT TIME ZONE '{TIME_ZONE}' AS time_test,
            module_pedestal_test.inspector,
            module_pedestal_test.trim_bias_voltage,
            module_pedestal_test.status_desc,
            module_pedestal_test.run_no,
            module_pedestal_test.xml_gen_datetime,
            module_pedestal_test.xml_upload_success,
            module_pedestal_test.meas_leakage_current,
            module_pedestal_test.inverse_sqrt_n,
            module_pedestal_test.pedestal_config_json
        FROM module_pedestal_test
        LEFT JOIN module_info ON module_info.module_name = module_pedestal_test.module_name
        WHERE  (module_info.hxb_name = {self.hxb_name})
            OR (module_info.module_name = {self.module_name})
            OR (module_info.proto_name = {self.proto_name})
            OR (module_info.sen_name = {self.sen_name})
            OR (module_info.bp_name = {self.bp_name})
        ORDER BY module_pedestal_test.mod_pedtest_no DESC
        """

        self.hxb_pedestal_sql = f"""
        SELECT
            hxb_pedestal_test.hxb_pedtest_no,
            hxb_pedestal_test.hxb_no,
            hxb_pedestal_test.hxb_name,
            hxb_pedestal_test.count_bad_cells,
            hxb_pedestal_test.list_dead_cells,
            hxb_pedestal_test.list_noisy_cells,
            hxb_pedestal_test.comment,
            hxb_pedestal_test.rel_hum,
            hxb_pedestal_test.temp_c,
            hxb_pedestal_test.date_test,
            hxb_pedestal_test.time_test AT TIME ZONE '{TIME_ZONE}' AS time_test,
            hxb_pedestal_test.inspector,
            hxb_pedestal_test.trim_bias_voltage,
            hxb_pedestal_test.xml_gen_datetime,
            hxb_pedestal_test.xml_upload_success,
            hxb_pedestal_test.status_desc,
            hxb_pedestal_test.inverse_sqrt_n,
            hxb_pedestal_test.pedestal_config_json
        FROM hxb_pedestal_test
        LEFT JOIN module_info ON module_info.hxb_name = hxb_pedestal_test.hxb_name
        WHERE  (hxb_pedestal_test.hxb_name = {self.hxb_name})
            OR (module_info.module_name = {self.module_name})
            OR (module_info.proto_name = {self.proto_name})
            OR (module_info.sen_name = {self.sen_name})
            OR (module_info.bp_name = {self.bp_name})
        ORDER BY hxb_pedestal_test.hxb_pedtest_no DESC
        """

        self.module_iv_curve_sql = rf"""
        WITH filtered_iv AS (
            SELECT DISTINCT ON (module_iv_test.status) module_iv_test.*,
                meas_i[array_length(meas_i, 1)] AS i_last
            FROM module_iv_test
            JOIN module_info ON module_iv_test.module_name = module_info.module_name
            WHERE (module_info.module_name = {self.module_name}
                OR module_info.proto_name = {self.proto_name}
                OR module_info.sen_name = {self.sen_name}
                OR module_info.bp_name = {self.bp_name}
                OR module_info.hxb_name = {self.hxb_name})
                AND (meas_v IS NOT NULL AND meas_i IS NOT NULL)
                AND temp_c ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
                AND rel_hum ~ '^[-+]?[0-9]+(\.[0-9]+)?$'
                AND (temp_c::float >= 10 AND temp_c::float <= 30)
                AND (rel_hum::float <= 12)
            ORDER BY module_iv_test.status, i_last ASC
        ),
            unnested AS (
                SELECT
                    status_desc,
                    v,
                    i
                FROM filtered_iv,
                UNNEST(meas_v, meas_i) AS t(v, i)
        )
        SELECT *
        FROM unnested;
        """

        self.all_module_iv_curve_sql = rf"""
        WITH filtered_iv AS (
            SELECT module_iv_test.*
            FROM module_iv_test
            JOIN module_info ON module_iv_test.module_name = module_info.module_name
            WHERE (module_info.module_name = {self.module_name}
                OR module_info.proto_name = {self.proto_name}
                OR module_info.sen_name = {self.sen_name}
                OR module_info.bp_name = {self.bp_name}
                OR module_info.hxb_name = {self.hxb_name})
                AND (meas_v IS NOT NULL AND meas_i IS NOT NULL)
        ),
            unnested AS (
                SELECT
                    mod_ivtest_no || ' / ' || status_desc || ' / ' || temp_c || '˚C / ' || rel_hum || '%RH' AS status_desc,
                    v,
                    i
                FROM filtered_iv,
                UNNEST(meas_v, meas_i) AS t(v, i)
        )
        SELECT *
        FROM unnested;
        """

        self.mean_hexmap_sql = f"""
        SELECT DISTINCT ON (module_pedestal_plots.module_name) encode(adc_mean_hexmap, 'base64') AS noise_channel_base64
        FROM module_pedestal_plots
        JOIN module_info ON module_pedestal_plots.module_name = module_info.module_name
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        ORDER BY module_pedestal_plots.module_name, module_pedestal_plots.mod_plottest_no DESC
        """

        self.std_hexmap_sql = f"""
        SELECT DISTINCT ON (module_pedestal_plots.module_name) encode(adc_std_hexmap, 'base64') AS noise_channel_base64
        FROM module_pedestal_plots
        JOIN module_info ON module_pedestal_plots.module_name = module_info.module_name
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        ORDER BY module_pedestal_plots.module_name, module_pedestal_plots.mod_plottest_no DESC
        """

        self.wirebond_info_sql = f"""
        WITH selected_front_wirebond AS (
            SELECT DISTINCT ON (module_name) *
            FROM front_wirebond
            ORDER BY module_name, frwirebond_no DESC
        )
        SELECT
            selected_front_wirebond.module_name,
            selected_front_wirebond.list_grounded_cells,
            selected_front_wirebond.list_unbonded_cells,
            selected_front_wirebond.bond_count_for_cell,
            selected_front_wirebond.bond_type,
            selected_front_wirebond.comment
        FROM selected_front_wirebond
        JOIN module_info ON selected_front_wirebond.module_name = module_info.module_name
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        """

    def generate_dashboard_json(self):
        """Generate the dashboard JSON for the components look-up form.
        """
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
                "h": 4,
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
                "showHeader": True
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
                "rawSql": self.module_info_sql,
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
                "h": 4,
                "w": 24,
                "x": 0,
                "y": 4
            },
            "id": 3,
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
                "showHeader": True
            },
            "pluginVersion": "12.0.1",
            "targets": [
                {
                "editorMode": "code",
                "format": "table",
                "rawQuery": True,
                "rawSql": self.proto_info_sql,
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
            "title": "Proto Info",
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
                "h": 4,
                "w": 24,
                "x": 0,
                "y": 8
            },
            "id": 4,
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
                "showHeader": True
            },
            "pluginVersion": "12.0.1",
            "targets": [
                {
                "editorMode": "code",
                "format": "table",
                "rawQuery": True,
                "rawSql": self.sensor_info_sql,
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
            "title": "Sensor Info",
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
                "h": 4,
                "w": 24,
                "x": 0,
                "y": 12
            },
            "id": 5,
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
                "showHeader": True
            },
            "pluginVersion": "12.0.1",
            "targets": [
                {
                "editorMode": "code",
                "format": "table",
                "rawQuery": True,
                "rawSql": self.bp_info_sql,
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
            "title": "Baseplate Info",
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
                "h": 4,
                "w": 24,
                "x": 0,
                "y": 16
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
                "showHeader": True
            },
            "pluginVersion": "12.0.1",
            "targets": [
                {
                "editorMode": "code",
                "format": "table",
                "rawQuery": True,
                "rawSql": self.hxb_info_sql,
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
            "title": "Hexaboard Info",
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
                "h": 9,
                "w": 24,
                "x": 0,
                "y": 20
            },
            "id": 6,
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
                "showHeader": True
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
                "rawSql": self.module_pedestal_sql,
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
            "title": "Module Pedestal Test",
            "type": "table",
            "links":[
                {
                "title": "All Hexmap Plots",
                "url": f"{GF_URL}/d/hexmap-plots",
                "targetBlank": True
                }
            ]
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
                "h": 9,
                "w": 24,
                "x": 0,
                "y": 29
            },
            "id": 7,
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
                "showHeader": True
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
                "rawSql": self.hxb_pedestal_sql,
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
            "title": "Hexaboard Pedestal Test",
            "type": "table",
            "links":[
                {
                "title": "All Hexmap Plots",
                "url": f"{GF_URL}/d/hexmap-plots",
                "targetBlank": True
                }
            ]
            },
            {
            "type": "xychart",
            "title": "All Module IV Curves [Log Scale]",
            "gridPos": {
                "x": 0,
                "y": 38,
                "h": 11,
                "w": 24
            },
            "fieldConfig": {
                "defaults": {
                "custom": {
                    "show": "lines",
                    "pointSize": {
                    "fixed": 5
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
                "overrides": [
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
                        "value": 0.001
                    },
                    {
                        "id": "min",
                        "value": 1e-9
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
            },
            "transformations": [
                {
                "id": "partitionByValues",
                "options": {
                    "keepFields": False,
                    "fields": [
                    "status_desc"
                    ]
                }
                }
            ],
            "pluginVersion": "12.0.0",
            "targets": [
                {
                "refId": "A",
                "format": "table",
                "rawSql": self.all_module_iv_curve_sql,
                "sql": {
                    "columns": [
                    {
                        "type": "function",
                        "parameters": []
                    }
                    ],
                    "groupBy": [
                    {
                        "type": "groupBy",
                        "property": {
                        "type": "string"
                        }
                    }
                    ],
                    "limit": 50
                },
                "rawQuery": True
                }
            ],
            "datasource": {
                "uid": f"{self.datasource_uid}",
                "type": "grafana-postgresql-datasource"
            },
            "options": {
                "mapping": "auto",
                "series": [
                {}
                ],
                "tooltip": {
                "mode": "single",
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
                "h": 4,
                "w": 24,
                "x": 0,
                "y": 49
            },
            "id": 11,
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
                "showHeader": True
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
                "rawSql": self.wirebond_info_sql,
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
            "title": "Wirebond Info",
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
                "text": "",
                "value": ""
                },
                "label": "Baseplate serial",
                "name": "bp_name",
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
                "label": "Hexaboard serial",
                "name": "hxb_name",
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
                "label": "Proto serial",
                "name": "proto_name",
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
                "label": "Sensor serial",
                "name": "sen_name",
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
                "label": "Module serial",
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
                "name": "mean_hex_map",
                "label": "Mean Hex Map",
                "type": "query",
                "hide": 2,
                "refresh": 1,
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "query": self.mean_hexmap_sql,
                "current": {
                "text": "",
                "value": ""
                }
            },
            {
                "name": "std_hex_map",
                "label": "Std Hex Map",
                "type": "query",
                "hide": 2,
                "refresh": 1,
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "query": self.std_hexmap_sql,
                "current": {
                "text": "",
                "value": ""
                }
            }    
            ]
        },
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "browser",
        "title": "Components Look-up Form",
        "uid": f"{self.dashboard_uid}",
        "version": 1
        }

        return dashboard_json

class HexmapPlotsBuilder:
    def __init__(self, datasource_uid):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("Hexmap Plots")

        self.mean_hex_map_base64 = "${mean_hex_map}"
        self.std_hex_map_base64 = "${std_hex_map}"

        self.mean_hexmap_md = f'<img src=\"data:image/png;base64,{self.mean_hex_map_base64}" style="width: auto; height: auto;"/>'
        self.std_hexmap_md = f'<img src=\"data:image/png;base64,{self.std_hex_map_base64}" style="width: auto; height: auto;"/>'

    
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
                    "definition": "SELECT status_desc\nFROM module_pedestal_plots\nGROUP BY status_desc\nORDER BY COUNT(*) DESC;",
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
                    "definition": "SELECT encode(adc_mean_hexmap, 'base64') AS hex_img\nFROM module_pedestal_plots\nWHERE module_name = '${module_name}'\nAND ('All' = ANY(ARRAY[${status_desc}]) OR \n                (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR \n                module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))\nORDER BY mod_plottest_no DESC;",
                    "hide": 2,
                    "includeAll": True,
                    "multi": True,
                    "name": "mean_hex_map",
                    "options": [],
                    "query": "SELECT encode(adc_mean_hexmap, 'base64') AS hex_img\nFROM module_pedestal_plots\nWHERE module_name = '${module_name}'\nAND ('All' = ANY(ARRAY[${status_desc}]) OR \n                (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR \n                module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))\nORDER BY mod_plottest_no DESC;",
                    "refresh": 1,
                    "regex": "",
                    "type": "query"
                },
                {
                    "current": {
                    "text": "All",
                    "value": "$__all"
                    },
                    "definition": "SELECT encode(adc_std_hexmap, 'base64') AS hex_img\nFROM module_pedestal_plots\nWHERE module_name = '${module_name}'\n             AND ('All' = ANY(ARRAY[${status_desc}]) OR \n                (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR \n                module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))\nORDER BY mod_plottest_no DESC;",
                    "description": "",
                    "hide": 2,
                    "includeAll": True,
                    "multi": True,
                    "name": "std_hex_map",
                    "options": [],
                    "query": "SELECT encode(adc_std_hexmap, 'base64') AS hex_img\nFROM module_pedestal_plots\nWHERE module_name = '${module_name}'\n             AND ('All' = ANY(ARRAY[${status_desc}]) OR \n                (module_pedestal_plots.status_desc IS NULL AND 'NULL' = ANY(ARRAY[${status_desc}])) OR \n                module_pedestal_plots.status_desc::text = ANY(ARRAY[${status_desc}]))\nORDER BY mod_plottest_no DESC;",
                    "refresh": 1,
                    "regex": "",
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