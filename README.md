# Grafana_HGCDB_Dashboard ε=ε=(<ゝω・)☆
This is a dashboard provided by [Grafana](https://github.com/grafana/grafana?tab=readme-ov-file) to monitor the HGC Postgres database. 

## Run Steps
Since I really afraid of setting up enviorment, (It is a realllll nightmare(／‵口′)／~ ╧╧) I tried my very best to make the scripts as simple as possible. ε=ε=(ノ≧∇≦)ノ  
I know that my scripts by no chance can be perfect, but this is the best I can have at this moment! (σ`∀´)♡ A more detailed explanation on how the scripts work can be found in the later section.
  
And.... Here are the steps to set up the Grafana_HGCDB_Dashboard: (;´ヮ`)7
1. Download Grafana.
2. *Check the files in `a_EverythingNeedToChange` folder and change the necessary parameters.*
3. Allow shell scripts to be executed.
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```
4. Run `start_grafana.sh` to start Grafana.
```
./start_grafana.sh
```
5. Run `main.py` to generate the dashboards to Grafana.
```
python main.py
```
6. All done! (๑•̀ㅂ•́)و✧
7. And lastly, if needed, to stop Grafana:
```
./stop_grafana.sh
```

## Download Grafana
- [Get Grafana](https://grafana.com/get)

In `Get Grafana` page, choose `OSS` instead of `Cloud`. Download the Grafana by your operating system. The version I used is `v12.0.0`.  

The default port is `localhost:3000` and the default URL is http://localhost:3000.
- default Grafana username: `admin`
- defualt Grafana password: `admin`


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


## Folders, Dashboards and Panels
- Components Inventory
    - Free Baseplates: bp_material, resolution, geometry
    - Free Sensors: thicknesses, resolutions, geometry
    - Free Hexaboards: roc_version, resolution, geometry
- 工事中...
  

## How the Scripts Work σ( ᑒ )
The "normal" way to generate a Grafana dashboard is to use the Grafana UI. However, since I am so bad at using the UI, and I `NOTICED` ～～very good attention～～ that each dashboard is actually a json file. I start to wonder if I can generate the json files by code, and upload them to Grafana... Then it is possible for me to generate the dashboards without interacting with the UI! ╮(￣▽￣)╭  
And luckly.... I can! (๑•̀ㅂ•́)و✧  
What's inside the folders will be explained below. The preSteps folder will only be runned for once, as there's a parameter in `gf_conn.yaml` counting how many times the `main.py` has been runned. Only the first run would run the `preSteps`:  
- `preSteps` folder:  
    - `get_api_key.py` is the script to create a service account and get the API_KEY for Grafana. The API_KEY will be stored in the `gf_conn.yaml` file for future usages: add datasource, create folders, and upload dashboards.
    - `add_datasource.py` is the script to add the database_source to Grafana. The database_source is called from the parameters in the `db_conn.yaml` file. -> *Modify the `db_conn.yaml` file before running the `main.py`. (・_ゝ・)*
    - `modify_defaulsIni.py` is the script to modify the default.ini file in the Grafana configuration folder. The modifications are mainly focusing on `auth.anonymous` and `server`. The `auth.anonymous` is set to `true` to allow anonymous access to the Grafana dashboard. The `server` is set to allow access from any IP address connection to the Grafana port -> hence modification on device's firewall is needed. I know this is not a secure connection, in the future we can use `Nginx` as a reverse proxy. But I'm having problem downloading `Nginx` on my device (╯°□°)╯︵ ┻━┻. I will figure it out, I will figure it out, I will figure it out.( `д´)σ -> *And also please MODIFY the `gf_conn.yaml` file before running the `main.py`. ( `д´)9*
- `Create` folder:
    - `create_dashboards.py` and `create_folders.py` are the scripts to do whatever is listed in the titles. There's nothing much to talk here. (´д`)
    -  `generate.py` is the script to generate almost everything. It is very very very long and I don't recommand any one talk a look at it, it is soooooooo looooooooong (;´Д`) and there's nothing I can do to make it shorter. It is soooo long and soooo tedious and I'm soooo sad I can't do anything with it. ( ;`д´; )
    - `sql_builder.py` is the script to build the SQL queries for each panel. I used `ABC` - Abstract Base Class - to build the SQL queries for different chart types. For the future developers who want to add more chart types, you can simply add a new class and implement the chart types in the `ChartSQLFactory` class. (´ε｀ ) The function are called only in: `generate.py`: line 343 - line 353 to generate the SQL queries for each panel.
    - And also, here is the link to [JSON MODEL](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/) for Grafana dashboards. I hope this is helpful! (*´ω`*)
  
That's all I would like to say about the scripts for now. If you have any questions, please feel free to ask me! (σ`∀´)
  
* Thank you very much for reading this! (๑•̀ㅂ•́)و✧ *  


## Potential Bugs
### Start Grafana
1. Problem: `Grafana failed to start.` at the first run. 
> Solution: check what is in the default port: 3000
```
lsof -i -P -n | grep grafana
```
> If there's output saying that you have grafana using the port: 3000, then you should be able to login to the Grafana dashboard by localhost:3000 directly. If you are not able to open localhost:3000, try to run `./start_grafana.sh` again, and the problem shoule be resolved.

### Get API_KEY and Add Database_Source
1. Problem: Not able to get the token.
> Solution: Unfortunatly if you failed to get the token_key, you will have to create a new service account and get a new token due to the secuirty limitation of Grafana. Under `preSteps\get_api.py`, you can change the name in `sa_payload` and `token_payload` to reget a new token.