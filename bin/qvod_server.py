#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-20 16:04:14

import web
import re
import os
import sqlite3
import sys
import cPickle
import traceback
import collections
import simplejson
from filelock import FileLock
from ConfigParser import ConfigParser
from sqliteutils import sqlite_query, sqlite_exec

#FIXME add path environment varibles if run it as moudule of apache
#sys.path.append(os.path.normpath(os.path.join(sys.path[0], "")))
__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

urls = (
        "/qvod_submit_task", "task_submit",
        "/qvod_query_task", "task_query",
        "/qvod_delete_file", "deletefile",
        "/qvod_kill_downloader", "killdownloader",
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
    config_dict["CACHE_PATH"] = config.get("Qconfig", "CACHE_PATH")
    config_dict["QVODTASK_FILE"] = config.get("Qconfig", "QVODTASK_FILE")
    config_dict["QVODTASK_DB"] = config.get("Qconfig", "QVODTASK_DB")
    config_dict["DOWN_PREX"] = config.get("Qconfig", "DOWN_PREX")
    return config_dict

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
        task_file = config['QVODTASK_FILE']
        task_file = os.path.normpath(os.path.join(__HOME__, task_file))
        raw_data = web.data()
        post_data = simplejson.loads(raw_data)
        qvod_urls = None
        try:
            qvod_urls = post_data.get("qvod_urls")
        except Exception, err:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
            return simplejson.dumps(resp)
        print qvod_urls

        ErrorCode = 0
        ErrorMessage = "success"
        sql = ''' insert or ignore into qvod_task ( qvod_url, hash_code, status) select '''
        un_s = "union all select"
        for url in qvod_urls:
            if url.__class__ is unicode:
                url = url.encode('utf-8')
            hash_code = url.split('|')[1]
            sql += ''' "%s", "%s", "initilized" ''' % (url, hash_code)
            sql += un_s
        sql = un_s.join(sql.split(un_s)[0:-1])
        dbname = self.config["QVODTASK_DB"]
        dbname = os.path.normpath(os.path.join(__HOME__, dbname))
        print dbname
        print sql
        
        sqlite_exec(dbname, sql)

#        with FileLock(task_file):
#            with file(task_file, "r+") as f:
#                try:
#                    taskQ = cPickle.load(f)
#                    for url in qvod_urls:
#                        if url.__class__ is unicode:
#                            url = url.encode('utf-8')
#                        if not self.valid_url(url):
#                            ErrorCode = 100
#                            ErrorMessage = "input error"
#                            resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
#                            return simplejson.dumps(resp)
#                        h = url.split('|')[1]
#                        if len ([ t for t in taskQ if re.match('.*' + h + ',*', t, re.IGNORECASE) ]) == 0:
#                            taskQ.append(url)
#                    s = cPickle.dumps(taskQ)
#                    f.seek(0,0)
#                    f.truncate()
#                    f.write(s)
#                except Exception, err:
#                    ErrorCod = -1
#                    ErrorMessage = "server error"
#                    print traceback.format_exc()
#            
        resp = {"ErrorCode":ErrorCode, "ErrorMessage":ErrorMessage}
        return simplejson.dumps(resp)


class task_query:
    def __init__(self):
        self.config = load_config()
        pass

    def GET(self):
        config = self.config
        dbname = config['QVODTASK_DB']
        dbname = os.path.normpath(os.path.join(__HOME__, dbname))

        down_prex = config["DOWN_PREX"]

        params = web.input()
        ErrorCode = 2
        ErrorMessage = "initialized"
        DownloadURL = ""
        qvod_url = ""
        hash_code = ""

        if params.has_key("hash_code"):
            hash_code = params["hash_code"]
        if len(hash_code) == 0:
            ErrorCode = 100
            ErrorMesage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)
        if hash_code.__class__ is unicode: 
            hash_code = hash_code.encode('utf-8')
        sql = "select status from qvod_task where hash_code = '%s'" % hash_code
        res = sqlite_query(dbname, sql)

        if len(res) == 0:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)

        status = res[0][0]
        ErrorMessage = status
        ErrorCode = status_dict[status]
        resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
        return simplejson.dumps(resp)

class killdownloader:
    def __init__(self):
        self.config = load_config()
    def GET(self):
        config = self.config
        dbname = config['QVODTASK_DB']
        dbname = os.path.normpath(os.path.join(__HOME__, dbname))
        params = web.input()

        if params.has_key("hash_code"):
            hash_code = params["hash_code"]
        if len(hash_code) == 0:
            ErrorCode = 100
            ErrorMesage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)
        if hash_code.__class__ is unicode: 
            hash_code = hash_code.encode('utf-8')

        # kill the downloader process and delete task from db, this task may retried
        sql = "select downlaoder_pid from qvod_task where status = 'processing' and hash_code = '%s'" % hash_code
        with FileLock(dbname, timeout=30):
            try:
                conn = sqlite3.connect(dbname)
                cursor = conn.cursor()
                cursor.execute(sql)
                item = cursor.fetchall()
                if len(item) == 0:
                    ErrorCode = 100
                    ErrorMessage = "input error"
                    resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage}
                    return simplejson.dumps(resp)
                pid = int(item[0][0])
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    print str(traceback.format_exc())
                sql = "delete from qvod_task where hash_code = '%s' " % hash_code
                cursor.execute(sql)
                conn.commit()
                conn.close()
            except Exception, err:
                print str(traceback.format_exc())

class deletefile:
    def __init__(self):
        self.config = load_config()

    def POST(self):
        ErrorCode = 0
        ErrorMessage = "success"
        config = self.config
        video_path = config["VIDEO_PATH"]
        cache_path = config["CACHE_PATH"]
        video_path = os.path.normpath(os.path.join(__HOME__, video_path))
        cache_path = os.path.normpath(os.path.join(__HOME__, cache_path))
        raw_data = web.data()
        req = simplejson.loads(raw_data)
        hash_list = req["hashid_list"]
        files = os.listdir(video_path)
        print files
        exist_files = []
        for hash_code in hash_list:
            
            exist_files += [ f for f in files if re.match(hash_code + ".*", f, re.IGNORECASE) and os.path.isfile(os.path.normpath(os.path.join(video_path, f)))]
            print exist_files, 'xxx'
        if len(exist_files) == 0:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
            return simplejson.dumps(resp)

        exist_files = [ os.path.normpath(os.path.join(video_path,f)) for f in exist_files ]
        print exist_files
        files2del = ' '.join(exist_files)
        
        if not os.path.isfile(file2del):
            print file2del, "is not file"
            ErrorCode = -1
            ErrorMessage = "server error: delete files error"
        if os.remove(file2del) != 0:
            ErrorCode = -1
            ErrorMessage = "server error: delete files error"
        resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
        return simplejson.dumps(resp)

if __name__ == "__main__":

    app = web.application(urls, globals())
    app.run()
