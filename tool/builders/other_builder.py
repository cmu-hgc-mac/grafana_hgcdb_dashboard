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
        # elif filter_name in QC_GRADE:
        #     filter_sql = f"""
        #     SELECT DISTINCT {filter_name}::text FROM module_qc_summary
        #     UNION
        #     SELECT 'NULL'
        #     ORDER BY {filter_name}
            # """
        else:
            filter_sql = f"""
            SELECT DISTINCT {filter_name}::text FROM {filters_table} 
            UNION
            SELECT 'NULL'
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
# === Input Builder ==========================================
# ============================================================

class InputBuilder:
    def __init__(self):
        pass

    def generate_input(self, input_name: str) -> dict:
        """Generate a template json based on the given input_name.
        """
        input_json = {
                "current": {
                "text": "",
                "value": ""
                },
                "label": input_name,
                "name": input_name,
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
        
        return input_json
    
    def build_template_list(self, inputs: dict, exist_filter: set) -> list:
        """Build all filters based on the given filter_dict.
        """
        template_list = []

        for table, elems in inputs.items():
            for elem in elems:
                if elem in exist_filter:
                    continue    # filter exists
                elif elem in TIME_COLUMNS:
                    continue    # filter not used in dashboard
            
                exist_filter.add(elem)

                # generate the filter's json
                input_json = self.generate_input(elem)
                template_list.append(input_json)
        
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
    """I know it looks gross, can't help sorry."""

    def __init__(self, datasource_uid):
        ## === UIDs ===
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("Components Look-up Form")

        ## == Arguments ==
        self.hxb_name = "UPPER(REPLACE('${hxb_name}', '-', ''))"
        self.bp_name = "UPPER('${bp_name}')"
        self.sen_name = "UPPER('${sen_name}')"
        self.proto_name = "UPPER('${proto_name}')"
        self.module_name = "UPPER(REPLACE('${module_name}', '-', ''))"
        self.mean_hex_map_base64 = "${mean_hex_map}"
        self.std_hex_map_base64 = "${std_hex_map}"

        ## === SQL ===
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
        WITH selected_bp_inspect AS (
            SELECT DISTINCT ON (bp_name) *
            FROM bp_inspect
            ORDER BY bp_name, bp_row_no DESC
        )
        SELECT
            baseplate.*,
            selected_bp_inspect.flatness,
            selected_bp_inspect.thickness
        FROM baseplate
        LEFT JOIN module_info ON module_info.bp_name = baseplate.bp_name
        LEFT JOIN proto_assembly ON proto_assembly.bp_name = baseplate.bp_name
        LEFT JOIN selected_bp_inspect ON selected_bp_inspect.bp_name = baseplate.bp_name
        WHERE  (baseplate.bp_name = {self.bp_name})
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
            module_pedestal_test.date_test::text,
            module_pedestal_test.time_test::text,
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
            hxb_pedestal_test.date_test::text,
            hxb_pedestal_test.time_test::text,
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
            ORDER BY mod_ivtest_no ASC
        ),
            unnested AS (
                SELECT
                    mod_ivtest_no || ' / ' || status_desc || ' / ' || temp_c || '˚C / ' || rel_hum || '%RH' AS status_desc,
                    ABS(v) as v,
                    i
                FROM filtered_iv,
                UNNEST(meas_v, meas_i) AS t(v, i)
        )

        SELECT *
        FROM unnested;
        """

        self.wirebond_info_sql = f"""
        WITH selected_front_wirebond AS (
            SELECT DISTINCT ON (module_name) *
            FROM front_wirebond
            ORDER BY module_name, frwirebond_no DESC
        )
        SELECT
            selected_front_wirebond.frwirebond_no,
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
        
        self.bond_pull_info_sql = f"""
        SELECT
            bond_pull_test.pulltest_no,
            bond_pull_test.module_name,
            bond_pull_test.avg_pull_strg_g,
            bond_pull_test.std_pull_strg_g,
            bond_pull_test.date_bond,
            bond_pull_test.comment
        FROM bond_pull_test
        JOIN module_info ON bond_pull_test.module_name = module_info.module_name
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        """

        self.module_module_name_sql = f"""
        SELECT module_name
        FROM module_info
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        """

        self.module_hex_name_sql = f"""
        SELECT hxb_name
        FROM module_info
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        """

        self.qc_data_list = self.generate_qc_data_list()

        self.mean_hexmap_md = f'<img src=\"data:image/png;base64,{self.mean_hex_map_base64}" style="width: auto; height: auto;"/>'
        self.std_hexmap_md = f'<img src=\"data:image/png;base64,{self.std_hex_map_base64}" style="width: auto; height: auto;"/>'

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

        self.encap_info_sql = f"""
        WITH encap AS (
            SELECT DISTINCT ON (front_encap.module_name)
                'front_encap' AS source,
                front_encap.module_name,
                front_encap.cure_temp_c,
                front_encap.epoxy_batch,
                front_encap.temp_c,
                front_encap.date_encap::text,
                front_encap.time_encap::text,
                front_encap.technician,
                front_encap.comment,
                front_encap.cure_start,
                front_encap.cure_end
            FROM front_encap
            JOIN module_info ON front_encap.module_name = module_info.module_name
            WHERE (module_info.module_name = {self.module_name}
                OR module_info.proto_name = {self.proto_name}
                OR module_info.sen_name = {self.sen_name}
                OR module_info.bp_name = {self.bp_name}
                OR module_info.hxb_name = {self.hxb_name})
        
            UNION ALL

            SELECT DISTINCT ON (back_encap.module_name)
                'back_encap' AS source,
                back_encap.module_name,
                back_encap.cure_temp_c,
                back_encap.epoxy_batch,
                back_encap.temp_c,
                back_encap.date_encap::text,
                back_encap.time_encap::text,
                back_encap.technician,
                back_encap.comment,
                back_encap.cure_start,
                back_encap.cure_end
            FROM back_encap
            JOIN module_info ON back_encap.module_name = module_info.module_name
            WHERE (module_info.module_name = {self.module_name}
                OR module_info.proto_name = {self.proto_name}
                OR module_info.sen_name = {self.sen_name}
                OR module_info.bp_name = {self.bp_name}
                OR module_info.hxb_name = {self.hxb_name})
            )

        SELECT *
        FROM encap
        """


    ######################################
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
    # Panel: Module Info
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
    # Panel: Module QC Summary
            {
            "type": "text",
            "title": "Module QC Summary",
            "gridPos": {
                "x": 0,
                "y": 4,
                "h": 24,
                "w": 24
            },
            "fieldConfig": {
                "defaults": {},
                "overrides": []
            },
            "pluginVersion": "12.0.0",
            "options": {
                "mode": "markdown",
                "code": {
                "language": "plaintext",
                "showLineNumbers": False,
                "showMiniMap": False
                },
                "content": "## Basic Info\n\n- **module_name**: ${module_module_name}  \n- **final_grade**: ${final_grade}\n  - **iv_grade**: ${iv_grade}\n  - **readout_grade**: ${readout_grade}\n  - **module_grade**: ${module_grade}\n  - **proto_grade**: ${proto_grade}\n- **comments_all**:\n  ```  \n  ${comments_all}\n  ```\n\n---\n\n## Measurements\n\n|              | flatness (mm)        | avg_thickness (mm)     | max_thickness (mm)    | x_offset (μm)        | y_offset (μm)      | ang_offset  (deg)     |\n|--------------|------------------|----------------------|----------------------|------------------|------------------|---------------------|\n| **Proto**| ${proto_flatness} | ${proto_avg_thickness} | ${proto_max_thickness} | ${proto_x_offset} | ${proto_y_offset} | ${proto_ang_offset} |\n| **Module**   | ${module_flatness} | ${module_avg_thickness} | ${module_max_thickness} | ${module_x_offset} | ${module_y_offset} | ${module_ang_offset} |\n\n---\n\n## Cell Info\n\n- **list_cells_unbonded**: ${list_cells_unbonded}  \n- **list_cells_grounded**: ${list_cells_grounded}  \n- **list_noisy_cells**: ${list_noisy_cells}  \n- **list_dead_cells**: ${list_dead_cells}  \n- **count_bad_cells**: ${count_bad_cells}  \n\n---\n\n## IV Info\n\n- **i_ratio_ref_b_over_a**: ${i_ratio_ref_b_over_a}\n- **ref_volt_a**: ${ref_volt_a} V\n- **ref_volt_b**: ${ref_volt_b} V\n- **i_at_ref_a**: ${i_at_ref_a} A"
            }
            },
    # Panel: Proto Info
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
                "y": 79
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
    # Panel: Sensor Info
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
                "y": 83
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
    # Panel: Baseplate Info
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
                "y": 87
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
    # Panel: Hexaboard Info
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
                "y": 91
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
    # Panel: Module Pedestal Test
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
                "y": 28
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
                "url": f"{GF_URL}/d/hexmap-plots?var-module_name="+"${module_module_name}",
                "targetBlank": True
                }
            ]
            },
    # Panel: Hexaboard Pedestal Test
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
                "y": 37
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
                "url": f"{GF_URL}/d/hexmap-plots?var-module_name="+"${module_hex_name}",
                "targetBlank": True
                }
            ]
            },
    # Panel: All Module IV Curves [Log Scale]
            {
            "type": "xychart",
            "title": "All Module IV Curves [Log Scale]",
            "gridPos": {
                "x": 0,
                "y": 46,
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
    # Panel: Latest Mean Hexmap
            {
            "fieldConfig": {
                "defaults": {},
                "overrides": []
            },
            "gridPos": {
                "h": 18,
                "w": 12,
                "x": 0,
                "y": 57
            },
            "id": 9,
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
            "title": "Pedestal Hexmap",
            "type": "text",
            "links":[
                {
                "title": "All Hexmap Plots",
                "url": f"{GF_URL}/d/hexmap-plots?var-module_name="+"${module_module_name}",
                "targetBlank": True
                }
            ]
            },
    # Panel: Latest Noisy Hexmap
            {
            "fieldConfig": {
                "defaults": {},
                "overrides": []
            },
            "gridPos": {
                "h": 18,
                "w": 12,
                "x": 12,
                "y": 57
            },
            "id": 10,
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
            "title": "Noise Hexmap",
            "type": "text",
            "links":[
                {
                "title": "All Hexmap Plots",
                "url": f"{GF_URL}/d/hexmap-plots?var-module_name="+"${module_module_name}",
                "targetBlank": True
                }
            ]
            },
    # Panel: Wirebond Info
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
                "y": 75
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
            },
    # Panel: Bond Pull Info
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
                "y": 95
            },
            "id": 12,
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
                "rawSql": self.bond_pull_info_sql,
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
            "title": "Bond Pull Info",
            "type": "table"
            },
    # Panel: Encap Info
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
                "h": 5,
                "w": 24,
                "x": 0,
                "y": 99
            },
            "id": 13,
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
                "rawSql": self.encap_info_sql,
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
            "title": "Encap Info",
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
                "name": "module_hex_name",
                "label": "Related Hex Name",
                "type": "query",
                "hide": 2,
                "refresh": 1,
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "query": self.module_hex_name_sql,
                "current": {
                "text": "",
                "value": ""
                }
            },
            {
                "name": "module_module_name",
                "label": "Related module Name",
                "type": "query",
                "hide": 2,
                "refresh": 1,
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "query": self.module_module_name_sql,
                "current": {
                "text": "",
                "value": ""
                }
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
            ] + self.qc_data_list
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

    def generate_qc_data_list(self):
        qc_data_list = []

        for qc_data in QC_COLUMNS:
            raw_sql = f"""
            SELECT 
                CASE 
                    WHEN {qc_data}::text = '1e+10' THEN 'null'
                    ELSE {qc_data}::text 
                END AS {qc_data}
            FROM module_qc_summary
            JOIN module_info ON module_qc_summary.module_name = module_info.module_name
            WHERE (module_info.module_name = {self.module_name}
                OR module_info.proto_name = {self.proto_name}
                OR module_info.sen_name = {self.sen_name}
                OR module_info.bp_name = {self.bp_name}
                OR module_info.hxb_name = {self.hxb_name})
            ORDER BY mod_qc_no DESC
            LIMIT 1;
            """

            arg = {
                "name": f"{qc_data}",
                "label": f"{qc_data}",
                "type": "query",
                "hide": 2,
                "refresh": 1,
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "query": raw_sql,
                "current": {
                "text": "",
                "value": ""
                }
            }

            qc_data_list.append(arg)

        return qc_data_list


