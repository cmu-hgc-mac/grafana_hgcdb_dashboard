from matplotlib import patches
from matplotlib.lines import Line2D
from matplotlib import pyplot as plt
import datetime
import glob
import pickle
import asyncio
import asyncpg
import sys
import os

import yaml
# Load Information
db_conn_path='a_EverythingNeedToChange/db_conn.yaml'
with open(db_conn_path, mode='r') as file:
    db_conn = yaml.safe_load(file)

DBHostname = db_conn["db_hostname"]
DBDatabase = db_conn["dbname"]
DBUsername = db_conn["user"]
DBPassword = db_conn["password"]

def generate_plot():
    loop = asyncio.get_event_loop()

    # functions for interating with db
    async def connect_db():
        return await asyncpg.create_pool(
            host = DBHostname,
            database = DBDatabase,
            user = DBUsername,
            password = DBPassword
        )

    pool = loop.run_until_complete(connect_db())

    async def fetch_modules(pool):
        query = """SELECT * FROM module_info;"""
        async with pool.acquire() as conn:
            return await conn.fetch(query)

    async def fetch_iv(pool, moduleserial):
        query = f"""SELECT *  
                    FROM module_iv_test                                                                  
                    WHERE REPLACE(module_name,'-','') = '{moduleserial}'                                       
                    ORDER BY date_test, time_test;"""
        async with pool.acquire() as conn:
            return await conn.fetch(query)


    def select_iv(moduleserial, modulestatus, dry=True, roomtemp=True):
        result = loop.run_until_complete(fetch_iv(pool, moduleserial))
        
        runs = []
        for r in result:
            RH = float(r['rel_hum'])
            T = float(r['temp_c'])
            req1 = (RH <= 12) if dry else (RH >= 20)
            req2 = (T >= 10 and T <= 30) if roomtemp else (T <= -20)
            if req1 and req2 and r['status_desc'] == modulestatus:
                runs.append(r)

        return runs

    N_MODULE_SHOW = 15

    result = loop.run_until_complete(fetch_modules(pool))

    def modserkey(module):
        return int(module['module_no'])

    result.sort(key=modserkey)
    module_serials = [mod['module_name'] for mod in result]
    modules = module_serials[-N_MODULE_SHOW:]

    fig, ax = plt.subplots(figsize=(16, 12))

    datetoday = str(datetime.datetime.now()).split(' ')[0]

    def sortkey(curve):
        return curve['meas_i'][-1]/curve['program_v'][-1]

    dry = True
    for module in modules:

        curvedata = select_iv(module, 'Completely Encapsulated', dry=dry, roomtemp=True)

        if len(curvedata) == 0:
            curvedata = select_iv(module, 'Frontside Encapsulated', dry=dry, roomtemp=True)

        if len(curvedata) > 0:
            # get best curve
            curvedata.sort(reverse=True, key = sortkey)
            
            meas_v = curvedata[-1]['meas_v']
            meas_i = curvedata[-1]['meas_i']

            plt.plot(meas_v, meas_i, label=module)
                    
    ax.set_yscale('log')
    dryname = 'Dry' if dry else 'Ambient'
    ax.set_title(f'{dryname} Module IV Curves [Log Scale]', fontsize=30)
    ax.set_xlabel('Reverse Bias [V]', fontsize=25)
    ax.set_ylabel(r'Leakage Current [A]', fontsize=25)
    ax.set_ylim(1e-9, 1e-03)
    ax.set_xlim(0, 500)
    ax.legend(fontsize=15, loc='upper left')

    # create folder:
    os.makedirs("iv_curves_plot", exist_ok=True)
    # define path and save plot
    plt_path = f'iv_curves_plot/combined_iv_logscale_{datetoday}_{N_MODULE_SHOW}.png'
    plt.savefig(plt_path)

    return plt_path


import base64
from PIL import Image

def convert_png_to_base64(image_path):
    """convert the png to base64
    """
    # Compress the image
    img = Image.open(image_path)
    img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
    img.save(image_path, optimize=True)

    # Generate the encoded_string
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string

def generate_content(encoded_string):
    """generate the markdown content for text panel
    """
    content = f'<img src=\"data:image/png;base64,{encoded_string}" style="width: auto; height: auto;"/>'
    return content
