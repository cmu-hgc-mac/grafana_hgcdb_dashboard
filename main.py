import os
import subprocess
from time import sleep

import yaml

from tool.generate import upload_dashboards
from tool.helper import *

"""
This file does EVERYTHING for you (*´ω`*)
"""

cmu_mcs_cms_logo = """
 ▗▄▄▖▗▖  ▗▖▗▖ ▗▖    ▗▖  ▗▖ ▗▄▄▖ ▗▄▄▖     ▗▄▄▖▗▖  ▗▖ ▗▄▄▖
▐▌   ▐▛▚▞▜▌▐▌ ▐▌    ▐▛▚▞▜▌▐▌   ▐▌       ▐▌   ▐▛▚▞▜▌▐▌   
▐▌   ▐▌  ▐▌▐▌ ▐▌    ▐▌  ▐▌▐▌    ▝▀▚▖    ▐▌   ▐▌  ▐▌ ▝▀▚▖
▝▚▄▄▖▐▌  ▐▌▝▚▄▞▘    ▐▌  ▐▌▝▚▄▄▖▗▄▄▞▘    ▝▚▄▄▖▐▌  ▐▌▗▄▄▞▘
                                                                                              
"""

def main():
    print(cmu_mcs_cms_logo)

    run_times = int(gf_conn.get('GF_RUN_TIMES'))

    # First run
    if run_times == 0:
        print(" >> First run, preSteps will be executed. (<ゝω・）☆")

        # preSteps in order
        subprocess.run(["python", "./preSteps/get_api_key.py"], check=True)
        sleep(0.5)    # wait for token to be generated

        # rebuild GrafanaClient with new token
        gf_conn.reload()
        new_token = gf_conn.get("GF_API_KEY")
        client = GrafanaClient(new_token, gf_url)

        subprocess.run(["python", "./preSteps/add_dbsource.py"], check=True)

    else:
        print(" >> preSteps skipped. (<ゝω・）☆ \n")

    # Everything Need To Generate
    subprocess.run(["python", "create/create_folders.py"], check=True)
    sleep(0.5)    # wait for folders to be added
    subprocess.run(["python", "create/create_dashboards.py"], check=True)


    # Upload dashboards
    folder_list = os.listdir("./Dashboards")
    for folder in folder_list:
        file_list = os.listdir(f"./Dashboards/{folder}")
        for file_name in file_list:
            if file_name.endswith(".json"):
                file_path = f"./Dashboards/{folder}/{file_name}"
                upload_dashboards(file_path)

    print(" >> Dashboards uploaded! ᕕ( ᐛ )ᕗ \n")


    # Add run times
    print(" >> And run_times updated! 乚(`ヮ´ ﾐэ)Э")
    gf_conn.set('GF_RUN_TIMES', run_times + 1)
    gf_conn.save()

    # Done!!
    print(" \n >> All done! (๑•̀ㅂ•́)و✧")


# allow run
if __name__ == "__main__":
    main()