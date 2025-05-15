## Getting Started

### Download Grafana
- [Get Grafana](https://grafana.com/get)
    - Select `OSS`
    - Download Grafana based on your operating system
    - Version: 12.0.0

For macOS (since I'm using macOS):
```
curl -k -O https://dl.grafana.com/enterprise/release/grafana-enterprise-12.0.0.darwin-amd64.tar.gz
tar -zxvf grafana-enterprise-12.0.0.darwin-amd64.tar.gz
```

Allow shell scripts to be executed:
```
chmod +x start_grafana.sh
chmod +x stop_grafana.sh
```

Run `main.py` to generate the dashboard:
```
python main.py
```

### Start Grafana
run `./start_grafana.sh` to start Grafana.

### Stop Grafana
run `./stop_grafana.sh` to stop Grafana.

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