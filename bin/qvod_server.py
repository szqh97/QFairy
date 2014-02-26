#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-20 16:04:14

import web
import re
import os
import sys
import traceback
import collections
import simplejson
from ConfigParser import ConfigParser

#FIXME add path environment varibles if run it as moudule of apache
#sys.path.append(os.path.normpath(os.path.join(sys.path[0], "")))
__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

import torndb
import portalocker
from portalocker import lock, unlock, LOCK_EX

urls = (
        "/qvod_submit_task", "task_submit",
        "/qvod_query_task", "task_query",
        "/qvod_delete_file", "deletefile",
        )


status_dict = { "succeed": 0, 
        "initialized": 2,
        "processing": 1,
        "error": 3,
        "params error": 4,
        "server error": -1,
        "input error": 100
        }

def check_platform():
    platform = ""
    if re.match("LINUX.*", sys.platform, re.IGNORECASE):
        platform = "LINUX"
    elif re.match("WIN.*", sys.platform, re.IGNORECASE):
        platform = "WIN"
    return platform

def load_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["VIDEO_PATH"] = config.get("Qconfig", "VIDEO_PATH")
    config_dict["CACHE_PATH"] = config.get("Qconfig", "CACHE_PATH")
    config_dict["QVODTASK_FILE"] = config.get("Qconfig", "QVODTASK_FILE")
    return config_dict


def db_conn():
    conn = None
    try:
        config =load_config()
        dbhoat = config
        dbhost = config["db_host"]
        dbname = config["db_name"]
        dbuser = config["db_user"]
        dbpass = config["db_pass"]
        conn = torndb.Connection(dbhost, dbname, dbuser, dbpass)
    except Exception, err:
        web.debug(" load db config error: %s", str(traceback.format_exc()))
    return conn

class task_submit:
    def __init__(self):
        self.config = load_config()

    def valid_url(self, qvod_url):
        # a qvod url has 3 trunks seperated by "|"
        # qvod://1397199013|56C3448D9FD6D04A8535D5B53DD46A3A482A175E|About_Time.rmvb|
        qvod_url_trunks = 3
        r = re.match("qvod://.+\|.+\|.+\|", qvod_url, re.IGNORECASE)
        trunks = [t for t in qvod_url.split('|') if t is not '']
        if r != None and len(trunks) == qvod_url_trunks:
            return True
        return False

    def POST(self):
        config = self.config
        task_file = confi['QVODTASK_FILE']
        task_file = os.path.normpath(os.path.join(__HOME__, task_file))
        raw_data = web.data()
        post_data = simplejson.loads(raw_data)
        qvod_urls = post_data.get("qvod_urls")

        ErrorCode = 0
        ErrorMessage = "success"

        with file(task_file, "r+") as f:
            lock(f, LOCK_EX)
            try:
                taskQ = cPickle.load(f)
                for url in qvod_urls:
                    if not self.valid_url(url):
                        ErrorCode = 100
                        ErrorMessage = "input error"
                    taskQ.append(url)
                s = cPickle.dumps(taskQ)
                f.seek(0,0)
                f.truncate()
                f.write(s)
            except Exception, err:
                ErrorCod = -1
                ErrorMessage = "server error"
                print traceback.format_exc()
            unlock(f)
        
        resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
        return simplejson.dumps(resp)


class task_query:
    def __init__(self):
        self.config = load_config()
        pass

    def GET(self):
        config = self.config
        params = web.input()
        ErrorCode = 2
        ErrorMessage = "initialized"
        DownloadURL = ""
        qvod_url = ""
        hash_code = ""
        video_path = config["VIDEO_PATH"]
        cache_path = config["CACHE_PATH"]
        video_path = os.path.normpath(os.path.join(__HOME__, video_path))
        cache_path = os.path.normpath(os.path.join(__HOME__, cache_path))
        if params.has_key("qvod_url"):
            qvod_url = params["qvod_url"]
            hash_code = qvod_url.split('|')[1]
        if params.has_key("hash_code"):
            hash_code = params["hash_code"]
        if len(qvod_url) == 0 or len(hash_code) == 0:
            ErrorCode = 100
            ErrorMesage = "input error"

        res = None
        try:
            conn = db_conn()
            sql = "select status,download_url from qvod_tasks where hash_code = '%s'" % hash_code
            print sql
            res = conn.get(sql)
            conn.close()
        except Exception, err:
            ErrorCode = -1
            ErrorMessage = "server error"
            web.debug("error: %s", str(traceback.format_exc()))
        if res:
            ErrorMessage = res.status
            ErrorCode = status_dict[res.status]
            DownloadURL = res.download_url
        else:
            ErrorCode = 100
            ErrorMessage = "input error"

        resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
        return simplejson.dumps(resp)

class deletefile:
    def __init__(self):
        self.config = load_config()

    def POST(self):
        ErroCode = 0
        cmd = "success"
        config = self.config
        video_path = config["VIDEO_PATH"]
        cache_path = config["CACHE_PATH"]
        video_path = os.path.normpath(os.path.join(__HOME__, video_path))
        cache_path = os.path.normpath(os.path.join(__HOME__, cache_path))
        raw_data = web.data()
        req = simplejson.loads(raw_data)
        hash_list = req["hashid_list"]
        files = os.listdir(video_path)
        for hash_code in hash_list:
            exist_files = [ f for f in files if re.match(hash_code + ".*", f, re.IGNORECASE) and os.isfile(f)]
        exist_files = [ os.path.normpath(os.path.join(video_path,f)) for f in exist_files ]
        files2del = ' '.join(exist_files)
        
        if os.name == 'posix':
            cmd = "rm -f %s" % files2del
        elif os.name = 'nt':
            cmd = "del /q %s" % files2del
        if not os.system(cmd):
            ErrorCode = -1
            ErrorMessage = "server error: delete files error"
        resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
        return simplejson.dumps(resp)

if __name__ == "__main__":

    app = web.application(urls, globals())
    app.run()
