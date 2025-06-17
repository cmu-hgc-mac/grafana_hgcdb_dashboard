import os
import json

from tool.helper import *

"""
This file defines classes for building additional Grafana features, including:
    - Filters: With support from Wen Li.
"""

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
        else:
            filter_sql = f"""
            SELECT DISTINCT {filter_name} FROM {filters_table} ORDER BY {filter_name}
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
                elif elem == "assembled" or elem.endswith("time") or elem.endswith("date") or elem.endswith("timestamp") or elem.startswith("date"):
                    continue    # filter not used in dashboard
            
                exist_filter.add(elem)

                # generate the filter's json
                filter_sql = self.generate_filterSQL(elem, filters_table)
                filter_json = self.generate_filter(elem, filter_sql)
                template_list.append(filter_json)
        
        return template_list