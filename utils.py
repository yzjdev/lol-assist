# 通过进程获取port和auth token
import json
import os
from datetime import datetime

from psutil import process_iter


def return_ux_process():
    for process in process_iter():
        if process.name() == 'LeagueClientUx.exe':
            yield process


def parse_cmdline_args(process):
    cmdline_args_parsed = {}
    for cmdline_arg in process.cmdline():
        if len(cmdline_arg) > 0 and '=' in cmdline_arg:
            key, value = cmdline_arg[2:].split('=', 1)
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed


def is_running():
    names = [p.name() for p in process_iter()]
    if 'LeagueClientUx.exe' in names:
        return True
    else:
        return False


def get(key: str, default=None):
    try:
        with open('info.ini', 'r') as f:
            return json.load(f)[key]
    except:
        return default


def save(key: str, value: any):
    file = 'info.ini'
    if os.path.exists(file):
        if os.path.getsize(file) == 0:
            with open(file, 'w') as f:
                f.write(json.dumps({key: value}))
        else:
            with open(file, 'r') as f:
                info = json.load(f)
                info[key] = value
            with open(file, 'w') as f:
                f.write(json.dumps(info))
    else:
        with open(file, 'w') as f:
            f.write(json.dumps({key: value}))


def nowtime():
    now = datetime.now()
    return now.strftime("%H:%M:%S %f")[:-3]