# ============================================================
# === Hexmap Plots Builder ===================================
# ============================================================

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


# ============================================================
# === Offset Plots Builder ===================================
# ============================================================

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
                "fieldConfig": {
                    "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": True,
                        "axisSoftMin": -150,
                        "axisSoftMax": 150,
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
                    "mappings": [
                        {
                        "options": {
                            "100": {
                            "color": "dark-red",
                            "index": 0
                            }
                        },
                        "type": "value"
                        }
                    ],
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
                    "h": 12,
                    "w": 12,
                    "x": 0,
                    "y": 0
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
                    }
                ],
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
                        "axisSoftMin": -150,
                        "axisSoftMax": 150,
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
                    "mappings": [
                        {
                        "options": {
                            "100": {
                            "color": "dark-red",
                            "index": 0
                            }
                        },
                        "type": "value"
                        }
                    ],
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
                    "h": 12,
                    "w": 12,
                    "x": 12,
                    "y": 0
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
                    }
                ],
                "title": "Proto-Module Offset",
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


# ============================================================
# === General Info Builder ===================================
# ============================================================

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
                    "rawSql": "WITH\ndaily_module AS (\n    SELECT\n        DATE(module_info.assembled AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS count\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         module_info.bp_material::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           module_info.resolution::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           module_info.roc_version::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           module_info.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           module_info.geometry::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(module_info.assembled)\n      AND module_info.assembled IS NOT NULL\n    GROUP BY 1\n),\n\ndaily_proto AS (\n    SELECT\n        DATE(proto_assembly.ass_run_date AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS count\n    FROM proto_assembly\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END)::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END)::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(proto_assembly.ass_run_date)\n      AND proto_assembly.ass_run_date IS NOT NULL\n    GROUP BY 1\n)\n\nSELECT\n    (COALESCE(m.local_date, p.local_date)::timestamp + interval '12 hour') AS \"time\",\n    m.count AS module_assembly,\n    p.count AS proto_assembly\nFROM daily_module m\nFULL OUTER JOIN daily_proto p\n    ON m.local_date = p.local_date\nORDER BY \"time\";",
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
                    "rawSql": "WITH\ndaily_module AS (\n    SELECT\n        DATE(module_info.assembled AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS cnt\n    FROM module_info\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (module_info.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         module_info.bp_material::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (module_info.resolution IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           module_info.resolution::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (module_info.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           module_info.roc_version::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (module_info.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           module_info.sen_thickness::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (module_info.geometry IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           module_info.geometry::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(module_info.assembled)\n      AND module_info.assembled IS NOT NULL\n    GROUP BY 1\n),\n\ncum_module AS (\n    SELECT\n        local_date,\n        SUM(cnt) OVER (\n            ORDER BY local_date\n            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n        ) AS module_total\n    FROM daily_module\n),\n\ndaily_proto AS (\n    SELECT\n        DATE(proto_assembly.ass_run_date AT TIME ZONE 'America/New_York') AS local_date,\n        COUNT(*)::bigint AS cnt\n    FROM proto_assembly\n    WHERE\n        ('All' = ANY(ARRAY[${bp_material}]) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END IS NULL AND 'NULL' = ANY(ARRAY[${bp_material}])) OR\n         (CASE substring(proto_assembly.proto_name from 8 for 1)\n              WHEN 'W' THEN 'CuW'\n              WHEN 'T' THEN 'Titanium'\n              WHEN 'C' THEN 'Carbon Fiber'\n              WHEN 'P' THEN 'PCB'\n              WHEN 'X' THEN ''\n              ELSE NULL\n          END)::text = ANY(ARRAY[${bp_material}]))\n\n      AND ('All' = ANY(ARRAY[${resolution}]) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${resolution}])) OR\n           (CASE substring(proto_assembly.proto_name from 5 for 1)\n                WHEN 'L' THEN 'LD'\n                WHEN 'H' THEN 'HD'\n                WHEN '0' THEN ''\n                ELSE NULL\n            END)::text = ANY(ARRAY[${resolution}]))\n\n      AND ('All' = ANY(ARRAY[${roc_version}]) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${roc_version}])) OR\n           (CASE substring(proto_assembly.proto_name from 9 for 1)\n                WHEN 'X' THEN 'preseries'\n                WHEN '2' THEN 'HGCROCV3b-2'\n                WHEN '4' THEN 'HGCROCV3b-4'\n                WHEN 'B' THEN 'HGCROCV3b-3'\n                WHEN 'C' THEN 'HGCROCV3c'\n                WHEN 'D' THEN 'HGCROCV3d'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${roc_version}]))\n\n      AND ('All' = ANY(ARRAY[${sen_thickness}]) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${sen_thickness}])) OR\n           (CASE substring(proto_assembly.proto_name from 7 for 1)\n                WHEN '1' THEN '120'\n                WHEN '2' THEN '200'\n                WHEN '3' THEN '300'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${sen_thickness}]))\n\n      AND ('All' = ANY(ARRAY[${geometry}]) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END IS NULL AND 'NULL' = ANY(ARRAY[${geometry}])) OR\n           (CASE substring(proto_assembly.proto_name from 6 for 1)\n                WHEN 'F' THEN 'Full'\n                WHEN 'T' THEN 'Top'\n                WHEN 'B' THEN 'Bottom'\n                WHEN 'L' THEN 'Left'\n                WHEN 'R' THEN 'Right'\n                WHEN '5' THEN 'Five'\n                WHEN 'S' THEN 'Whole'\n                WHEN 'M' THEN 'Half-moons'\n                ELSE NULL\n            END)::text = ANY(ARRAY[${geometry}]))\n\n      AND $__timeFilter(proto_assembly.ass_run_date)\n      AND proto_assembly.ass_run_date IS NOT NULL\n    GROUP BY 1\n),\n\ncum_proto AS (\n    SELECT\n        local_date,\n        SUM(cnt) OVER (\n            ORDER BY local_date\n            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW\n        ) AS proto_total\n    FROM daily_proto\n)\n\nSELECT\n    (COALESCE(m.local_date, p.local_date)::timestamp + interval '12 hour') AS \"time\",\n    m.module_total AS module_assembly,\n    p.proto_total AS proto_assembly\nFROM cum_module m\nFULL OUTER JOIN cum_proto p\n    ON m.local_date = p.local_date\nORDER BY \"time\";",
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
                    "h": 2,
                    "w": 24,
                    "x": 0,
                    "y": 16
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
                    "y": 18
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
                    "y": 18
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
                    "y": 18
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
                    "h": 2,
                    "w": 24,
                    "x": 0,
                    "y": 27
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
                    "y": 29
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


