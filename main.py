import os
import subprocess
from time import sleep

import yaml

from tool.helper import *

"""
This file does EVERYTHING for you (*´ω`*) 
    — from configuring Grafana to linking PostgreSQL and auto-generating dashboards.

Special thanks to Sindhu Murthy and Manami Kanemura for the amazing database this is built on.

I'm also sincerely thankful to the entire CMU HGCal MAC for trusting me with the responsibility of leading this project.
"""

cmu_hgc_mac_logo = """
 ▗▄▄▖▗▖  ▗▖▗▖ ▗▖    ▗▖ ▗▖ ▗▄▄▖ ▗▄▄▖    ▗▖  ▗▖ ▗▄▖  ▗▄▄▖
▐▌   ▐▛▚▞▜▌▐▌ ▐▌    ▐▌ ▐▌▐▌   ▐▌       ▐▛▚▞▜▌▐▌ ▐▌▐▌   
▐▌   ▐▌  ▐▌▐▌ ▐▌    ▐▛▀▜▌▐▌▝▜▌▐▌       ▐▌  ▐▌▐▛▀▜▌▐▌   
▝▚▄▄▖▐▌  ▐▌▝▚▄▞▘    ▐▌ ▐▌▝▚▄▞▘▝▚▄▄▖    ▐▌  ▐▌▐▌ ▐▌▝▚▄▄▖

"""

def main():
    print(cmu_hgc_mac_logo)

    run_times = int(gf_conn.get('GF_RUN_TIMES'))

    # First run
    if run_times == 0:
        print(" >> First run, preSteps will be executed. (<ゝω・）☆ \n")

        # preSteps in order
        subprocess.run(["python", "./preSteps/get_api_key.py"], check=True)
        sleep(0.5)    # wait for token to be generated

        # rebuild GrafanaClient with new token
        gf_conn.reload()
        new_token = gf_conn.get("GF_API_KEY")
        client = GrafanaClient(new_token, GF_URL)

        subprocess.run(["python", "./preSteps/add_dbsource.py"], check=True)

    else:
        print(" >> preSteps skipped. (<ゝω・）☆ \n")

    # Everything Need To Generate
    subprocess.run(["python", "create/create_folders.py"], check=True)
    sleep(0.5)    # wait for folders to be added
    subprocess.run(["python", "create/create_dashboards.py"], check=True)
    subprocess.run(["python", "create/create_alerts.py"], check=True)

    # Add run times
    gf_conn.reload()
    print(" >> And run_times updated! 乚(`ヮ´ ﾐэ)Э")
    gf_conn.set('GF_RUN_TIMES', run_times + 1)
    gf_conn.save()

    # Done!!
    print(" \n >> All done! (๑•̀ㅂ•́)و✧")


# allow run
if __name__ == "__main__":
    main()
