from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type is "barchart".
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, override: str) -> str:
        pass


# -- Generator for BarChart --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, override: str) -> str:
        select_clause = self._build_select_clause(groupby)
        where_clause = self._build_where_clause(filters, condition, table, filters_table)
        join_clause = self._build_join_clause(table, filters_table)
        groupby_clause, case_statement = self._build_groupby_clause(override)

        sql = f"""
        SELECT 
            {select_clause} AS label,
            {case_statement}
            COUNT(*) AS count
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        GROUP BY {groupby_clause}
        ORDER BY count DESC;
        """
        return sql.strip()

    def _build_select_clause(self, groupby: list) -> str:
        """Builds the SELECT clause by joining all groupby fields.
        """
        groupby_fields = []
        for elem in groupby:
            if elem.endswith("time"):
                name = elem.split("_")[0]
                groupby_fields.append(f"CASE WHEN {elem} IS NULL THEN 'not {name}' ELSE '{name}' END")
            else:
                groupby_fields.append(elem)
        return " || '-' || ".join(groupby_fields)

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
            join_clause = f"JOIN {filters_table} ON {table}.module_no = {filters_table}.module_no"
        
        return join_clause

    def _build_groupby_clause(self, override: str) -> tuple:
        """Builds the GROUP BY clause and optional CASE statement.
        """
        if override:
            name = override.split("_")[0]
            case_stmt = f"CASE WHEN {override} IS NULL THEN 'not {name}' ELSE '{name}' END AS status,"
            groupby_clause = f"label, status"
        else:
            case_stmt = ""
            groupby_clause = "label"

        return groupby_clause, case_stmt


# -- Generator for Histogram --
class HistogramGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, filters_table: str, override: str) -> str:
        select_clause = self._build_select_clause(table, groupby)
        where_clause = self._build_where_clause(filters, condition, table, filters_table)
        join_clause = self._build_join_clause(table, filters_table)

        sql = f"""
        SELECT {select_clause} AS bin,
        COUNT(*) AS count
        FROM {table}
        {join_clause}
        WHERE {where_clause}
        GROUP BY bin
        ORDER BY bin;
        """

        return sql
    
    def _build_select_clause(self, table: str, groupby: list) -> str:
        """Builds the SELECT clause from groupby. 
           - For histogram, there should only be 1 element in groupby.
        """
        target_column = groupby[0]
        select_clause = f"width_bucket({table}.{target_column}, 0, 500, 10)"

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
            join_clause = f"JOIN {filters_table} ON {table}.module_no = {filters_table}.module_no"
        
        return join_clause


# -- Placeholder for LineChart (not implemented yet) --
class LineChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
        raise NotImplementedError("Line chart SQL generation is not implemented yet.")


# -- Create the SQL Generator Factory --
class ChartSQLFactory:
    _generators = {
        "barchart": BarChartGenerator(),
        "histogram": HistogramGenerator(),
        "linechart": LineChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator
