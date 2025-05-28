from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type is "barchart".
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
        pass


# -- Generator for BarChart --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
        select_clause = self._build_select_clause(groupby)
        where_clause = self._build_where_clause(filters, condition)
        groupby_clause, case_statement = self._build_groupby_clause(override)

        sql = f"""
        SELECT 
            {select_clause} AS label,
            {case_statement}
            COUNT(*) AS count
        FROM {table}
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
        return " || '/' || ".join(groupby_fields)

    def _build_where_clause(self, filters: list, condition: str) -> str:
        """Builds the WHERE clause from filters and condition.
        """
        clauses = []
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

        if condition:
            clauses.append(condition)

        return " AND ".join(clauses)

    def _build_groupby_clause(self, override: str) -> tuple:
        """Builds the GROUP BY clause and optional CASE statement.
        """
        if override:
            name = override.split("_")[0]
            case_stmt = f"CASE WHEN {override} IS NULL THEN 'not {name}' ELSE '{name}' END AS {override},"
            groupby_clause = f"label, {override}"
        else:
            case_stmt = ""
            groupby_clause = "label"
        return groupby_clause, case_stmt


# -- Placeholder for LineChart (not implemented yet) --
class LineChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
        raise NotImplementedError("Line chart SQL generation is not implemented yet.")


# -- Create the SQL Generator Factory --
class ChartSQLFactory:
    _generators = {
        "barchart": BarChartGenerator(),
        "linechart": LineChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator
