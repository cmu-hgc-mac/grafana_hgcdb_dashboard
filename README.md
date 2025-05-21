# Grafana_HGCDB_Dashboard
This is a dashboard provided by [Grafana](https://github.com/grafana/grafana?tab=readme-ov-file) to monitor the HGC Postgres database. 

## Download Grafana
- [Get Grafana](https://grafana.com/get)

In `Get Grafana` page, choose `OSS` instead of `Cloud`. Download the Grafana by your operating system. The version I used is `v12.0.0`.  

The default port is `localhost:3000` and the default URL is http://localhost:3000.
- default Grafana username: `admin`
- defualt Grafana password: `admin`

## Getting Started
I have written scripts to start and stop Grafana. In `start_grafana.sh`, an enviornment is setted to avoid log in, wchih allow readers to view the dashboard direclty. I think this might be more convineient so I added it. In order to use the scripts, it is necessary to make them executable.  

### Before running the scripts, make sure to check the files in `a_EverythingNeedToChange` folder and change the necessary parameters.
  
Allow shell scripts to be executed:
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```
  
Start Grafana:
```
./start_grafana.sh
```
  
Run `main.py` to generate the dashboards to Grafana:
```
python main.py
```
If everything went smoothly, at this point the dashboard should be created successfully. But if very unfourtunate, due to different settings and conditions, there are some problems happened, I will try my best to encounter all the bugs I met and provide potential / my solution to the problem. But let's assume we have successfully created the dashboard.  
  
And finally, if needed, to stop Grafana:
```
./stop_grafana.sh
```

## Files and Folders Inventory:
- Files:
    - `start_grafana.sh`: start Grafana with the environment setted to avoid log in.
    - `stop_grafana.sh`: stop Grafana.
    - `main.py`: The only script that need to be run.
- Folders:
    - `a_EverythingNeedToChange`: contains all the files that need to be changed before running the scripts.
        - `db_conn.yaml`: contains the database connection information.
        - `gf_config.yaml`: contains the Grafana configuration information.
        - **PLEASE CHECK THESE FILES BEFORE RUNNING THE SCRIPTS.**
    - `config_folders`: contains all the configuration files for Grafana.
    - `Create`: contains all the files to create the dashboards.
    - `preSteps`: contains all the scripts to get the API_KEY and add the database_source.


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
> If there's output saying that you have grafana using the port: 3000, then you should be able to login to the Grafana dashboard by localhost:3000 directly. If you are not able to open localhost:3000, try to run `./stop_grafana.sh` and restart it.  

### Get API_KEY and Add Database_Source
1. Problem: Not able to get the token.
> Solution: Unfortunatly if you failed to get the token_key, you will have to create a new service account and get a new token due to the secuirty limitation of Grafana. Under `preSteps\get_api.py`, you can change the name in `sa_payload` and `token_payload` to reget a new token.