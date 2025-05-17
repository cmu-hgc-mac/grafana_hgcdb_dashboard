import os

"""
This script modifies the default.ini file in the conf directory to enable anonymous access to Grafana.
    *** Make Sure the path is correct ***
By default the file should be inside the conf directory of grafana-v12.0.0
"""

def modify_viewer_access(default_config_path = './grafana-v12.0.0/conf/default.ini'):
    # exit the program if default.ini not found in conf directory
    if not os.path.exists(default_config_path):
        print(f">> {default_config_path} not found. Exiting.")
        exit(1)
    
    # load the file
    with open(default_config_path, 'r') as file:
        lines = file.readlines()

    output = []
    in_anonymous_block = False  # Initialize the condition

    # start the loop
    for line in lines:
        stripped = line.strip()

        if stripped.startswith('[auth.anonymous]'):
            in_anonymous_block = True   # Block starts
            output.append(line)
            continue

        if in_anonymous_block:
            if stripped.startswith('['):
                in_anonymous_block = False  # Block ends

            # modify the lines
            if stripped.startswith('enabled'):
                line = 'enabled = true\n'
            if stripped.startswith('device_limit'):
                line = 'device_limit = 100000\n'

        output.append(line)
        
    # Modify the file:
    with open(default_config_path, 'w') as file:
        file.writelines(output)

# Allow Run
if __name__ == '__main__':
    modify_viewer_access()