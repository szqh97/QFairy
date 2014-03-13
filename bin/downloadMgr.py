#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date:  2014-02-19 10:32:39
import os
import sys
import time
import Queue
import cPickle
import logging
import logging.config
from filelock import FileLock
from sqliteutils import qvod_exec, qvod_query
import traceback
import multiprocessing
from multiprocessing import Process
import threading
import downloader
import multiprocessing

logger = logging

__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)

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

    def start_download(self):
        concur_num = int(self.config["CONCUR_NUM"])
        task_pickle = self.config["QVODTASK_FILE"]
        task_pickle = os.path.normpath(os.path.join(__HOME__, task_pickle))

        # start download threads at first time
        if len(self.down_processes) == 0:
            tasks = []
            taskQ = None
            with FileLock(task_pickle):
                with file(task_pickle, "r+") as f:
                    try:
                        taskQ = cPickle.load(f)
                        if len(taskQ):
                            logger.info("taskQ: %s" % str(taskQ))
                    except EOFError, e:
                        logger.info ("there is no task to download.")

                    for i in xrange(concur_num):
                        qvod_url = ""
                        try:
                            qvod_url = taskQ.popleft()
                        except IndexError, e :
                            break
                        tasks.append(qvod_url)

                    s = cPickle.dumps(taskQ)
                    f.seek(0,0)
                    f.truncate()
                    f.write(s)

            for t in tasks:
                self.down_processes.append(Process(target = qvod_download_proc, args = (self.config, t)))
            for t in self.down_processes:
                t.daemon = True
                t.start()
            time.sleep(5)
            return 
        
        need_start = False
        for t in self.down_processes:
            if not t.is_alive():
                self.down_processes.remove(t)
        
        if len(self.down_processes) < concur_num:
            need_start = True
        if need_start:
            qvod_urls = []
            with FileLock(task_pickle):
                with file (task_pickle, "r+") as f:
                    taskQ = cPickle.load(f)
                    for i in xrange(concur_num - len(self.down_processes)):
                        try:
                            qvod_url = taskQ.popleft()
                            qvod_urls.append(qvod_url)
                        except IndexError, e:
                            pass 
                    s = cPickle.dumps(taskQ)
                    f.seek(0,0)
                    f.truncate()
                    f.write(s)
            for qvod_url in qvod_urls:
                t = Process(target = qvod_download_proc, args = (self.config, qvod_url))
                self.down_processes.append(t)
                t.daemon = True
                t.start()
        
        time.sleep(5)

    def run(self):
        while True:
            self.start_download()
            
def qvod_download_proc(config, qvod_url):
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

    if qvod_url.__class__ is unicode:
        qvod_url = qvod_url.encode("utf-8")
        
    trunks = downloader.verify_url(qvod_url)

    movie = ""
    if trunks:
        movie_len, hash_code, movie = trunks
    else:
        logger.error("ivalid qvod url:%s", qvod_url)
        return 

    movie = movie.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
    suffix = '.'.join(('', movie.split('.')[-1]))
    filename = hash_code + suffix
    ret = downloader.download_proc(qvod_url, filename)
    
    sql = ""
    if ret:
        sql = "update qvod_task set status = 'error' where hash_code = '%s' " % hash_code
    else:
        sql = "update qvod_task set status = 'succed' where hash_code = '%s' " % hash_code
    qvod_exec(dbname, sql)
    

if __name__ == '__main__':
    install_logger()
    downloader.install_signal_handlers()
    logger.info("download Manager starting ...")
    Mgr = downloaderMgr()
    Mgr.run()