# ============================================================
# === Module Assembly Builder ================================
# ============================================================

class ModuleAssemblyBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("General Info")
        self.timezone = f"{timezone}"
        self.bp_material = "{bp_material}"
        self.resolution = "{resolution}"
        self.roc_version = "{roc_version}"
        self.sen_thickness = "{sen_thickness}"
        self.geometry = "{geometry}"
        self.final_grade = "{final_grade}"
        self.module_name = "{module_name}"

        self.table_sql = f"""WITH
                temp_table_0 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_info
                WHERE ('$module_name' = '' OR module_name = '${self.module_name}')
                ORDER BY module_name, module_no DESC
                ),

                temp_table_1 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_qc_summary
                WHERE ('$module_name' = '' OR module_name = '${self.module_name}')
                ORDER BY module_name, mod_qc_no DESC
                ),

                temp_table_2 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_iv_test
                WHERE status = 7 OR status = 8
                AND ('$module_name' = '' OR module_name = '${self.module_name}')
                ORDER BY module_name, temp_c DESC
                ),

                temp_table_3 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_pedestal_test
                WHERE status = 7 OR status = 8
                AND ('$module_name' = '' OR module_name = '${self.module_name}')
                ORDER BY module_name, temp_c DESC
                )
        SELECT 
            temp_table_0.module_name::text,
            temp_table_0.assembled::text,
            temp_table_0.wb_back::text,
            temp_table_0.encap_back::text,
            temp_table_0.wb_front::text,
            temp_table_0.encap_front::text,
            temp_table_2.temp_c::text,
            temp_table_2.date_test::text AS test_iv,
            temp_table_3.date_test::text AS test_ped,
            temp_table_0.xml_upload_success::text,
            temp_table_0.packed_datetime::text,
            temp_table_0.shipped_datetime::text
        FROM temp_table_0
        LEFT JOIN temp_table_1 ON temp_table_0.module_name = temp_table_1.module_name
        LEFT JOIN temp_table_2 ON temp_table_0.module_name = temp_table_2.module_name
        LEFT JOIN temp_table_3 ON temp_table_0.module_name = temp_table_3.module_name
        WHERE 
                ('All' = ANY(ARRAY[${self.bp_material}]) OR 
                (temp_table_0.bp_material IS NULL AND 'NULL' = ANY(ARRAY[${self.bp_material}])) OR 
                temp_table_0.bp_material::text = ANY(ARRAY[${self.bp_material}]))
          AND 
                ('All' = ANY(ARRAY[${self.resolution}]) OR 
                (temp_table_0.resolution IS NULL AND 'NULL' = ANY(ARRAY[${self.resolution}])) OR 
                temp_table_0.resolution::text = ANY(ARRAY[${self.resolution}]))
          AND 
                ('All' = ANY(ARRAY[${self.roc_version}]) OR 
                (temp_table_0.roc_version IS NULL AND 'NULL' = ANY(ARRAY[${self.roc_version}])) OR 
                temp_table_0.roc_version::text = ANY(ARRAY[${self.roc_version}]))
          AND 
                ('All' = ANY(ARRAY[${self.sen_thickness}]) OR 
                (temp_table_0.sen_thickness IS NULL AND 'NULL' = ANY(ARRAY[${self.sen_thickness}])) OR 
                temp_table_0.sen_thickness::text = ANY(ARRAY[${self.sen_thickness}]))
          AND 
                ('All' = ANY(ARRAY[${self.geometry}]) OR 
                (temp_table_0.geometry IS NULL AND 'NULL' = ANY(ARRAY[${self.geometry}])) OR 
                temp_table_0.geometry::text = ANY(ARRAY[${self.geometry}]))
          AND $__timeFilter(temp_table_0.assembled AT TIME ZONE '{self.timezone}')
          AND 
                ('All' = ANY(ARRAY[${self.final_grade}]) OR 
                (temp_table_1.final_grade IS NULL AND 'NULL' = ANY(ARRAY[${self.final_grade}])) OR 
                temp_table_1.final_grade::text = ANY(ARRAY[${self.final_grade}]))
          AND bp_material IS NOT NULL AND resolution IS NOT NULL AND roc_version IS NOT NULL AND geometry IS NOT NULL
        ORDER BY temp_table_0.module_no DESC"""
    
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
                        "align": "auto",
                        "cellOptions": {
                        "type": "auto"
                        },
                        "inspect": False
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
                    "overrides": [
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "test_iv"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            },
                            {
                                "options": {
                                "match": "empty",
                                "result": {
                                    "color": "red",
                                    "index": 1
                                }
                                },
                                "type": "special"
                            },
                            {
                                "options": {
                                "pattern": ".+",
                                "result": {
                                    "color": "green",
                                    "index": 2
                                }
                                },
                                "type": "regex"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "test_ped"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            },
                            {
                                "options": {
                                "match": "empty",
                                "result": {
                                    "color": "red",
                                    "index": 1
                                }
                                },
                                "type": "special"
                            },
                            {
                                "options": {
                                "pattern": ".+",
                                "result": {
                                    "color": "green",
                                    "index": 2
                                }
                                },
                                "type": "regex"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "wb_back"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "encap_back"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "wb_front"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "encap_front"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "xml_upload_success"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "orange",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            },
                            {
                                "options": {
                                "match": "False",
                                "result": {
                                    "color": "red",
                                    "index": 1
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "shipped_datetime"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "assembled"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "packed_datetime"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 0
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "module_name"
                        },
                        "properties": [
                        {
                            "id": "custom.width",
                            "value": 161
                        }
                        ]
                    },
                    {
                        "matcher": {
                        "id": "byName",
                        "options": "temp_c"
                        },
                        "properties": [
                        {
                            "id": "custom.cellOptions",
                            "value": {
                            "type": "color-background"
                            }
                        },
                        {
                            "id": "mappings",
                            "value": [
                            {
                                "options": {
                                "from": -50,
                                "result": {
                                    "color": "green",
                                    "index": 0
                                },
                                "to": -30
                                },
                                "type": "range"
                            },
                            {
                                "options": {
                                "from": 20,
                                "result": {
                                    "color": "orange",
                                    "index": 1
                                },
                                "to": 50
                                },
                                "type": "range"
                            },
                            {
                                "options": {
                                "match": "null",
                                "result": {
                                    "color": "red",
                                    "index": 2
                                }
                                },
                                "type": "special"
                            }
                            ]
                        }
                        ]
                    }
                    ]
                },
                "gridPos": {
                    "h": 15,
                    "w": 24,
                    "x": 0,
                    "y": 0
                },
                "id": 12,
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
                    "rawSql":  self.table_sql,
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
                }
            ],
            "preload": False,
            "refresh": "5m",
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
            "title": "Module Assembly",
            "uid": "module-assembly",
            "version": 14
            }

        return dashboard_json


