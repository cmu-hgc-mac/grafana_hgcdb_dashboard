import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helper import *

"""
Add the PostgreSQL data source to Grafana as default.
"""

# reload info
gf_conn.reload()

datasource_name = gf_conn.get('GF_DATA_SOURCE_NAME')
datasource_uid  = gf_conn.get('GF_DATA_SOURCE_UID')

client.add_postgres_datasource(datasource_name, datasource_uid, db_host, db_port, db_name, db_user, db_password)