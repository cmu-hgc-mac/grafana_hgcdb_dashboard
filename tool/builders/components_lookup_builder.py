from tool.helper import *
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

        self.mean_hexmap_sql = f"""
        SELECT DISTINCT ON (module_pedestal_plots.module_name) encode(adc_mean_hexmap, 'base64') AS hex_img
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
        SELECT DISTINCT ON (module_pedestal_plots.module_name) encode(adc_std_hexmap, 'base64') AS hex_img
        FROM module_pedestal_plots
        JOIN module_info ON module_pedestal_plots.module_name = module_info.module_name
        WHERE (module_info.module_name = {self.module_name}
            OR module_info.proto_name = {self.proto_name}
            OR module_info.sen_name = {self.sen_name}
            OR module_info.bp_name = {self.bp_name}
            OR module_info.hxb_name = {self.hxb_name})
        ORDER BY module_pedestal_plots.module_name, module_pedestal_plots.mod_plottest_no DESC
        """

        self.mean_hexmap_md = '<img src="data:image/png;base64,${mean_hex_map}" style="width: auto; height: auto;"/>'
        self.std_hexmap_md = '<img src="data:image/png;base64,${std_hex_map}" style="width: auto; height: auto;"/>'

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
                    "keepFields": True,
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
            "pluginVersion": "12.0.1",
            "repeat": "mean_hex_map",
            "repeatDirection": "v",
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
            "pluginVersion": "12.0.1",
            "repeat": "std_hex_map",
            "repeatDirection": "v",
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
                "skipUrlSync": True,
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
                "skipUrlSync": True,
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
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
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
                "datasource": {
                    "type": "postgres",
                    "uid": f"{self.datasource_uid}"
                },
                "type": "query"
            },
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
                "skipUrlSync": True,
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

