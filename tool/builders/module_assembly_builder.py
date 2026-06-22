from tool.helper import *
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
        self.test_status = "{test_status}"
        self.assembly_status = "{assembly_status}"
        self.pack_ship_status = "{pack_ship_status}"

        self.table_sql = f"""WITH
                temp_table_0 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_info
                WHERE ('${self.module_name}' = '' OR module_name ILIKE '%' || '${self.module_name}' || '%')
                ORDER BY module_name, module_no DESC
                ),

                temp_table_1 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_qc_summary
                WHERE ('${self.module_name}' = '' OR module_name ILIKE '%' || '${self.module_name}' || '%')
                ORDER BY module_name, mod_qc_no DESC
                ),

                temp_table_2 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_iv_test
                WHERE (status = 7 OR status = 8)
                AND ('${self.module_name}' = '' OR module_name ILIKE '%' || '${self.module_name}' || '%')
                ORDER BY module_name, temp_c DESC
                ),

                temp_table_3 AS (
                SELECT DISTINCT ON (module_name) *
                FROM module_pedestal_test
                WHERE (status = 7 OR status = 8)
                AND ('${self.module_name}' = '' OR module_name ILIKE '%' || '${self.module_name}' || '%')
                ORDER BY module_name, temp_c DESC
                )
        SELECT
            ROW_NUMBER() OVER (ORDER BY temp_table_0.module_no DESC) AS no,
            temp_table_0.module_name::text,
            temp_table_0.assembled::text,
            temp_table_1.final_grade::text,
            temp_table_0.inspected::text,
            temp_table_0.wb_back::text,
            temp_table_0.encap_back::text,
            temp_table_0.wb_front::text,
            temp_table_0.encap_front::text,
            temp_table_2.temp_c::text,
            temp_table_2.date_test::text AS test_iv,
            temp_table_3.date_test::text AS test_ped,
            temp_table_0.xml_upload_success::text AS xml_build_upload_success,
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
          AND (
            '${self.test_status}' = 'All'
            OR ('${self.test_status}' = 'Untested' AND (temp_table_2.module_name IS NULL OR temp_table_3.module_name IS NULL))
            OR ('${self.test_status}' = 'Tested' AND (temp_table_2.module_name IS NOT NULL AND temp_table_3.module_name IS NOT NULL))
            OR ('${self.test_status}' = 'Tested at < 0°C' AND (temp_table_2.module_name IS NOT NULL OR temp_table_3.module_name IS NOT NULL) AND EXISTS (SELECT 1 FROM module_iv_test WHERE module_iv_test.module_name = temp_table_0.module_name AND (module_iv_test.status = 7 OR module_iv_test.status = 8) AND module_iv_test.temp_c::numeric < 0))
            OR ('${self.test_status}' = 'Tested at > 0°C' AND (temp_table_2.module_name IS NOT NULL OR temp_table_3.module_name IS NOT NULL) AND EXISTS (SELECT 1 FROM module_iv_test WHERE module_iv_test.module_name = temp_table_0.module_name AND (module_iv_test.status = 7 OR module_iv_test.status = 8) AND module_iv_test.temp_c::numeric > 0))
            OR ('${self.test_status}' = 'Untested at < 0°C' AND NOT EXISTS (SELECT 1 FROM module_iv_test WHERE module_iv_test.module_name = temp_table_0.module_name AND (module_iv_test.status = 7 OR module_iv_test.status = 8) AND module_iv_test.temp_c::numeric < 0))
            OR ('${self.test_status}' = 'Untested at > 0°C' AND NOT EXISTS (SELECT 1 FROM module_iv_test WHERE module_iv_test.module_name = temp_table_0.module_name AND (module_iv_test.status = 7 OR module_iv_test.status = 8) AND module_iv_test.temp_c::numeric > 0))
          )
          AND (
            '${self.assembly_status}' = 'All'
            OR ('${self.assembly_status}' = 'Incomplete' AND (temp_table_0.assembled IS NULL OR temp_table_0.inspected IS NULL OR temp_table_0.wb_back IS NULL OR temp_table_0.encap_back IS NULL OR temp_table_0.wb_front IS NULL OR temp_table_0.encap_front IS NULL))
            OR ('${self.assembly_status}' = 'Complete' AND (temp_table_0.assembled IS NOT NULL AND temp_table_0.inspected IS NOT NULL AND temp_table_0.wb_back IS NOT NULL AND temp_table_0.encap_back IS NOT NULL AND temp_table_0.wb_front IS NOT NULL AND temp_table_0.encap_front IS NOT NULL))
          )
          AND (
            '${self.pack_ship_status}' = 'All'
            OR ('${self.pack_ship_status}' = 'Not packed (unshipped)' AND temp_table_0.packed_datetime IS NULL AND temp_table_0.shipped_datetime IS NULL)
            OR ('${self.pack_ship_status}' = 'Packed (unshipped)' AND temp_table_0.packed_datetime IS NOT NULL AND temp_table_0.shipped_datetime IS NULL)
            OR ('${self.pack_ship_status}' = 'Packed & Shipped' AND temp_table_0.packed_datetime IS NOT NULL AND temp_table_0.shipped_datetime IS NOT NULL)
            OR ('${self.pack_ship_status}' = 'Shipped; Not packed' AND temp_table_0.shipped_datetime IS NOT NULL AND temp_table_0.packed_datetime IS NULL)
          )
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
                        "options": "no"
                        },
                        "properties": [
                        {
                            "id": "custom.width",
                            "value": 50
                        }
                        ]
                    },
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
                        "options": "xml_build_upload_success"
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
                    },
                    {
            "matcher": {
              "id": "byName",
              "options": "final_grade"
            },
            "properties": [
              {
                "id": "mappings",
                "value": [
                  {
                    "options": {
                      "A": {
                        "color": "green",
                        "index": 0
                      },
                      "B": {
                        "color": "green",
                        "index": 1
                      },
                      "C": {
                        "color": "orange",
                        "index": 2
                      },
                      "F": {
                        "color": "red",
                        "index": 3
                      }
                    },
                    "type": "value"
                  },
                  {
                    "options": {
                      "match": "null",
                      "result": {
                        "color": "transparent",
                        "index": 4
                      }
                    },
                    "type": "special"
                  }
                ]
              },
              {
                "id": "custom.cellOptions",
                "value": {
                  "type": "color-background"
                }
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "inspected"
            },
            "properties": [
              {
                "id": "mappings",
                "value": [
                  {
                    "options": {
                      "A": {
                        "color": "green",
                        "index": 0
                      },
                      "B": {
                        "color": "green",
                        "index": 1
                      },
                      "C": {
                        "color": "orange",
                        "index": 2
                      },
                      "F": {
                        "color": "red",
                        "index": 3
                      }
                    },
                    "type": "value"
                  },
                  {
                    "options": {
                      "match": "null",
                      "result": {
                        "color": "transparent",
                        "index": 4
                      }
                    },
                    "type": "special"
                  }
                ]
              },
              {
                "id": "custom.cellOptions",
                "value": {
                  "type": "color-background"
                }
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
                },
                {
                    "current": {
                        "text": "All",
                        "value": "All"
                    },
                    "label": "Pack & Ship status",
                    "name": "pack_ship_status",
                    "options": [
                        {
                            "selected": True,
                            "text": "All",
                            "value": "All"
                        },
                        {
                            "selected": False,
                            "text": "Not packed (unshipped)",
                            "value": "Not packed (unshipped)"
                        },
                        {
                            "selected": False,
                            "text": "Packed (unshipped)",
                            "value": "Packed (unshipped)"
                        },
                        {
                            "selected": False,
                            "text": "Packed & Shipped",
                            "value": "Packed & Shipped"
                        },
                        {
                            "selected": False,
                            "text": "Shipped; Not packed",
                            "value": "Shipped; Not packed"
                        }
                    ],
                    "query": "All,Not packed (unshipped),Packed (unshipped),Packed & Shipped,Shipped; Not packed",
                    "type": "custom"
                },
                {
                    "current": {
                        "text": "All",
                        "value": "All"
                    },
                    "label": "Assembly status",
                    "name": "assembly_status",
                    "options": [
                        {
                            "selected": True,
                            "text": "All",
                            "value": "All"
                        },
                        {
                            "selected": False,
                            "text": "Complete",
                            "value": "Complete"
                        },
                        {
                            "selected": False,
                            "text": "Incomplete",
                            "value": "Incomplete"
                        }
                    ],
                    "query": "All,Complete,Incomplete",
                    "type": "custom"
                },
                {
                    "current": {
                        "text": "All",
                        "value": "All"
                    },
                    "label": "Test status",
                    "name": "test_status",
                    "options": [
                        {
                            "selected": True,
                            "text": "All",
                            "value": "All"
                        },
                        {
                            "selected": False,
                            "text": "Tested",
                            "value": "Tested"
                        },
                        {
                            "selected": False,
                            "text": "Untested",
                            "value": "Untested"
                        },
                        {
                            "selected": False,
                            "text": "Tested at < 0°C",
                            "value": "Tested at < 0°C"
                        },
                        {
                            "selected": False,
                            "text": "Tested at > 0°C",
                            "value": "Tested at > 0°C"
                        },
                        {
                            "selected": False,
                            "text": "Untested at < 0°C",
                            "value": "Untested at < 0°C"
                        },
                        {
                            "selected": False,
                            "text": "Untested at > 0°C",
                            "value": "Untested at > 0°C"
                        }
                    ],
                    "query": "All,Tested,Untested,Tested at < 0°C,Tested at > 0°C,Untested at < 0°C,Untested at > 0°C",
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
            "title": "Module Assembly",
            "uid": "module-assembly",
            "version": 14
            }

        return dashboard_json

