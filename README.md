## Getting Started

### Download Grafana
- [Get Grafana](https://grafana.com/get) from [Grafana](https://github.com/grafana/grafana?tab=readme-ov-file)

In `Get Grafana` page, choose `OSS` instead of `Cloud`. Download the Grafana with your operating system. The version I used is `v12.0.0`.
Since I'm using MacOS, this is the command I used to download the Grafana:
```
curl -k -O https://dl.grafana.com/enterprise/release/grafana-enterprise-12.0.0.darwin-amd64.tar.gz
tar -zxvf grafana-enterprise-12.0.0.darwin-amd64.tar.gz
```

The default port is `localhost:3000` and the default URL is `http://localhost:3000`.
- Default username: `admin`
- Defualt password: `admin`

I have written scripts to start and stop Grafana. In order to use the scripts, it is necessary to make them executable.
Allow shell scripts to be executed:
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```

Start Grafana
```
./start_grafana.sh
```

Run `main.py` to generate the dashboard:
```
python main.py
```

Finally to stop Grafana
```
./stop_grafana.sh
```

## File introduction
- `a_EverythingNeedToChange`: This is the only file that need to be changed with different settings.
    - `db_conn.yaml`: database connection file.
    - `gf_conn.yaml`: grafana connectoin file. Some settings would be automatically updated affer running `get_api.py`.
- `get_api.py`: Generate server API key and update `gf_conn.yaml`.
- `add_dbsource.py`: Connect the PostegreSQL database to Grafana.
- `main.py`: the main file to generate the dashboard.
- `create_panels.py`: generate the SQL queries for creating panels.
- `create_dashboard.py`: generate the dashboard JSON file.
- `start_grafana.sh`: scrpit to start Grafana.
- `stop_grafana.sh`: script to stop Grafana.