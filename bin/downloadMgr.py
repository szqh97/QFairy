#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date:  2014-02-19 10:32:39
import os
import sys
import time
import Queue
import torndb
import cPickle
import logging
import logging.config
from filelock import FileLock
import traceback
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

class downloaderMgr(threading.Thread):
    """
     Manager downloader process
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.config = downloader.load_config()
        self.cur_task_id = 0
        self.taskQ = Queue.Queue()
        self.down_processes =[]

    def start_download(self):
        concur_num = len(self.config["CONCUR_NUM"])
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

            print tasks
            for t in tasks:
                self.down_processes.append(threading.Thread(target = qvod_download_proc, args = (self.config, t)))
            for t in self.down_processes:
                t.setDaemon(True)
                t.start()
            time.sleep(5)
            return 
        
        need_start = 0
        for t in self.down_processes:
            if not t.is_alive():
                self.down_processes.remove(t)
                ++need_start
        
        if need_start:
            qvod_urls = []
            with FileLock(task_pickle):
                with file (task_pickle, "r+") as f:
                    taskQ = cPickle.load(f)
                    for i in xrange(need_start):
                        qvod_url = taskQ.popleft()
                        qvod_urls.append(qvod_url)
                    s = cPickle.dumps(taskQ)
                    f.seek(0,0)
                    f.truncate()
                    f.write(s)
            for qvod_url in qvod_urls:
                t = threading.Thread(target = qvod_download_proc, args = (self.config, qvod_url))
                self.down_processes.append(t)
                t.setDaemon(True)
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
    cache_path = config["CACHE_PATH"]
    down_prex = config["DOWN_PREX"]

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
    
    # download error move 4AD312D81D59DDBC7684139892E1A41C51C4C094/ to4AD312D81D59DDBC7684139892E1A41C51C4C094.err/ in cache dir
    if not ret:
        old_cache = os.path.normpath(os.path.join(cache_path, hash_code))
        err_cache = os.path.normpath(os.path.join(cache_path, hash_code + ".err"))
        cmd = ""
        if os.name == 'posix':
            cmd = "mv %s %s" % (old_cache, err_cache)
        elif os.name == 'nt':
            cmd = "rename %s %s" % (old_cache, err_cache)
        if os.system(cmd):
            logger.error("rename %s -> %s failed", old_cache, err_cache)

if __name__ == '__main__':
    install_logger()
    logger.info("download Manager starting ...")
    Mgr = downloaderMgr()
    Mgr.setDaemon(False)
    Mgr.start()

