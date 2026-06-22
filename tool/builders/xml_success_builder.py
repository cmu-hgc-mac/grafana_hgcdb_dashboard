from tool.helper import *
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
        ),
        hxb_inspect_failed AS (
            SELECT DISTINCT ON (hxb_inspect.hxb_name) module_info.module_name, hxb_inspect.xml_upload_success
            FROM hxb_inspect
            JOIN module_info ON hxb_inspect.hxb_name = module_info.hxb_name
            ORDER BY hxb_inspect.hxb_name, hxb_inspect.xml_upload_success, hxb_inspect.hxb_no DESC
        ),
        bp_inspect_failed AS (
            SELECT DISTINCT ON (bp_inspect.bp_name) module_info.module_name, bp_inspect.xml_upload_success
            FROM bp_inspect
            JOIN module_info ON bp_inspect.bp_name = module_info.bp_name
            ORDER BY bp_inspect.bp_name, bp_inspect.xml_upload_success, bp_inspect.bp_no DESC
        ),
        hxb_pedestal_failed AS (
            SELECT DISTINCT ON (hxb_pedestal_test.hxb_name) module_info.module_name, hxb_pedestal_test.xml_upload_success
            FROM hxb_pedestal_test
            JOIN module_info ON hxb_pedestal_test.hxb_name = module_info.hxb_name
            ORDER BY hxb_pedestal_test.hxb_name, hxb_pedestal_test.xml_upload_success, hxb_pedestal_test.hxb_no DESC
        ),
        sen_inspect_failed AS (
            SELECT DISTINCT ON (sensor.sen_name) module_info.module_name, sensor.xml_upload_success
            FROM sensor
            JOIN module_info ON sensor.sen_name = module_info.sen_name
            ORDER BY sensor.sen_name, sensor.xml_upload_success, sensor.sen_no DESC
        ),
        back_wirebond_failed AS (
            SELECT DISTINCT ON (back_wirebond.module_name) back_wirebond.module_name, back_wirebond.xml_upload_success
            FROM back_wirebond
            ORDER BY back_wirebond.module_name, back_wirebond.xml_upload_success, back_wirebond.module_no DESC
        ),
        back_encap_failed AS (
            SELECT DISTINCT ON (back_encap.module_name) back_encap.module_name, back_encap.xml_upload_success
            FROM back_encap
            ORDER BY back_encap.module_name, back_encap.xml_upload_success, back_encap.module_no DESC
        ),
        front_wirebond_failed AS (
            SELECT DISTINCT ON (front_wirebond.module_name) front_wirebond.module_name, front_wirebond.xml_upload_success
            FROM front_wirebond
            ORDER BY front_wirebond.module_name, front_wirebond.xml_upload_success, front_wirebond.module_no DESC
        ),
        front_encap_failed AS (
            SELECT DISTINCT ON (front_encap.module_name) front_encap.module_name, front_encap.xml_upload_success
            FROM front_encap
            ORDER BY front_encap.module_name, front_encap.xml_upload_success, front_encap.module_no DESC
        ),
        bond_pull_failed AS (
            SELECT DISTINCT ON (bond_pull_test.module_name) bond_pull_test.module_name, bond_pull_test.xml_upload_success
            FROM bond_pull_test
            ORDER BY bond_pull_test.module_name, bond_pull_test.xml_upload_success, bond_pull_test.module_no DESC
        ),
        result AS (
        SELECT
            module_info_failed.module_no,
            module_info_failed.module_name,
            CASE
                WHEN module_info_failed.module_name IS NULL THEN 'N/A'
                WHEN module_info_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_info_failed.xml_upload_success::text
            END AS module_build,
            CASE
                WHEN proto_assembly_failed.module_name IS NULL THEN 'N/A'
                WHEN proto_assembly_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE proto_assembly_failed.xml_upload_success::text
            END AS proto_assembly,
            CASE
                WHEN proto_inspect_failed.module_name IS NULL THEN 'N/A'
                WHEN proto_inspect_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE proto_inspect_failed.xml_upload_success::text
            END AS proto_inspect,
            CASE
                WHEN module_assembly_failed.module_name IS NULL THEN 'N/A'
                WHEN module_assembly_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_assembly_failed.xml_upload_success::text
            END AS module_assembly,
            CASE
                WHEN module_inspect_failed.module_name IS NULL THEN 'N/A'
                WHEN module_inspect_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_inspect_failed.xml_upload_success::text
            END AS module_inspect,
            CASE
                WHEN (back_wirebond_failed.module_name IS NULL OR back_encap_failed.module_name IS NULL OR front_wirebond_failed.module_name IS NULL OR front_encap_failed.module_name IS NULL) THEN 'N/A'
                WHEN (back_wirebond_failed.xml_upload_success IS NULL OR back_encap_failed.xml_upload_success IS NULL OR front_wirebond_failed.xml_upload_success IS NULL OR front_encap_failed.xml_upload_success IS NULL) THEN 'NULL'
                WHEN (back_wirebond_failed.xml_upload_success = 'true' AND back_encap_failed.xml_upload_success = 'true' AND front_wirebond_failed.xml_upload_success = 'true' AND front_encap_failed.xml_upload_success = 'true') THEN 'true'
                WHEN (back_wirebond_failed.xml_upload_success = 'false' OR back_encap_failed.xml_upload_success = 'false' OR front_wirebond_failed.xml_upload_success = 'false' OR front_encap_failed.xml_upload_success = 'false' OR bond_pull_failed.xml_upload_success = 'false') THEN 'false'
            END AS module_wirebond,
            CASE
                WHEN module_iv_failed.module_name IS NULL THEN 'N/A'
                WHEN module_iv_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_iv_failed.xml_upload_success::text
            END AS module_iv,
            CASE
                WHEN module_pedestal_failed.module_name IS NULL THEN 'N/A'
                WHEN module_pedestal_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_pedestal_failed.xml_upload_success::text
            END AS module_pedestal,
            CASE
                WHEN module_grade_failed.module_name IS NULL THEN 'N/A'
                WHEN module_grade_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE module_grade_failed.xml_upload_success::text
            END AS module_grade,       
            CASE
                WHEN bp_inspect_failed.module_name IS NULL THEN 'N/A'
                WHEN bp_inspect_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE bp_inspect_failed.xml_upload_success::text
            END AS bp_inspect,
            CASE
                WHEN sen_inspect_failed.module_name IS NULL THEN 'N/A'
                WHEN sen_inspect_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE sen_inspect_failed.xml_upload_success::text
            END AS sen_inspect,
            CASE
                WHEN hxb_inspect_failed.module_name IS NULL THEN 'N/A'
                WHEN hxb_inspect_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE hxb_inspect_failed.xml_upload_success::text
            END AS hxb_inspect,
            CASE
                WHEN hxb_pedestal_failed.module_name IS NULL THEN 'N/A'
                WHEN hxb_pedestal_failed.xml_upload_success IS NULL THEN 'NULL'
                ELSE hxb_pedestal_failed.xml_upload_success::text
            END AS hxb_pedestal
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
        LEFT JOIN hxb_inspect_failed
            ON module_info_failed.module_name = hxb_inspect_failed.module_name
        LEFT JOIN bp_inspect_failed
            ON module_info_failed.module_name = bp_inspect_failed.module_name
        LEFT JOIN hxb_pedestal_failed
            ON module_info_failed.module_name = hxb_pedestal_failed.module_name
        LEFT JOIN sen_inspect_failed
            ON module_info_failed.module_name = sen_inspect_failed.module_name
        LEFT JOIN back_wirebond_failed
            ON module_info_failed.module_name = back_wirebond_failed.module_name
        LEFT JOIN back_encap_failed
            ON module_info_failed.module_name = back_encap_failed.module_name
        LEFT JOIN front_wirebond_failed
            ON module_info_failed.module_name = front_wirebond_failed.module_name
        LEFT JOIN front_encap_failed
            ON module_info_failed.module_name = front_encap_failed.module_name
        LEFT JOIN bond_pull_failed
            ON module_info_failed.module_name = bond_pull_failed.module_name
        WHERE ('${{module_name}}' = '' OR module_info_failed.module_name ILIKE '%' || '${{module_name}}' || '%')
        ORDER BY module_info_failed.module_no DESC
        )
        SELECT * FROM result
        WHERE (
            ('${{show_failed_uploads}}' != 'Yes' AND '${{show_unattempted_uploads}}' != 'Yes')
            OR ('${{show_failed_uploads}}' = 'Yes' AND (
                module_build = 'false' OR proto_assembly = 'false' OR proto_inspect = 'false'
                OR module_assembly = 'false' OR module_inspect = 'false' OR module_wirebond = 'false'
                OR module_iv = 'false' OR module_pedestal = 'false' OR module_grade = 'false'
                OR bp_inspect = 'false' OR sen_inspect = 'false' OR hxb_inspect = 'false'
                OR hxb_pedestal = 'false'
            ))
            OR ('${{show_unattempted_uploads}}' = 'Yes' AND (
                module_build = 'NULL' OR proto_assembly = 'NULL' OR proto_inspect = 'NULL'
                OR module_assembly = 'NULL' OR module_inspect = 'NULL' OR module_wirebond = 'NULL'
                OR module_iv = 'NULL' OR module_pedestal = 'NULL' OR module_grade = 'NULL'
                OR bp_inspect = 'NULL' OR sen_inspect = 'NULL' OR hxb_inspect = 'NULL'
                OR hxb_pedestal = 'NULL'
            ))
        )
        ORDER BY module_no DESC;
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "hxb_inspect"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "bp_inspect"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "hxb_pedestal"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "sen_inspect"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
                        }
                        ]
                    }
                    ]
                },
                {
                    "matcher": {
                    "id": "byName",
                    "options": "module_wirebond"
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
                            "N/A": {
                                "color": "transparent",
                                "index": 0
                            },
                            "NULL": {
                                "color": "orange",
                                "index": 1
                            },
                            "false": {
                                "color": "red",
                                "index": 3
                            },
                            "true": {
                                "color": "green",
                                "index": 2
                            }
                            },
                            "type": "value"
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
                        "text": "No",
                        "value": "No"
                    },
                    "label": "Failed Uploads Only",
                    "name": "show_failed_uploads",
                    "options": [
                        {
                            "selected": True,
                            "text": "No",
                            "value": "No"
                        },
                        {
                            "selected": False,
                            "text": "Yes",
                            "value": "Yes"
                        }
                    ],
                    "query": "No,Yes",
                    "type": "custom"
                },
                {
                    "current": {
                        "text": "No",
                        "value": "No"
                    },
                    "label": "Unattempted Uploads Only",
                    "name": "show_unattempted_uploads",
                    "options": [
                        {
                            "selected": True,
                            "text": "No",
                            "value": "No"
                        },
                        {
                            "selected": False,
                            "text": "Yes",
                            "value": "Yes"
                        }
                    ],
                    "query": "No,Yes",
                    "type": "custom"
                }
            ]
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
