#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date:  2014-02-19 10:32:39
import os
import sys
import time
import Queue
import sqlite3
import cPickle
import logging
import logging.config
from filelock import FileLock
from sqliteutils import sqlite_exec, sqlite_query
import traceback
import multiprocessing
from multiprocessing import Process
import threading
import downloader
import multiprocessing

logger = logging

__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

class EmptylistError(Exception):
    pass

def install_logger():
    global logger
    logger.config.fileConfig(os.path.normpath(os.path.join(__HOME__, "config", "logging.conf")))
    logger = logger.getLogger("QvodDownloader")

class downloaderMgr():
    """
     Manager downloader process
    """
    def __init__(self):
        self.config = downloader.load_config()
        self.cur_task_id = 0
        self.taskQ = Queue.Queue()
        self.down_processes =[]

    def start_downloader(self):
        concur_num = int(self.config["CONCUR_NUM"])
        dbname = self.config["QVODTASK_DB"]
        dbname = os.path.normpath(os.path.join(__HOME__, dbname))

        select_tasks = "select id from qvod_task where status = 'initialized' order by id limit 1"
        while True:
            for p in self.down_processes:
                if not p.is_alive(): self.down_processes.remove(p)
            if len(self.down_processes) != concur_num:
                sql = select_tasks 
                items = sqlite_query(dbname, sql)
                time.sleep(0.1)
                if len(items) > 0 :
                    p = Process(target = qvod_download_proc, args = (self.config,))
                    self.down_processes.append(p)
                    p.daemon = True
                    p.start()
            time.sleep(10)

    def run(self):
        while True:
            self.start_downloader()
            
def qvod_download_proc(config):
    """
    get task from downloaderMgr, 
    start downloader.download_proc,
    update db
    """
    
    dbname = config["QVODTASK_DB"]
    cache_path = config["CACHE_PATH"]
    down_prex = config["DOWN_PREX"]
    cache_path = os.path.normpath(os.path.join(__HOME__, cache_path))
    dbname = os.path.normpath(os.path.join(__HOME__, dbname))

    pid = os.getpid()
    select_task = "select id, qvod_url from qvod_task where  status = 'initialized' order by id limit 1" 
    update_task = "update qvod_task set status = 'processing', downloader_pid = %d where id = %d"
    qvod_url = ""
    curr_task_id = 0
    with FileLock(dbname, timeout = 30):
        sql = select_task 
        try:
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            cursor.execute(sql)
            task = cursor.fetchall()
            cur_task_id = task[0][0]
            qvod_url = task[0][1]
            sql = update_task % (pid, cur_task_id)
            cursor.execute(sql)
            conn.commit()
        except Exception, err:
            print str(traceback.format_exc())
        finally:
            conn.close()

    if qvod_url.__class__ is unicode:
        qvod_url = qvod_url.encode("utf-8")
        
    trunks = downloader.verify_url(qvod_url)

    movie = ""
    if trunks:
        movie_len, hash_code, movie = trunks
    else:
        logger.error("ivalid qvod url:%s", qvod_url)
        sql = "update qvod_task set status = 'error' where hash_code = '%s' " % hash_code
        sqlite_exec(dbname, sql)
        return False

    movie = movie.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
    suffix = '.'.join(('', movie.split('.')[-1]))
    filename = hash_code + suffix
    ret = downloader.download_proc(qvod_url, filename)
    
    download_url = down_prex + filename
    sql = ""
    if not ret:
        sql = "update qvod_task set status = 'error' where hash_code = '%s' " % hash_code
    else:
        sql = "update qvod_task set status = 'succeed', download_url = '%s', filename = '%s' where hash_code = '%s' " % (download_url, filename, hash_code)
    sqlite_exec(dbname, sql)
    return True
    

if __name__ == '__main__':
    install_logger()
    downloader.install_signal_handlers()
    logger.info("download Manager starting ...")
    Mgr = downloaderMgr()
    Mgr.run()

