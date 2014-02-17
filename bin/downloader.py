#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-17 13:53:06

import os
import re
import sys
import time
import sqlite3
from ConfigParser import ConfigParser

__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)
__INSTALLER__ = "QvodSetup.exe"
print __HOME__

if not re.match("LINUX.*", os.platform, re.IGNORECASE):
    __platform__ = "LINUX"
elif not re.match("WIN.*", os.platform, re.IGNORECASE):
    MKDIRP = "mkdir "
    __platform__ = "WIN"


def load_qfairy_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["VIDEO_PATH"] = config.get("Qconfig", "VIDEO_PATH") # TODO set a default path
    config_dict["CACHE_PATH "] = config.get("Qconfig", "CACHE_PATH") # TODO set a default path
    config_dict["TIMEOUT"] = config.get("Qconfig", "TIMEOUT") # TODO set a default path
    config_dict["RECORD "] = config.get("Qconfig", "RECORD") # FIXME use database instead it
    return config_dict

def verify_url(qvod_url):

    # a qvod url has 3 trunks seperated by "|"
    # qvod://1397199013|56C3448D9FD6D04A8535D5B53DD46A3A482A175E|About_Time.rmvb|
    qvod_url_trunks = 3

    r = re.match("qvod://.+\|.+\|.+\|", qvod_url, re.IGNORECASE)

    trunks = [t for t in qvod_url.split('|') if t is not '']
    if r != None and len(trunks) == qvod_url_trunks:
        return trunks
    return False

def donotescapespace(s):
    return s.replace("\ ", ' ')

def download_proc(qvod_url, frename = ""):
    # verify qvod url
    trunks = verify_url(qvod_url)
    if not trunks:
        print str(thread.get_ident()) + "QVOD url is illegal"
    movie_len, hash_code, movie = trunks
    movie = moive.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")

    # load conf
    conf = load_qfairy_config()
    video_path = conf["VIDEO_PATH"] 
    cache_path = conf["CACHE_PATH"]
    timeout = int(conf["TIMEOUT"])

    # cache dir
    suffix = '.'.join('', [movie.split('.')[-1]])
    if frename == '':
        frename = movie.replace(suffix, '')
    else:
        frename = frename.replace(suffix, '').replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
    
    frename = frename.decode("utf-8")
    cache_dir = os.path.normpath(os.path.join(cache_path, frename))

    if not os.path.isdir(donotescapespace(cache_dir)):
        cmd = ""
        if __platform__ == "LINUX":
            cmd = 'mkdir -p ' + cache_dir + " 2>/dev/null")
        elif __platform__ == "WIN":
            cmd = 'mkdir ' + cache_dir
        ret = os.system(cmd)
        if ret != 0: 
            print str(thread.get_ident()) + "Permission denied to create cache directory!"
            return False

    # copy setup.exe to hashcode+movie_hasicode.exe
    download_exe = has_code + '+' + frename + '_' + has_code + ".exe"
    cmd = ""
    if __platform__ == "LINUX":
        cmd = "cp " + download_exe + ' ' + cache_dir + os.sep + download_exe
    if __platform__ == "WIN":
        cmd = "copy " + download_exe + ' ' + cache_dir + os.sep + download_exe
    
    down_cmd = 

    




