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
import signal
import traceback
import time
import collections
import simplejson
from filelock import FileLock
from ConfigParser import ConfigParser
from sqliteutils import sqlite_query, sqlite_exec
import psutil

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

def utf8(s):
    if s.__class__ is unicode:
        s = s.encode('utf-8')
    return s

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
      p = psutil.Process(parent_pid)
    except psutil.error.NoSuchProcess:
      return
    child_pid = p.get_children(recursive=True)
    for pid in child_pid:
      os.kill(pid.pid, sig)
     
def delete_file_folder(src):
    '''delete files and folders'''
    if os.path.isfile(src):
        try:
            os.remove(src)
        except:
            pass
    elif os.path.isdir(src):
        for item in os.listdir(src):
            itemsrc=os.path.join(src,item)
            delete_file_folder(itemsrc) 
        try:
            os.rmdir(src)
        except:
            pass

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
            url = utf8(url)
            hash_code = url.split('|')[1]
            sql += ''' "%s", "%s", "initialized" ''' % (url, hash_code)
            sql += un_s
        sql = un_s.join(sql.split(un_s)[0:-1])
        dbname = self.config["QVODTASK_DB"]
        dbname = os.path.normpath(os.path.join(__HOME__, dbname))
        print dbname
        print sql
        
        sqlite_exec(dbname, sql)

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
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)
        hash_code = utf8(hash_code)

        sql = "select status, download_url from qvod_task where hash_code = '%s'" % hash_code
        res = sqlite_query(dbname, sql)

        if len(res) == 0:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)

        status = res[0][0]
        DownloadURL = res[0][1]
        if DownloadURL is None: DownloadURL = ""
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
        ErrorCode = 0
        ErrorMessage = "success"
        cache_dir = config["CACHE_PATH"]

        if params.has_key("hash_code"):
            hash_code = params["hash_code"]
        if len(hash_code) == 0:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage, "DownloadURL" : DownloadURL}
            return simplejson.dumps(resp)
        hash_code = utf8(hash_code)

        # kill the downloader process and delete task from db, this task may retried
        sql = "select downloader_pid from qvod_task where status = 'processing' and hash_code = '%s'" % hash_code
        pid = -1
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
                sql = "delete from qvod_task where hash_code = '%s' " % hash_code
                cursor.execute(sql)
                conn.commit()
            except Exception, err:
                print str(traceback.format_exc())
            finally:
                conn.close()
        try:
            if os.name == 'nt':
                kill_child_processes(pid)
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)

        except OSError:
            print str(traceback.format_exc())
            raise Exception("kill pid %d error" % pid)
        try:
            cache_dir = os.path.normpath(os.path.join(__HOME__, cache_dir))
            cache_dir = os.path.normpath(os.path.join(cache_dir, hash_code))
            print cache_dir
            delete_file_folder(cache_dir)
        except Exception, err:
            print "rm cachedir:", cache_dir, "errr"

        resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage}
        return simplejson.dumps(resp)

class deletefile:
    def __init__(self):
        self.config = load_config()

    def POST(self):
        raw_data = web.data()
        req = simplejson.loads(raw_data)
        try:
            hash_list = req["hashid_list"]
        except Exception, err:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage" : ErrorMessage}
            return simplejson.dumps(resp)
        ErrorCode = 0
        ErrorMessage = "success"
        config = self.config
        video_path = config["VIDEO_PATH"]
        dbname = config["QVODTASK_DB"]
        video_path = os.path.normpath(os.path.join(__HOME__, video_path))
        dbname= os.path.normpath(os.path.join(__HOME__, dbname))

        
        res = []
        hashlist = tuple( utf8(h) for h in hash_list )
        sql = ""
        if len(hashlist) >1:
            sql = "select filename from qvod_task where hash_code in %s and status = 'succeed'" % str(hashlist)
        else:
            sql = "select filename from qvod_task where hash_code = '%s' and status = 'succeed'" % hashlist[0]
        print sql
        res = sqlite_query(dbname, sql)

        if len(res) == 0:
            ErrorCode = 100
            ErrorMessage = "input error"
            resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
            return simplejson.dumps(resp)

        for f in res:
            f = utf8(f[0])
            f = os.path.normpath(os.path.join(video_path, f))
            if not os.path.isfile(f):
                print f, "is not file"
                ErrorCode = -1
                ErrorMessage = "server error: delete files error"
                resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
                return simplejson.dumps(resp)

        for f in res:
            f = utf8(f[0])
            f = os.path.normpath(os.path.join(video_path, f))
            try:
                os.remove(f)
                print f
            except OSError:
                ErrorCode = -1
                ErrorMessage = "server error: delete files error"

        resp = {"ErrorCode" : ErrorCode, "ErrorMessage": ErrorMessage}
        return simplejson.dumps(resp)

if __name__ == "__main__":

    app = web.application(urls, globals())
    app.run()
