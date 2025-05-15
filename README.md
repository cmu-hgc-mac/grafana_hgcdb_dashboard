# Grafana_HGCDB_Dashboard
This is a dashboard provided by [Grafana](https://github.com/grafana/grafana?tab=readme-ov-file) to monitor the HGC Postgres database. 

## Download Grafana
- [Get Grafana](https://grafana.com/get) from 

In `Get Grafana` page, choose `OSS` instead of `Cloud`. Download the Grafana by your operating system. The version I used is `v12.0.0`.
Since I'm using MacOS, this is the command I used to download the Grafana for MacOS:
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
- `a_EverythingNeedToChange`: This is the only file that need to be changed with different settings. (`a` is added to be put in the top)
    - `db_conn.yaml`: database connection file.
    - `gf_conn.yaml`: grafana connectoin file. `GF_SA_NAME`, `GF_SA_ID`, `GF_DATA_SOURCE_NAME`, and `GF_API_KEY` would be automatically updated after running `get_api.py`.
- `dashboard_config.yaml`: The configuration file for the dashboards and panels.
- `get_api.py`: Generate server API key and update `gf_conn.yaml`.
- `add_dbsource.py`: Connect the PostegreSQL (hgcdb) as data source to Grafana.
- `create_panels.py`: generate the SQL queries for creating panels.
- `create_dashboard.py`: generate the dashboard JSON file.
- `start_grafana.sh`: scrpit to start Grafana.
- `stop_grafana.sh`: script to stop Grafana.
- `main.py`: the main file to run everything.

## Dashboards and Panels
- `Components Inventory`
    -
- `Modules Assembly and Inventory`
    -