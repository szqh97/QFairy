#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-20 16:04:14

import web
import re
import os
import sys
import traceback
import simplejson
from ConfigParser import ConfigParser

#FIXME add path environment varibles if run it as moudule of apache
#sys.path.append(os.path.normpath(os.path.join(sys.path[0], "")))
__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

import torndb

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

def load_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["VIDEO_PATH"] = config.get("Qconfig", "VIDEO_PATH")
    config_dict["db_host"] = config.get("Qconfig", "db_host")
    config_dict["db_name"] = config.get("Qconfig", "db_name")
    config_dict["db_user"] = config.get("Qconfig", "db_user")
    config_dict["db_pass"] = config.get("Qconfig", "db_pass")
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
        print "aaaa"
        raw_data = web.data()
        print "bbbb"
        print raw_data
        print type(raw_data)
        print raw_data.__class__
        post_data = simplejson.loads(raw_data)
        print "ccccc"
        qvod_urls = post_data.get("qvod_urls")
        print qvod_urls[0].__class__

        ErrorCode = 0
        ErrorMessage = "success"
        try:
            conn = db_conn()
            #FIXME convert unicode to utf8?
            for url in qvod_urls:
                if url.__class__ is unicode:
                    url = url.encode('utf-8')
                if self.valid_url(url):
                    hash_code = url.split('|')[1]
                    sql = "insert into qvod_tasks (qvod_url, hash_code, created_at, updated_at) values ( '%s', '%s', \
                            current_timestamp, current_timestamp)" % (url, hash_code)
                    conn.execute(sql)
                else:
                    ErrorCode = 100
                    ErrorMessage = "input errror"
            conn.close()
        except Exception, err:
            ErrorCode = -1
            ErrorMessage = "server error"
            print traceback.format_exc()
        resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
        return simplejson.dumps(resp)


class task_query:
    def __init__(self):
        pass

    def GET(self):
        params = web.input()
        ErrorCode = 2
        ErrorMessage = "initialized"
        DownloadURL = ""
        qvod_url = ""
        hash_code = ""
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
        config = self.config
        video_path = config["VIDEO_PATH"]
        raw_data = web.data()
        req = simplejson.loads(raw_data)
        try:
            hash_list = req["hashid_list"]
            conn = db_conn()
            sql = "select qvod_url, hash_code from qvod_tasks where hash_code in %s" % str(tuple(hash_list))
            res = conn.query(sql)
            conn.close()
            for item in res:
                qvod_url = res.qvod_url
                hash_code = res.hash_code
                suffix = '.' + qvod_url.split('|')[2].split('.')[-1]
                filename = hash_code + suffix 
                filename = os.path.normpath(os.path.join(video_path, filename))
                #FIXME os platform
                if os.path.exist(filename):
                    os.system("rm -f %s" % filename)
            ErrorCode = 0
            ErrorMessage = "success"
        except Exception, err:
            ErrorCode = -1
            ErrorMessage = "server error"
        resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
        return simplejson.dumps(resp)

if __name__ == "__main__":

    app = web.application(urls, globals())
    app.run()
