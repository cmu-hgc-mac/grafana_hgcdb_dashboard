# Grafana_HGCDB_Dashboard
This is a dashboard provided by [Grafana](https://github.com/grafana/grafana?tab=readme-ov-file) to monitor the HGC Postgres database. 

## Download Grafana
- [Get Grafana](https://grafana.com/get)

In `Get Grafana` page, choose `OSS` instead of `Cloud`. Download the Grafana by your operating system. The version I used is `v12.0.0`. Since I'm using MacOS, here is the command I used to download the Grafana for MacOS:
```
curl -k -O https://dl.grafana.com/enterprise/release/grafana-enterprise-12.0.0.darwin-amd64.tar.gz
tar -zxvf grafana-enterprise-12.0.0.darwin-amd64.tar.gz
```

The default port is `localhost:3000` and the default URL is http://localhost:3000.
- default Grafana username: `admin`
- defualt Grafana password: `admin`

## Getting Started
I have written scripts to start and stop Grafana. In order to use the scripts, it is necessary to make them executable.
Allow shell scripts to be executed:
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```

Start Grafana:
```
./start_grafana.sh
```

Run `main.py` to generate the dashboard:
```
python main.py
```

Finally to stop Grafana:
```
./stop_grafana.sh
```

## Files
- `a_EverythingNeedToChange`: This is the only folder that need to be changed with different settings if everything runs smoothly. 
    - `db_conn.yaml`: database connection file.
    - `gf_conn.yaml`: grafana connectoin file. `GF_SA_NAME`, `GF_SA_ID`, `GF_DATA_SOURCE_NAME`, and `GF_API_KEY` would be automatically updated after running `get_api.py`.
- `preSteps`: This is the folder that contains the scripts to prepare the database and tables.
    - `get_api.py`: Generate server API key and update `gf_conn.yaml`.
    - `add_dbsource.py`: Connect the PostegreSQL (hgcdb) as data source to Grafana.
- `dashboard_config.yaml`: This is the configuration file for all the dashboards and panels.
- `Create`: This is the folder that creates the database and tables from `dashboard_config.yaml` and the templates in the `Generate` folder.
    - `create_panels.py`: This script creates the panels (SQL) from `dashboard_config.yaml`.
    - `create_dashboard.py`: This script creates the dashboards (JSON) from `dashboard_config.yaml` and `panels.sql`.
- `Generate`: This is the folder that contains the scripts to genreate the dashboards (JSON) and panels (SQL)
    - `generate_panel_sql.py`: This script generates the SQL for differenty types of panels: Bar, Histograms...
    - `generate_dashboard_json.py`: This script generates the JSON for dashboards.
- `Scripts`: This is the folder that contains the scripts to start and stop Grafana.
    - `start_grafana.sh`: scrpit to start Grafana.
    - `stop_grafana.sh`: script to stop Grafana.
- `main.py`: the main file to run everything.

## Dashboards and Panels
- Components Inventory
    -
- Modules Assembly and Inventory
    -