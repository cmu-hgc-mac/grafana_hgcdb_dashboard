from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type:
        - "barchart"
        - "histogram"
        - "timeseries"
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        pass


# -- Generator for BarChart --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, distinct: bool) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause = self._build_where_clause(filters, condition, filters_table)
        join_clause = self._build_join_clause(table, filters_table)

        sql = f"""
        SELECT 
            {select_clause} AS label,
            COUNT(*) AS count
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        GROUP BY label
        ORDER BY count DESC;
        """
        return sql.strip()

    def _build_select_clause(self, table: str, groupby: list) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []
        for elem in groupby:
            if elem.endswith("time"):
                continue
            elif elem.startswith("list"):
                groupby_fields.append(f"COALESCE(array_length({table}.{elem}::int[], 1), 0)")
            else:
                groupby_fields.append(f"{table}.{elem}")
        return " || '/' || ".join(groupby_fields)

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
        where_clause = self._build_where_clause(filters, condition, table, filters_table, distinct)
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
        elem = groupby[0]

        if distinct:
            table = "temp_table"

        if elem.startswith("list"):
            select_clause = f"COALESCE(array_length({table}.{elem}::int[], 1), 0)"
        else:
            select_clause = f"{table}.{groupby[0]}"
        
        return select_clause

    def _build_where_clause(self, filters: list, condition: str, table: str, filters_table: str, distinct: bool) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []

        if distinct:
            table = "temp_table"
            filters_table = "temp_table"

        if table == filters_table: 
            for elem in filters:
                if elem == "status":
                    param = "${status}"
                    arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                            (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                            (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
                else:
                    param = f"${{{elem}}}"
                    arg = f"('All' = ANY(ARRAY[{param}]) OR {elem}::text = ANY(ARRAY[{param}]))"
                clauses.append(arg)
        else:
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

        sql = f"""
        SELECT 
            {select_clause} AS date,
            COUNT(*) AS count
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        GROUP BY date
        ORDER BY date;
        """
        return sql.strip()

    def _build_select_clause(self, table: str, groupby: list) -> str:
        """Builds the SELECT clause from groupby.                                                                                                                                                                      - For histogram, there should only be 1 element in groupby.                                                                                                                                            """
        elem = groupby[0]

        if elem.startswith("list"):
            select_clause = f"COALESCE(array_length({table}.{elem}::int[], 1), 0)"
        else:
            select_clause = f"{table}.{groupby[0]}"

        return select_clause

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


# -- Placeholder for LineChart (not implemented yet) --
class LineChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str) -> str:
        raise NotImplementedError("Line chart SQL generation is not implemented yet.")


# -- Create the SQL Generator Factory --
class ChartSQLFactory:
    _generators = {
        "barchart": BarChartGenerator(),
        "histogram": HistogramGenerator(),
        "timeseries": TimeseriesGenerator(),
        "linechart": LineChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator
