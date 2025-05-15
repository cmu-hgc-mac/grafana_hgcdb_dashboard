def create_Bar(table, condition, groupby, filters):
    # SQL qurey for selection groups:
    groupby_sql = ", ".join(groupby)

    # SQL qurey for filters:
    filter_conditions = [f"('${f}' = 'All' OR {f} = ANY(string_to_array('${f}', ',')))" for f in filters]
    filter_sql = "\n        AND".join(filter_conditions)

    if condition:
        where_condition = f"{filter_sql}\n        AND {condition}"
    else:
        where_condition = filter_sql

    panel_sql = f"""
    SELECT 
        {groupby_sql},
    COUNT(*) AS free_count
    FROM {table}
    WHERE {where_condition}
    GROUP BY {groupby_sql}
    ORDER BY free_count DESC;
    """
    
    return panel_sql

# def create_Hist(table):