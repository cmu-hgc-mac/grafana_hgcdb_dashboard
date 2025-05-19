import yaml
from get_api import get_api
from add_dbsource import add_dbsource


def run_git_pull_seq(auto_exit_on_update=True):
    result = subprocess.run(["git", "pull"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Git pull successful.")
        if "Already up to date." not in result.stdout:
            print("Repo updated.")
            if auto_exit_on_update:
                print("Please re-run the script to use the latest version.")
                exit()
    else:
        print("Git pull failed.")
        print(result.stderr)

# def run_step():
    # 1. get_api()
    # 2. add_dbsource()
    # 3. update_dashboard.py (upload the json file to grafana)

def upload():
    - upload whatever in dashboard_json folder
    - update uid for each dashboard


if __name__ == '__main__':
    try:
        run_git_pull_seq() 
    except:
        print("There is a git conflict or network issue.")

    run_step()
