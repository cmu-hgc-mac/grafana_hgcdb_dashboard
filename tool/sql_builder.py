import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type:
        - "barchart"
        - "histogram"
        - "timeseries"
        - "text"
        - "stat"
        - "table"
"""

# ============================================================
# === Define the Abstract Class ==============================
# ============================================================

class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pass


# ============================================================
# === Base SQL Generator =====================================
# ============================================================

class BaseSQLGenerator(ChartSQLGenerator):
    # inherit from the abstract class -> ChartSQLGenerator
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pass

    # Base SQL for all chart types
    def _build_pre_clause(self, table: str, distinct: bool) -> str:
        """Builds the pre-SELECT clause for histogram. 
           - If distinct is True, it will select the distinct modules.
           - Hard Coded Version: Only for module_qc_summary table.
        """
        # fetch distinct modules from "module_qc_summary"
        if distinct:
            target_table = "temp_table"
            if table == "module_qc_summary":
                pre_clause = """WITH temp_table AS (SELECT DISTINCT ON (module_no) * FROM module_qc_summary ORDER BY module_no, mod_qc_no DESC)"""
        
        else:
            target_table = table
            pre_clause = ""
        
        return pre_clause, target_table
    
    def _build_filter_argument(self, elem: str, filters_table: str) -> str:
        """Builds the filter argument for the WHERE clause.
        """
        # shipped / not shipped
        if elem == "status":
            param = "${status}"
            arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                    (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                    (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""

        # time: using the Grafana built-in time filter
        elif elem == "assembled" or elem.endswith("time") or elem.endswith("date"):
            arg = f"$__timeFilter({filters_table}.{elem})"
        
        # general cases
        else:
            param = f"${{{elem}}}"
            arg = f"('All' = ANY(ARRAY[{param}]) OR {filters_table}.{elem}::text = ANY(ARRAY[{param}]))"

        return arg

    def _build_where_clause(self, filters: dict, condition: str, table: str, distinct: bool) -> str:
        """Builds the WHERE clause from filters and condition. 
        """
        filters_table_list = list(filters.keys())
        where_clauses = []

        for filters_table in filters_table_list:
            # update table name with distinct condition
            if filters_table == table:
                if distinct:
                    filters["temp_table"] = filters.pop(f"{filters_table}")
                    filters_table = "temp_table"

            # build the WHERE clause for each filter
            for elem in filters[filters_table]:
                arg = self._build_filter_argument(elem, filters_table)
                where_clauses.append(arg)   

        if condition:
            where_clauses.append(condition) 
        
        return "\n          AND ".join(where_clauses)

    def _build_join_clause(self, table: str, filters: dict, distinct: bool) -> str:
        """Builds the JOIN command by using the foriegn key.
        """
        join_clause = []
        
        # update table name with distinct condition
        main_table = "temp_table" if distinct else table
        main_prefix = table.split("_")[0]

        for filters_table in filters:
            if filters_table == main_table:
                continue  # skip self-joining
            else:
                join_clause.append(f"JOIN {filters_table} ON {main_table}.{main_prefix}_no = {filters_table}.{main_prefix}_no")

        return "\n        ".join(join_clause)


# ============================================================
# === Chart SQL Generator ====================================
# ============================================================

# -- BarChart --
class BarChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, filters, distinct)

        sql = f"""
        {pre_clause}
        SELECT 
            {select_clause} AS label,
            COUNT(*) AS count
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        GROUP BY label
        ORDER BY label;
        """
        return sql.strip()
    
    def _build_select_clause(self, table: str, groupby: list, distinct: bool) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []

        if distinct:
            table = "temp_table"

        for elem in groupby:
            if isinstance(elem, str):
                if elem.endswith("time"):
                    continue
                elif elem.startswith("list"):
                    groupby_fields.append(f"COALESCE(array_length({table}.{elem}::int[], 1), 0)::text")
                else:
                    groupby_fields.append(f"{table}.{elem}::text")
            # COALESCE Case: join multiple columns into 1 column
            elif isinstance(elem, list):
                select_clause = []
                for column in elem:
                    if column.startswith("list"):
                        select_arg = f"COALESCE(array_length({table}.{column}::int[], 1), 0)"
                    else:
                        select_arg = f"{table}.{column}"
                    select_clause.append(select_arg)
                select_clause = f"COALESCE({', '.join(select_clause)}) as {elem[0]}"
                groupby_fields.append(select_clause)

        return " || '/' || ".join(groupby_fields)


# -- Histogram --
class HistogramGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, filters, distinct)

        sql = f"""
        {pre_clause}
        SELECT {select_clause}
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """

        return sql
    
    def _build_select_clause(self, table: str, groupby: list, distinct: bool) -> str:
        """Builds the SELECT clause from groupby. 
           - For histogram, there should only be 1 element in groupby.
        """
        if distinct:
            table = "temp_table"

        # check for the lenght of groupby:
        if len(groupby) > 1:
            raise ValueError("The groupby list should have only 1 element.")
        
        # fetch the element from groupby
        elem = groupby[0]

        if isinstance(elem, str):
            elem = groupby[0]
            if elem.startswith("list"):
                groupby_fields = f"COALESCE(array_length({table}.{elem}::int[], 1), 0) AS {elem}"
            else:
                groupby_fields = f"{table}.{elem} AS {elem}"
        # COALESCE Case: join multiple columns into 1 column
        elif isinstance(elem, list):
            select_clause = []
            for column in groupby[0]:
                if column.startswith("list"):
                    select_arg = f"COALESCE(array_length({table}.{column}::int[], 1), 0)"
                else:
                    select_arg = f"{table}.{column}"
                select_clause.append(select_arg)
            groupby_fields = f"COALESCE({', '.join(select_clause)}) as {groupby[0][0]}"

        return groupby_fields


# -- Timeseries --
class TimeseriesGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, filters, distinct)
        orderby_clause = self._build_orderby_clause(groupby)

        sql = f"""
        SELECT 
            {select_clause}
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        {orderby_clause};
        """
        return sql.strip()

    def _build_select_clause(self, table: str, groupby: list) -> str:
        """Builds the SELECT clause from groupby.    
        """
        # Currently, it is setted to have the first element as time and the second element as the element to be counted.
        # It is definetly not ideal, I will try to come up with a better solution later.
        time = groupby[0]
        elem = groupby[1]
        select_clause = []

        # Time
        time_arg = f"{table}.{time} AS date"
        select_clause.append(time_arg)

        # Element
        if elem.startswith("list"):
            elem_arg = f"COALESCE(array_length({table}.{elem}::int[], 1), 0) AS {elem}"
        elif elem == "count":
            elem_arg = "COUNT(*) AS count"
        else:
            elem_arg = f"{table}.{elem} AS {elem}"
        select_clause.append(elem_arg)

        return ", ".join(select_clause)
    
    def _build_orderby_clause(self, groupby: list) -> str:
        """Builds the ORDER BY clause from groupby.
        """
        time = groupby[0]
        elem = groupby[1]
        clause = []

        groupby_arg = f"GROUP BY {time}" if elem == "count" else ""
        orderby_arg = f"ORDER BY {time}"

        clause.append(groupby_arg)
        clause.append(orderby_arg)

        return "\n        ".join(clause)


# -- Text Chart --
class TextChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        return None


# -- Stat Chart --
class StatChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)        
        where_clause = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, filters, distinct)
        
        sql = f"""
        {pre_clause}
        SELECT COUNT(*) AS count
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """

        return sql.strip()


# -- Table Chart --
class TableGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, filters, distinct)

        sql = f"""
        {pre_clause}
        SELECT 
            {select_clause}
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """
        return sql.strip()

    def _build_select_clause(self, table: str, groupby: list, distinct: bool) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []

        if distinct:
            table = "temp_table"

        for elem in groupby:
            if isinstance(elem, str):
                if elem.endswith("time"):
                    continue
                elif elem.startswith("list"):
                    groupby_fields.append(f"COALESCE(array_length({table}.{elem}::int[], 1), 0)::text")
                else:
                    groupby_fields.append(f"{table}.{elem}::text")
            elif isinstance(elem, list):
                select_clause = []
                for column in elem:
                    if column.startswith("list"):
                        select_arg = f"COALESCE(array_length({table}.{column}::int[], 1), 0)"
                    else:
                        select_arg = f"{table}.{column}"
                    select_clause.append(select_arg)
                select_clause = f"COALESCE({', '.join(select_clause)}) as {elem[0]}"
                groupby_fields.append(select_clause)

        return ", ".join(groupby_fields)


# ============================================================
# === SQL Generator Factory ==================================
# ============================================================

class ChartSQLFactory:
    _generators = {
        "barchart": BarChartGenerator(),
        "histogram": HistogramGenerator(),
        "timeseries": TimeseriesGenerator(),
        "text": TextChartGenerator(),
        "stat": StatChartGenerator(),
        "table": TableGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator