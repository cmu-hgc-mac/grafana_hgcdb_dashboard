from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type:
        - "barchart"
        - "histogram"
        - "timeseries"
        - "text"
        - "stat"
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        pass


# -- Generator for BarChart --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause = self._build_where_clause(filters, condition, filters_table, distinct)
        join_clause = self._build_join_clause(table, filters_table)

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
    
    def _build_pre_clause(self, table: str, distinct: bool) -> str:
        """Builds the pre-SELECT clause for histogram. 
           - If distinct is True, it will select the distinct modules.
           - Hard Coded Version: Only for module_qc_summary table.
        """
        if distinct:
            target_table = "temp_table"

            if table == "module_qc_summary":
                pre_clause = """WITH temp_table AS (SELECT DISTINCT ON (module_no) * FROM module_qc_summary ORDER BY module_no, mod_qc_no DESC)"""
        else:
            target_table = table
            pre_clause = ""
        
        return pre_clause, target_table

    def _build_select_clause(self, table: str, groupby: list, distinct: bool) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []

        if distinct:
            table = "temp_table"

        for elem in groupby:
            if elem.endswith("time"):
                continue
            elif elem.startswith("list"):
                groupby_fields.append(f"COALESCE(array_length({table}.{elem}::int[], 1), 0)::text")
            else:
                groupby_fields.append(f"{table}.{elem}::text")
        return " || '/' || ".join(groupby_fields)

    def _build_where_clause(self, filters: list, condition: str, filters_table: str, distinct: bool) -> str:
        """Builds the WHERE clause from filters and condition. 
        """
        clauses = []

        if distinct:
            filters_table = "temp_table"

        for elem in filters:
            if elem == "status":
                param = "${status}"
                arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                        (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                        (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
            elif elem == "assembled" or elem.endswith("time"):
                arg = f"$__timeFilter({filters_table}.{elem})"
            else:
                param = f"${{{elem}}}"
                arg = f"('All' = ANY(ARRAY[{param}]) OR {filters_table}.{elem}::text = ANY(ARRAY[{param}]))"
            clauses.append(arg)

        if condition:
            clauses.append(condition)

        return " AND ".join(clauses)
    
    def _build_join_clause(self, table: str, filters_table: str) -> str:
        """Builds the JOIN command by using the foriegn key.
        """
        if table == filters_table:
            join_clause = ""
        else:
            elem = table.split("_")[0]
            join_clause = f"JOIN {filters_table} ON {table}.{elem}_no = {filters_table}.{elem}_no"
        
        return join_clause


# -- Generator for Histogram --
class HistogramGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)
        select_clause = self._build_select_clause(table, groupby, distinct)
        where_clause = self._build_where_clause(filters, condition, filters_table, distinct)
        join_clause = self._build_join_clause(table, filters_table, distinct)

        sql = f"""
        {pre_clause}
        SELECT {select_clause}
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """

        return sql

    def _build_pre_clause(self, table: str, distinct: bool) -> str:
        """Builds the pre-SELECT clause for histogram. 
           - If distinct is True, it will select the distinct modules.
           - Hard Coded Version: Only for module_qc_summary table.
        """
        if distinct:
            target_table = "temp_table"

            if table == "module_qc_summary":
                pre_clause = """WITH temp_table AS (SELECT DISTINCT ON (module_no) * FROM module_qc_summary ORDER BY module_no, mod_qc_no DESC)"""
        else:
            target_table = table
            pre_clause = ""
        
        return pre_clause, target_table
    
    def _build_select_clause(self, table: str, groupby: list, distinct: bool) -> str:
        """Builds the SELECT clause from groupby. 
           - For histogram, there should only be 1 element in groupby.
        """
        if distinct:
            table = "temp_table"
        
        # check for the groupby length:
        num_groupby = len(groupby)

        if num_groupby == 1:
            elem = groupby[0]
            if elem.startswith("list"):
                select_clause = f"COALESCE(array_length({table}.{elem}::int[], 1), 0) AS {elem}"
            else:
                select_clause = f"{table}.{elem} AS {elem}"

        elif num_groupby == 2: 
            select_clause = []
            for elem in groupby:
                if elem.startswith("list"):
                    select_arg = f"COALESCE(array_length({table}.{elem}::int[], 1), 0)"
                else:
                    select_arg = f"{table}.{elem}"
                select_clause.append(select_arg)
            select_clause = f"COALESCE({", ".join(select_clause)}) as {groupby[0]}"
        else:
            raise ValueError("The groupby list has not correct length.")
            # return None

        return select_clause

    def _build_where_clause(self, filters: list, condition: str, filters_table: str, distinct: bool) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []

        if distinct:
            # table = "temp_table"
            filters_table = "temp_table"

        for elem in filters:
            if elem == "status":
                param = "${status}"
                arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                        (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                        (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
            else:
                param = f"${{{elem}}}"
                arg = f"('All' = ANY(ARRAY[{param}]) OR {filters_table}.{elem}::text = ANY(ARRAY[{param}]))"
            clauses.append(arg)

        if condition:
            clauses.append(condition)

        return " AND ".join(clauses)
    
    def _build_join_clause(self, table: str, filters_table: str, distinct: bool) -> str:
        """Builds the JOIN command by using the foriegn key.
        """
        if table == filters_table:
            join_clause = ""
        else:
            elem = table.split("_")[0]
            join_clause = f"JOIN {filters_table} ON {table}.{elem}_no = {filters_table}.{elem}_no"
        
        return join_clause


# -- Generator for Timeseries --
class TimeseriesGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause = self._build_where_clause(filters, condition, filters_table)
        join_clause = self._build_join_clause(table, filters_table)
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

    def _build_where_clause(self, filters: list, condition: str, filters_table: str) -> str:
        """Builds the WHERE clause from filters and condition. 
        """
        clauses = []
        for elem in filters:
            if elem == "status":
                param = "${status}"
                arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                        (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                        (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
            elif elem == "assembled" or elem.endswith("time") or elem == "log_timestamp":
                arg = f"$__timeFilter({filters_table}.{elem})"
            else:
                param = f"${{{elem}}}"
                arg = f"('All' = ANY(ARRAY[{param}]) OR {filters_table}.{elem}::text = ANY(ARRAY[{param}]))"
            clauses.append(arg)

        if condition:
            clauses.append(condition)

        return " AND ".join(clauses)
    
    def _build_join_clause(self, table: str, filters_table: str) -> str:
        """Builds the JOIN command by using the foriegn key.
        """
        if table == filters_table:
            join_clause = ""
        else:
            elem = table.split("_")[0]
            join_clause = f"JOIN {filters_table} ON {table}.{elem}_no = {filters_table}.{elem}_no"
        
        return join_clause
    
    def _build_orderby_clause(self, groupby: list) -> str:
        """Builds the ORDER BY clause from groupby.
        """
        time = groupby[0]
        elem = groupby[1]
        clause = []

        if elem == "count":
            groupby_arg = f"GROUP BY {time}"
        else: 
            groupby_arg = ""
        
        orderby_arg = f"ORDER BY {time};"

        clause.append(groupby_arg)
        clause.append(orderby_arg)

        return "\n".join(clause)


# -- Generator for Text Chart --
class TextChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        return None


# -- Generator for Stat Chart --
class StatChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        pre_clause, target_table = self._build_pre_clause(table, distinct)        
        where_clause = self._build_where_clause(filters, condition, filters_table, distinct)
        join_clause = self._build_join_clause(table, filters_table, distinct)        
        
        sql = f"""
        {pre_clause}
        SELECT COUNT(*) AS count
        FROM {target_table}
        {join_clause}
        WHERE {where_clause}
        """

        return sql.strip()

    def _build_pre_clause(self, table: str, distinct: bool) -> str:
        """Builds the pre-SELECT clause for histogram. 
           - If distinct is True, it will select the distinct modules.
           - Hard Coded Version: Only for module_qc_summary table.
        """
        if distinct:
            target_table = "temp_table"

            if table == "module_qc_summary":
                pre_clause = """WITH temp_table AS (SELECT DISTINCT ON (module_no) * FROM module_qc_summary ORDER BY module_no, mod_qc_no DESC)"""
        else:
            target_table = table
            pre_clause = ""
        
        return pre_clause, target_table

    def _build_where_clause(self, filters: list, condition: str, filters_table: str, distinct: bool) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []

        if distinct:
            # table = "temp_table"
            filters_table = "temp_table"

        for elem in filters:
            if elem == "status":
                param = "${status}"
                arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                        (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                        (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
            else:
                param = f"${{{elem}}}"
                arg = f"('All' = ANY(ARRAY[{param}]) OR {filters_table}.{elem}::text = ANY(ARRAY[{param}]))"
            clauses.append(arg)

        if condition:
            clauses.append(condition)

        return " AND ".join(clauses)
    
    def _build_join_clause(self, table: str, filters_table: str, distinct: bool) -> str:
        """Builds the JOIN command by using the foriegn key.
        """
        if table == filters_table:
            join_clause = ""
        else:
            elem = table.split("_")[0]
            join_clause = f"JOIN {filters_table} ON {table}.{elem}_no = {filters_table}.{elem}_no"
        
        return join_clause


# -- Create the SQL Generator Factory --
class ChartSQLFactory:
    _generators = {
        "barchart": BarChartGenerator(),
        "histogram": HistogramGenerator(),
        "timeseries": TimeseriesGenerator(),
        "text": TextChartGenerator(),
        "stat": StatChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator
