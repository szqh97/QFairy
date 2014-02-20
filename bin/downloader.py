#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-17 13:53:06

import os
import re
import sys
import time
import thread
import sqlite3
import subprocess
from ConfigParser import ConfigParser

__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)
__INSTALLER__ = "QvodSetup.exe"
__INSTALLER__ = os.path.normpath(os.path.join(__HOME__, "bin", __INSTALLER__))
print __HOME__

if re.match("LINUX.*", sys.platform, re.IGNORECASE):
    __platform__ = "LINUX"
elif re.match("WIN.*", sys.platform, re.IGNORECASE):
    MKDIRP = "mkdir "
    __platform__ = "WIN"


def load_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["VIDEO_PATH"] = config.get("Qconfig", "VIDEO_PATH") # TODO set a default path
    config_dict["CACHE_PATH"] = config.get("Qconfig", "CACHE_PATH") # TODO set a default path
    config_dict["TIMEOUT"] = config.get("Qconfig", "TIMEOUT") # TODO set a default path
    config_dict["CONCUR_NUM"] = config.get("Qconfig", "CONCUR_NUM") # FIXME use database instead it
    config_dict["QVODTASK_DB"] = config.get("Qconfig", "QVODTASK_DB")
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

def env_check():
    if __platform__ == "LINUX":
        ret = os.system("which wine 2>&1 >/dev/null")
        if ret != 0:
            print "error, Please install Wine first ..."
            return False


def download_proc(qvod_url, frename = ""):
    # verify qvod url
    trunks = verify_url(str(qvod_url))
    if not trunks:
        print str(thread.get_ident()) + " QVOD url is illegal"
        return False
    movie_len, hash_code, movie = trunks
    movie = movie.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")

    env_check()

    # load conf
    conf = load_config()
    print conf
    video_path = conf["VIDEO_PATH"] 
    print video_path
    cache_path = conf["CACHE_PATH"]
    timeout = int(conf["TIMEOUT"])

    # cache dir
    suffix = '.'.join(('', movie.split('.')[-1]))
    if frename == '':
        #frename = movie.replace(suffix, '')
        frename = movie
    else:
        frename = frename.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
    movie = frename.replace(suffix, '')
    print movie, frename
    
    frename = frename.decode("utf-8")
    cache_dir = os.path.normpath(os.path.join(cache_path, movie))

    if not os.path.isdir(donotescapespace(cache_dir)):
        cmd = ""
        print __platform__
        if __platform__ == "LINUX":
            cmd = 'mkdir -p ' + cache_dir + " 1>&2 >/dev/null"
            print cmd
        elif __platform__ == "WIN":
            cmd = 'mkdir ' + cache_dir
            print cmd
        ret = os.system(cmd)
        if ret != 0: 
            print str(thread.get_ident()) + " Permission denied to create cache directory!"
            return False

    # copy setup.exe to hashcode+movie_hasicode.exe
    download_exe =  frename + '_' + hash_code + ".exe"
    cmd = ""
    p_downloder = None
    if __platform__ == "LINUX":
        cmd = "cp " + __INSTALLER__ + ' ' + cache_dir + os.sep + download_exe
        print cmd
        if not os.system(cmd):
            p_downloder = subprocess.Popen(["wine", donotescapespace(cache_dir + os.sep + download_exe)],
                    stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        else:
            print "cp xxxx"

    elif __platform__ == "WIN":
        cmd = "copy " + __INSTALLER__ + ' ' + cache_dir + os.sep + download_exe
        if not os.system(cmd):
            p_downloder = subprocess.Popen([donotescapespace(cache_dir + os.sep + download_exe)], 
                    stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        else:
            print "xxx"
    
    # update downloading progress
    cache =  frename+ ".!qd"
    complete = cache.replace(".!qd", '')
    b_successed = False
    start_time = time.time()
    last_update = start_time
    while True:
        print "detect whether download succe"
        print cache_dir + os.sep +complete
        print cache
        if os.path.isfile(donotescapespace(cache_dir + os.sep + complete)):
            p_downloder.terminate()
            if __platform__ == "LINUX":
                if not os.system("mv " + cache_dir + os.sep + complete + ' ' + video_path + os.sep + complete):
                    os.system("rm -rf " + cache_dir)
                else:
                    print "Cannot move the cache file to video path"
            elif __platform__ == "WIN":
                if not os.system("move " + cache_dir + os.sep + complete + ' ' + video_path + os.sep + complete):
                    os.system("rmdir /s " + cache_dir)
                else:
                    print "Cannot move the cache file to video path"
            b_successed = True
            break
        elif  not os.path.isfile(donotescapespace(cache_dir + os.sep + cache)):
            
            cur_time = time.time()
            passed_time = cur_time - start_time
            if cur_time - last_update >= timeout:
                p_downloder.terminate()
                print "time out kill downloader"
                b_successed = False
                break
        time.sleep(5)
    if b_successed:
        print "Completed!"
        return True
    return False

if __name__ == '__main__':
    download_proc(sys.argv[1], sys.argv[2])

