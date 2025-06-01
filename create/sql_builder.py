from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type:
        - "barchart"
        - "histogram"
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str) -> str:
        pass


# -- Generator for BarChart --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str) -> str:
        select_clause = self._build_select_clause(groupby)
        where_clause = self._build_where_clause(filters, condition, table, filters_table)
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

    def _build_select_clause(self, groupby: list) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []
        for elem in groupby:
            if elem.endswith("time"):
                continue
            else:
                groupby_fields.append(elem)
        return " || '/' || ".join(groupby_fields)

    def _build_where_clause(self, filters: list, condition: str, table: str, filters_table: str) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []
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
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause = self._build_where_clause(filters, condition, table, filters_table)
        join_clause = self._build_join_clause(table, filters_table)

        sql = f"""
        SELECT {select_clause}
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        """

        return sql
    
    def _build_select_clause(self, table: str, groupby: list) -> str:
        """Builds the SELECT clause from groupby. 
           - For histogram, there should only be 1 element in groupby.
        """
        select_clause = groupby[0]

        return select_clause

    def _build_where_clause(self, filters: list, condition: str, table: str, filters_table: str) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []
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
    
    def _build_join_clause(self, table: str, filters_table: str) -> str:
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
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str) -> str:
        select_clause = self._build_select_clause(groupby)
        where_clause = self._build_where_clause(filters, condition, table, filters_table)
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

    def _build_select_clause(self, groupby: list) -> str:
        """Builds the SELECT clause by joining all groupby fields.
           - For timeseries, there should only be 1 element in groupby.
        """
        select_clause = f"{groupby[0]}::date"

        return select_clause

    def _build_where_clause(self, filters: list, condition: str, table: str, filters_table: str) -> str:
        """Builds the WHERE clause from filters and condition. 
           - Minor changes for filters from a different table.
        """
        clauses = []
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
