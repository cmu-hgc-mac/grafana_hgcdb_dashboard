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
I have written scripts to start and stop Grafana. In `start_grafana.sh`, an enviornment is setted to avoid log in, wchih allow readers to view the dashboard direclty. I think this might be more convineient so I added it. In order to use the scripts, it is necessary to make them executable.  
  
Allow shell scripts to be executed:
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```
  
Start Grafana:
```
cd Scripts
./start_grafana.sh
```
  
Run `main.py` to generate the dashboard:
```
python main.py
```
If everything went smoothly, at this point the dashboard should be created successfully. But if very unfourtunate, due to different settings and conditions, there are some problems happened, I will try my best to encounter all the bugs I met and provide potential / my solution to the problem. But let's assume we have successfully created the dashboard.  
  
And finally, stop Grafana:
```
cd Scripts
./stop_grafana.sh
```
  
## Files Introductory
- `a_EverythingNeedToChange`: This is the only folder that need to be changed with different settings if everything runs smoothly. 
    - `db_conn.yaml`: database connection file.
    - `gf_conn.yaml`: grafana connectoin file. `GF_SA_NAME`, `GF_SA_ID`, `GF_DATA_SOURCE_NAME`, and `GF_API_KEY` would be automatically updated after running `get_api.py`.  
- `preSteps`: This is the folder that contains the scripts to prepare the database and tables.
    - `get_api.py`: Generate server API key and update `gf_conn.yaml`.
    - `add_dbsource.py`: Connect the PostegreSQL (hgcdb) as data source to Grafana.  
- `Create`: This is the folder that creates the database and tables from `dashboard_config.yaml` and the templates in the `Generate` folder.
    - `create_panels.py`: This script creates the panels (SQL) from `dashboard_config.yaml`.
    - `create_dashboard.py`: This script creates the dashboards (JSON) from `dashboard_config.yaml` and `panels.sql`.  
- `Generate`: This is the folder that contains the scripts to genreate the dashboards (JSON) and panels (SQL)
    - `generate_panel_sql.py`: This script generates the SQL for differenty types of panels: Bar, Histograms...
    - `generate_dashboard_json.py`: This script generates the JSON for dashboards.  
- `Scripts`: This is the folder that contains the scripts to start and stop Grafana.
    - `start_grafana.sh`: scrpit to start Grafana.
    - `stop_grafana.sh`: script to stop Grafana.  
- `dashboard_config.yaml`: This is the configuration file for all the dashboards and panels.  
- `main.py`: the main file to run everything: `get_api.py`, `add_dbsource.py`, and finally upload all the dashboards' JSON files to Grafana.  


## Dashboards and Panels
- Components Inventory
    -
- Modules Assembly and Inventory
    -
- 工事中...
  
## Potential Bugs
### Start Grafana
1. Problem: `Grafana failed to start.` at the first run. 
> Solution: check what is in the default port: 3000
```
lsof -i -P -n | grep grafana
```
If there's output saying that you have grafana using the port, then you should be able to login to the Grafana dashboard by localhost:3000 directly. It that doesn't work, try to run `./stop_grafana.sh` and then restart it.  

### Get API_KEY and Add Database_Source
1. Problem: Not able to get the token.
> Solution: Unfortunatly if you failed to get the token_key, you will have to create a new service account and get a new token due to the secuirty limitation of Grafana. Under `preSteps\get_api.py`, you can change the name in `sa_payload` and `token_payload` to reget a new token.