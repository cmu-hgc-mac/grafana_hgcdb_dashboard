import yaml

db_conn = { 
    # Setting for hgcdb database
        # Should be the same as local database settings

    'dbname': 'hgcdb',
    'port': '5432',   
    'db_hostname': 'localhost',  # 'localhost' 
    'institution_abbr': 'CMU',  # update this: CMU, IHEP, NTU, TTU, TIFR, UCSB

    'user': 'viewer',  # recommended
    'password': ''  # your password
}

gf_conn = {
    # Setting for Grafana

    # Things must be changed:
    'GF_PORT': '3000', # default 
    'GF_IP': '127.0.0.1', # default
    'GF_defaults_PATH': '/Users/******/grafana-v12.0.0/conf/defaults.ini', 
        # by default, 'defaults.ini' should be in the conf directory of Grafana (for MacOs)
        # For Linux, the path should be '/etc/grafana/grafana.ini'

    # Things might be changed:
    'GF_USER': 'admin', # default
    'GF_PASS': 'admin', # default
    'GF_URL': "http://127.0.0.1:3000", # default -> only change your port if you changed GF_PORT
        # the url for login Grafana and uploading dashboards

    # Things will be auto-updated:
    'GF_SA_NAME': "",
    'GF_SA_ID': "",
    'GF_DATA_SOURCE_NAME': "",
    'GF_API_KEY': "",
    'GF_DATA_SOURCE_UID': "",
    'GF_RUN_TIMES': 0 # this will be updated automatically according to the run time of the `main.py` script
}



import os

# create a directory for the connection files
folder_path = "./a_EverythingNeedToChange"
os.makedirs(folder_path, exist_ok=True)    # Create the folder if it doesn't exist

# create a file for the database connection
db_conn_path = os.path.join(folder_path, "db_conn.yaml")
with open(db_conn_path, "w") as file:
    yaml.dump(db_conn, file)

# create a file for the Grafana connection
gf_conn_path = os.path.join(folder_path, "gf_conn.yaml")
with open(gf_conn_path, "w") as file:
    yaml.dump(gf_conn, file)