# ============================================================
# === XML Success Builder ====================================
# ============================================================

class XMLSuccessBuilder:
    def __init__(self, datasource_uid, timezone = 'America/New_York'):
        self.datasource_uid = datasource_uid
        self.dashboard_uid = create_uid("XML Upload Status")
        self.timezone = f"{timezone}"

        self.table_sql = f"""
        WITH module_info_failed AS (
            SELECT DISTINCT ON (module_name) module_no, module_name, xml_upload_success
            FROM module_info
            WHERE $__timeFilter(module_info.assembled) 
            ORDER BY module_name, xml_upload_success, module_no DESC
        ),
        proto_assembly_failed AS (
            SELECT DISTINCT ON (proto_assembly.proto_name) module_info.module_name, proto_assembly.xml_upload_success
            FROM proto_assembly
            JOIN module_info ON proto_assembly.proto_name = module_info.proto_name
            ORDER BY proto_assembly.proto_name, proto_assembly.xml_upload_success, proto_assembly.proto_no DESC
        ),
        proto_inspect_failed AS (
            SELECT DISTINCT ON (proto_inspect.proto_name) module_info.module_name, proto_inspect.xml_upload_success
            FROM proto_inspect
            JOIN module_info ON proto_inspect.proto_name = module_info.proto_name
            ORDER BY proto_inspect.proto_name, proto_inspect.xml_upload_success, proto_inspect.proto_no DESC
        ),
        module_assembly_failed AS (
            SELECT DISTINCT ON (module_assembly.module_name) module_assembly.module_name, module_assembly.xml_upload_success
            FROM module_assembly
            ORDER BY module_assembly.module_name, module_assembly.xml_upload_success, module_assembly.module_no DESC
        ),
        module_inspect_failed AS (
            SELECT DISTINCT ON (module_inspect.module_name) module_inspect.module_name, module_inspect.xml_upload_success
            FROM module_inspect
            ORDER BY module_inspect.module_name, module_inspect.xml_upload_success, module_inspect.module_no DESC
        ),
        module_iv_failed AS (
            SELECT DISTINCT ON (module_iv_test.module_name) module_iv_test.module_name, module_iv_test.xml_upload_success
            FROM module_iv_test
            WHERE status = 7 OR status = 8
            ORDER BY module_iv_test.module_name, module_iv_test.xml_upload_success, module_iv_test.module_no DESC
        ),
        module_pedestal_failed AS (
            SELECT DISTINCT ON (module_pedestal_test.module_name) module_pedestal_test.module_name, module_pedestal_test.xml_upload_success
            FROM module_pedestal_test
            WHERE status = 7 OR status = 8
            ORDER BY module_pedestal_test.module_name, module_pedestal_test.xml_upload_success, module_pedestal_test.module_no DESC
        ),
        module_grade_failed AS (
            SELECT DISTINCT ON (module_qc_summary.module_name) module_qc_summary.module_name, module_qc_summary.xml_upload_success
            FROM module_qc_summary
            ORDER BY module_qc_summary.module_name, module_qc_summary.xml_upload_success, module_qc_summary.mod_qc_no DESC
        )
        SELECT
            module_info_failed.module_no,
            module_info_failed.module_name,
            module_info_failed.xml_upload_success AS module_build,
            proto_assembly_failed.xml_upload_success AS proto_assembly,
            proto_inspect_failed.xml_upload_success AS proto_inspect,
            module_assembly_failed.xml_upload_success AS module_assembly,
            module_inspect_failed.xml_upload_success AS module_inspect,
            module_iv_failed.xml_upload_success AS module_iv,
            module_pedestal_failed.xml_upload_success AS module_pedestal,
            module_grade_failed.xml_upload_success AS module_grade
        FROM module_info_failed
        LEFT JOIN proto_assembly_failed
            ON module_info_failed.module_name = proto_assembly_failed.module_name
        LEFT JOIN proto_inspect_failed
            ON module_info_failed.module_name = proto_inspect_failed.module_name
        LEFT JOIN module_assembly_failed
            ON module_info_failed.module_name = module_assembly_failed.module_name
        LEFT JOIN module_inspect_failed
            ON module_info_failed.module_name = module_inspect_failed.module_name
        LEFT JOIN module_iv_failed
            ON module_info_failed.module_name = module_iv_failed.module_name
        LEFT JOIN module_pedestal_failed
            ON module_info_failed.module_name = module_pedestal_failed.module_name
        LEFT JOIN module_grade_failed
            ON module_info_failed.module_name = module_grade_failed.module_name
        ORDER BY module_info_failed.module_no DESC;
        """

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
                    }
                    ]
                }
                },
                "overrides": [
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_build"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_no"
                    },
                    "properties": [
                    {
                        "id": "custom.width",
                        "value": 42
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_name"
                    },
                    "properties": [
                    {
                        "id": "custom.width",
                        "value": 165
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "proto_assembly"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "proto_inspect"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_assembly"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_inspect"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_iv"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_pedestal"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_grade"
                    },
                    "properties": [
                    {
                        "id": "custom.cellOptions",
                        "value": {
                        "type": "color-background"
                        }
                    },
                    {
                        "id": "mappings",
                        "value": [
                        {
                            "options": {
                            "match": "True",
                            "result": {
                                "color": "green",
                                "index": 0
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "False",
                            "result": {
                                "color": "orange",
                                "index": 1
                            }
                            },
                            "type": "special"
                        },
                        {
                            "options": {
                            "match": "null",
                            "result": {
                                "color": "red",
                                "index": 2
                            }
                            },
                            "type": "special"
                        }
                        ]
                    }
                    ]
                }
                ]
            },
            "gridPos": {
                "h": 16,
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
                "showHeader": True,
                "sortBy": [
                {
                    "desc": True,
                    "displayName": "module_no"
                }
                ]
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
            "title": "XML ",
            "type": "table"
            }
        ],
        "preload": False,
        "schemaVersion": 41,
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-30d",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "browser",
        "title": "XML Upload Status",
        "uid": self.dashboard_uid
        }

        return dashboard_json