import copy
from abc import ABC, abstractmethod

from tool.helper import *

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type:
        - "barchart"
        - "histogram"
        - "timeseries"
        - "text": only available for IV_Curve Plot
        - "stat"
        - "table"
        - "gauge"
        - "piechart": only available for shipping status
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
    def _build_pre_clause(self, table: str, distinct: list):
        """Builds the pre-SELECT clause for histogram. 
           - If distinct is True, it will select the distinct modules.
        """
        if distinct:
            temp_table_list = []
            pre_clause_list = []

            for n, table in enumerate(distinct):
                temp_table_list.append(f"temp_table_{n}")

                distinct_column = get_distinct_column_name(table)   # first column name of the table
                
                if table in PREFIX:
                    prefix = PREFIX[table]
                else:
                    prefix = table.split("_")[0]

                sort_column = f"{prefix}_name"         # e.g.: hxb_no, module_no...

                arg = f"""
                {temp_table_list[n]} AS (
                SELECT DISTINCT ON ({sort_column}) *
                FROM {table}
                ORDER BY {sort_column}, {distinct_column} DESC
                )"""

                pre_clause_list.append(arg)

            pre_clause = "WITH" + ",\n".join(pre_clause_list)
            target_table = temp_table_list[0]   # default: temp_table_0
        
        else:
            pre_clause = ""
            target_table = table
    
        return pre_clause, target_table
    
    def _build_filter_argument(self, elem: str, filters_table: str) -> str:
        """Builds the filter argument for the WHERE clause.
        """
        # shipped / not shipped
        if elem == "shipping_status":
            param = "${shipping_status}"
            arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                    (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                    (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""

        # time: using the Grafana built-in time filter
        elif elem in TIME_COLUMNS:
            arg = f"$__timeFilter({filters_table}.{elem} AT TIME ZONE '{TIME_ZONE}')"
        
        # General Cases
        else:
            param = f"${{{elem}}}"
            arg = f"""(
                'All' = ANY(ARRAY[{param}]) OR 
                ({filters_table}.{elem} IS NULL AND 'NULL' = ANY(ARRAY[{param}])) OR 
                {filters_table}.{elem}::text = ANY(ARRAY[{param}])
            )"""

        return arg

    def _build_where_clause(self, filters: dict, condition: str, table: str, distinct: list):
        """Builds the WHERE clause from filters and condition. 
        """
        original_filters = copy.deepcopy(filters)   # make a copy of the original filters

        where_clauses = [] 

        if filters:
            filters_table_list = list(filters.keys())  

            # update table name with distinct condition
            for filters_table in filters_table_list:
                if distinct:
                    if filters_table in distinct:
                        index = distinct.index(filters_table)
                        filters[f"temp_table_{index}"] = filters.pop(f"{filters_table}")
                        filters_table = f"temp_table_{index}"
            
                for elem in filters[filters_table]:
                    arg = self._build_filter_argument(elem, filters_table)
                    where_clauses.append(arg)
        if condition:
            where_clauses.append(condition) 
        
        return "\n          AND ".join(where_clauses), original_filters

    def _build_join_clause(self, table: str, filters: dict, distinct: list) -> str:
        """Builds the LEFT JOIN command by using the foreign key.
        """
        join_clause = []

        # define the main table for LEFT JOIN
        main_table = "temp_table_0" if distinct else table

        # define the main prefix
        if table in PREFIX:
            main_prefix = PREFIX[table]
        else:
            main_prefix = table.split("_")[0]

        # Map table -> {main_prefix}_{postfix}
        filters_table_list = list(filters.keys())

        for filters_table in filters_table_list:
            # Skip self-join
            if filters_table == table or filters_table == main_table:
                continue
            
            # assign postfix for special cases
            if filters_table in POSTFIX:
                postfix = "no"
            else:
                postfix = "name"
            
            # Special case for dictionary groupby
            if distinct:
                if filters_table in distinct:
                    index = distinct.index(filters_table)     # get the index for temp_table_X
                    filters[f"temp_table_{index}"] = filters.pop(f"{filters_table}")    # update the filters table name in `filters`
                    filters_table = f"temp_table_{index}"   # update the filters table name in the join clause

            arg = f"LEFT JOIN {filters_table} ON {main_table}.{main_prefix}_{postfix} = {filters_table}.{main_prefix}_{postfix}"

            join_clause.append(arg)
        
        return "\n        ".join(join_clause)
    
    def _build_select_argument(self, table: str, elem: Any, TYPE="::text") -> str:
        """Builds the select argument for the SELECT clause.
        """
        # Single element
        if isinstance(elem, str):
            if elem.endswith("time"):
                return None
            elif elem.startswith("list"):
                arg = f"COALESCE(array_length({table}.{elem}::int[], 1), 0){TYPE}"
            else:
                arg = f"{table}.{elem}{TYPE}"

        # COALESCE Case: join multiple columns into 1 column
        elif isinstance(elem, list):
            select_clause = []
            for column in elem:
                if column.startswith("list"):
                    select_arg = f"COALESCE(array_length({table}.{column}::int[], 1), 0)"
                else:
                    select_arg = f"{table}.{column}{TYPE}"
                select_clause.append(select_arg)
            arg = f"COALESCE({', '.join(select_clause)}) as {elem[0]}"
        
        return arg


# ============================================================
# === Chart SQL Generator ====================================
# ============================================================

# -- Bar Chart --
class BarChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)

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
            table = "temp_table_0"

        for elem in groupby:
            arg = self._build_select_argument(table, elem)
            if arg:
                groupby_fields.append(arg)

        return " || '/' || ".join(groupby_fields)


# -- Histogram --
class HistogramGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)

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
            table = "temp_table_0"

        # check for the lenght of groupby:
        if len(groupby) > 1:
            raise ValueError("Histogram groupby list should have only 1 element.")
        
        # fetch the element from groupby
        elem = groupby[0]
        groupby_fields = self._build_select_argument(table, elem, TYPE="")

        return groupby_fields


