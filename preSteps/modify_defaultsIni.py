import os
import yaml
import subprocess

"""
Modify the default.ini file in the conf directory to enable anonymous access to Grafana.
    *** Make Sure the path is correct *** --> In gf_conn.yaml
    By default the file should be inside the conf directory of grafana-v12.0.0
Grafana will be restarted after the modification.
"""

# Define path:
gf_conn_path = 'a_EverythingNeedToChange/gf_conn.yaml'

# Read the conn files:
with open(gf_conn_path, mode='r') as file:
    gf_conn = yaml.safe_load(file)

# load information
default_config_path = gf_conn['GF_defaults_PATH']
gf_port = gf_conn['GF_PORT']
gf_ip = gf_conn['GF_IP']

# exit the program if default.ini not found in conf directory
if not os.path.exists(default_config_path):
    print(f">> {default_config_path} not found. Exiting.")
    exit(1)

# load the file
with open(default_config_path, 'r') as file:
    lines = file.readlines()

# Initialize the condition
output = []
in_anonymous_block = False  
in_server_block = False

# start the loop
for line in lines:
    stripped = line.strip()

    # set condition
    if stripped.startswith('[auth.anonymous]'):
        in_anonymous_block = True   # Anonymous block starts
        output.append(line)
        continue
    
    if stripped.startswith('[server]'):
        in_server_block = True  # Server block starts
        output.append(line)
        continue

    # modify the lines
    if in_anonymous_block:
        if stripped.startswith('['):
            in_anonymous_block = False  # Anonymous block ends

        if stripped.startswith('enabled'):
            line = 'enabled = true\n'
        if stripped.startswith('device_limit'):
            line = 'device_limit = 1000\n'
        if stripped.startswith('hide_version'):
            line = 'hide_version = true\n'

    if in_server_block:
        if stripped.startswith('['):
            in_server_block = False # Server block ends
    
        if stripped.startswith('http_addr'):
            line = f'http_addr = 0.0.0.0\n'     # allow access from outside
        if stripped.startswith('http_port'):
            line = f'http_port = {gf_port}\n'
        if stripped.startswith('domain'):
            line = f'domain = {gf_ip}\n'
        if stripped.startswith('root_url'):
            line = f'root_url = http://{gf_ip}:{gf_port}\n'

    output.append(line)
    
# rewrite the file:
with open(default_config_path, 'w') as file:
    file.writelines(output)

# restart grafana:
subprocess.run(["bash", "./start_grafana.sh"])

# let user know: 
print(" >> defaults.ini file is modified ↙(`ヮ´ )↗, and Grafana is restarted for allowing anonymous access. ᕕ( ᐛ )ᕗ")