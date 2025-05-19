import os
import yaml
import subprocess

"""
This script modifies the default.ini file in the conf directory to enable anonymous access to Grafana.
    *** Make Sure the path is correct ***
By default the file should be inside the conf directory of grafana-v12.0.0
Grafana will be restarted after the modification.
"""

def modify_defaultsIni():
    # read the path from gf_conn.yaml
    file = open('./a_EverythingNeedToChange/gf_conn.yaml','r')
    default_config_path = yaml.safe_load(file)['GF_defaults_PATH']

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

        if stripped.startswith('[auth.anonymous]'):
            in_anonymous_block = True   # Anonymous block starts
            output.append(line)
            continue

        if in_anonymous_block:
            if stripped.startswith('['):
                in_anonymous_block = False  # Anonymous block ends

            # modify the lines
            if stripped.startswith('enabled'):
                line = 'enabled = true\n'
            if stripped.startswith('device_limit'):
                line = 'device_limit = 100000\n'
        
        if stripped.startswith('[server]'):
            in_server_block = True  # Server block starts
            output.append(line)
            continue

        if in_server_block:
            if stripped.startswith('['):
                in_server_block = False
        
            # modify the lines:
            if stripped.startswith('http_addr'):
                line = 'http_addr = 127.0.0.1\n'    # only allow listen to local

        output.append(line)
        
    # Modify the file:
    with open(default_config_path, 'w') as file:
        file.writelines(output)
    
    # restart grafana:
    subprocess.run(["bash", "./start_grafana.sh"])

# Allow Run
if __name__ == '__main__':
    modify_defaultsIni()