# -- Timeseries --
class TimeseriesGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)
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
        # Check lenghth of groupby:
        if len(groupby) != 2:
            raise ValueError("Timeseries groupby list should have 2 elements.")
        
        # Check if groupby contains time:
        if not any(col in TIME_COLUMNS for col in groupby):
            raise ValueError("Timeseries groupby list should contain time column.")
        
        # assign time and element
        for col in groupby:
            if col in TIME_COLUMNS:
                time = col
            else:
                elem = col

        select_clause = []

        # Time
        time_arg = f"{table}.{time} AT TIME ZONE '{TIME_ZONE}' AS date"
        select_clause.append(time_arg)

        # Element
        if elem.startswith("list"):
            elem_arg = f"COALESCE(array_length({table}.{elem}::int[], 1), 0) AS {elem}"
        elif elem == "count":
            elem_arg = "COUNT(*) AS count"
        else:
            elem_arg = f"{table}.{elem} AS {elem}"
        select_clause.append(elem_arg)

        return ",\n            ".join(select_clause)
    
    def _build_orderby_clause(self, groupby: list) -> str:
        """Builds the ORDER BY clause from groupby.
        """
        # assign time and element
        for col in groupby:
            if col in TIME_COLUMNS:
                time = col
            else:
                elem = col

        clause = []

        groupby_arg = f"GROUP BY {time}" if elem == "count" else ""
        orderby_arg = f"ORDER BY {time}"

        clause.append(groupby_arg)
        clause.append(orderby_arg)

        return "\n             ".join(clause)


# -- Text Chart --
class TextChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        return None


# -- Stat Chart --
class StatChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)        
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)
        
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
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)

        sql = f"""
        {pre_clause}
        SELECT 
            {select_clause}
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """
        return sql.strip()

    def _build_select_clause(self, table: str, groupby: Any, distinct: bool) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []

        # Preprocess groupby into list of (table, column)
        pairs = []

        if isinstance(groupby, list):
            temp_table = "temp_table_0" if distinct else table
            for elem in groupby:
                cols = [elem]
                for col in cols:
                    pairs.append((temp_table, col))

        elif isinstance(groupby, dict):
            for i, (original_table, cols) in enumerate(groupby.items()):
                temp_table = f"temp_table_{i}" if distinct else original_table
                cols = cols if isinstance(cols, list) else [cols]
                for col in cols:
                    pairs.append((temp_table, col))

        # Now generate select arguments
        for table_name, col in pairs:
            arg = self._build_select_argument(table_name, col)
            if arg:
                groupby_fields.append(arg)

        return ",\n            ".join(groupby_fields)


# -- Gauge Chart --
class GaugeGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)

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
            arg = self._build_select_argument(table, elem, TYPE="")
            if arg:
                groupby_fields.append(arg)
        
        return ",\n               ".join(groupby_fields)


# -- Pie Chart --
class PieChartGenerator(BaseSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        where_clause, original_filters = self._build_where_clause(filters, condition, table, distinct)
        join_clause = self._build_join_clause(table, original_filters, distinct)

        sql = f"""
        {pre_clause}
        SELECT 
            COUNT(*) FILTER (WHERE shipped_datetime IS NULL) AS not_shipped,
            COUNT(*) FILTER (WHERE shipped_datetime IS NOT NULL) AS shipped
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """
        return sql.strip()


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
        "table": TableGenerator(),
        "gauge": GaugeGenerator(),
        "piechart": PieChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator