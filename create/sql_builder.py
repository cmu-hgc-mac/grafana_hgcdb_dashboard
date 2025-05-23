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


# -- Create a SQL Generator Factory --
class ChartSQLFactory:
    _generators = {
        "barchart" = BarChartGenerator()
    }

    @classmethod
    def get_generator(cls, chart_type: str) -> ChartSQLGenerator:
        generator = cls._generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        return generator


# -- Generator for each chart_type --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: str) -> str:
        # Check `condition`
        if condition:
            where_condition = f"WHERE {condition}"
        else:
            where_condition = ""

        # generate the sql command
        panel_sql = f"""
        SELECT 
            {groupby},
        COUNT(*) AS free_count
        FROM {table}
        {where_condition}
        GROUP BY {groupby}
        ORDER BY free_count DESC;
        """
        
        return panel_sql

class LineChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: str) -> str:
        pass