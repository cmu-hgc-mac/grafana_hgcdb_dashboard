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


# -- Generator for each chart_type --
class BarChartGenerator(ChartSQLGenerator):
    def generate_sql(self, table: str, condition: str, groupby: list, filters: list, override: str) -> str:
        # define the select clause
        groupby_tmp = []
        for elem in groupby:
            if elem.endswith("time"):
                name = elem.split("_")[0]
                groupby_tmp.append(f"CASE WHEN {elem} IS NULL THEN 'not {name}' ELSE '{name}' END")
            else:
                groupby_tmp.append(elem)

        select_clause = " || '/' || ".join(groupby_tmp)

        # define WHERE query
        where_clause = []

        for elem in filters:
            if elem == "status":
                param = "${status}"
                arg = f"""('All' = ANY(ARRAY[{param}]) OR 
                        (shipped_datetime IS NULL AND 'not shipped' = ANY(ARRAY[{param}])) OR
                        (shipped_datetime IS NOT NULL AND 'shipped' = ANY(ARRAY[{param}])))"""
                where_clause.append(arg)
            else:
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
            case_condition = f"CASE WHEN {override} IS NULL THEN 'not {name}' ELSE '{name}' END AS {override},"
            groupby_clause = f"label, {override}"
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
