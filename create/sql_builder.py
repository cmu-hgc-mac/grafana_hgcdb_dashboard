from abc import ABC, abstractmethod

"""
This file defines the abstract class ChartSQLGenerator and the factory ChartSQLFactory.
    - The current available chart type is "barchart".
"""

# -- Define the abstract class --
class ChartSQLGenerator(ABC):
    @abstractmethod
    def generate_sql(self, table: str, condition: str, groupby: str) -> str:
        pass


# -- Generator for each chart_type --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, override: str) -> str:
        # define the select clause
        select_clause = " || '-' || ".join(groupby)

        # whatever in WHERE query
        where_clause = []

        for elem in groupby:
            param = f"${{{elem}}}"
            arg = f"('All' = ANY(ARRAY[{param}]) OR {elem}::text = ANY(ARRAY[{param}]))"
            where_clause.append(arg)

        # check condition
        if condition:
            where_condition = f"{' AND '.join(where_clause)} AND {condition}"
        else:
            where_condition = f"{' AND '.join(where_clause)}"

        # check status:
        if override:
            name = override.split("_")[0]
            case_condition = f"CASE WHEN {override} IS NULL THEN 'not {name}' ELSE '{name}' END AS status,"
            groupby_clause = "label, status"
        else:
            case_condition = ""
            groupby_clause = "label"
        

        # generate the sql command
        panel_sql = f"""
        SELECT 
        {select_clause} AS label,
        {case_condition}
        COUNT(*) AS count
        FROM {table}
        WHERE {where_condition}
        GROUP BY {groupby_clause}
        ORDER BY count DESC;
        """
        
        return panel_sql

class LineChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: str) -> str:
        pass



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
