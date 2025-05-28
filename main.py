import os
import subprocess
import yaml
from create.generate import upload_dashboards
from time import sleep

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

    # check run times
    gf_conn_path = './a_EverythingNeedToChange/gf_conn.yaml'
    with open(gf_conn_path, mode='r') as file:
        gf_conn = yaml.safe_load(file)
    run_times = int(gf_conn['GF_RUN_TIMES'])


    # First run
    if run_times == 0:
        print(" >> First run, preSteps will be executed. (<ゝω・）☆")
        # preSteps in order
        subprocess.run(["python", "./preSteps/get_api_key.py"], check=True)
        sleep(0.5)    # wait for token to be generated
        subprocess.run(["python", "./preSteps/add_datasource.py"], check=True)
        subprocess.run(["python", "./preSteps/modify_defaultsIni.py"], check=True)


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
    
    print(" >> Dashboards uploaded! ᕕ( ᐛ )ᕗ")


    # Add run times
    run_times += 1
    gf_conn['GF_RUN_TIMES'] = run_times
    with open(gf_conn_path, mode='w') as file:
        yaml.dump(gf_conn, file)

    print(" >> And run_times updated! 乚(`ヮ´ ﾐэ)Э")

    # Done!!
    print(" >>>> All done! (๑•̀ㅂ•́)و✧")


# allow Run
if __name__ == '__main__':
    main()