import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tool.helper import *

"""
Add the PostgreSQL data source to Grafana as default.
"""

# reload info
gf_conn.reload()

datasource_name = gf_conn.get('GF_DATA_SOURCE_NAME')
datasource_uid  = gf_conn.get('GF_DATA_SOURCE_UID')

client.add_postgres_datasource(datasource_name, datasource_uid, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)