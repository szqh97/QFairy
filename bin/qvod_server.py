#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-20 16:04:14

import web
import re
import os
import sys
import simlejson

#FIXME add path environment varibles if run it as moudule of apache
#sys.path.append(os.path.normpath(os.path.join(sys.path[0], "")))
__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

import torndb

def load_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["db_host"] = config.get("Qconfig", "db_host")
    config_dict["db_name"] = config.get("Qconfig", "db_name")
    config_dict["db_user"] = config.get("Qconfig", "db_user")
    config_dict["db_pass"] = config.get("Qconfig", "db_pass")
    return config_dict


urls = (
        "qvod_submit_task", "task_submit",
        "qvod_query_task", "task_query",
    )

class task_submit:
    def __init__(self):
        pass;
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
        config = load_config()
        raw_data = web.data()
        post_data = simplejson.loads(raw_data)
        qvod_urls = post_data.get("qvod_urls")

        dbhost = config["db_host"]
        dbname = config["db_name"]
        dbuser = config["db_user"]
        dbpass = config["db_pass"]

        ErrorCode = 0
        ErrorMessage = "success"
        try:
            conn = torndb.Connection(dbhost, dbname, dbuser, dbpass)
            #FIXME convert unicode to utf8?
            for url in qvod_urls:
                if valid_url(url):
                    hash_code = url.split('|')[2]
                    sql = "insert into qvod_tasks (qvod_url, hash_code, created_at, updated_at) values ( '%s', '%s', current_timestamp, current_timestamp)" \
                            % (url, hash_code)
                    conn.execute(sql)
                else:
                    ErrorCode = 100
                    ErrorMessage = "input errror"
            conn.close()
        except Exception, err:
            ErrorCode = -1
            ErrorMessage = "server error"
            pass;
        resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
        return simplejson.dumps(resp)


class task_query:
    def __init__(self):
        pass

    def GET(self):

        pass
