#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date:  2014-02-19 10:32:39
import os
import sys
import time
import Queue
import torndb
import logging
import logging.config
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

    def get_tasks(self):
        tasks_list = lambda:None
        logger.debug("%s", self.config)
        try:
            dbhost = self.config["db_host"]
            dbname = self.config["db_name"]
            dbuser = self.config["db_user"]
            dbpass = self.config["db_pass"]
            conn = torndb.Connection(dbhost, dbname, dbuser, dbpass)
            sql = "select id as idx, qvod_url, hash_code, filename, status from qvod_tasks where status = 'initialized' and id > %d order by id" % self.cur_task_id
            logger.debug("get task sql is: %s", sql)
            tasks_list = conn.query(sql)
            conn.close()
        except Exception, err:
            logger.error("get task error!")
            logger.error("%s", str(traceback.format_exc()))

        if len(tasks_list) > 0:
            self.cur_task_id = tasks_list[-1].idx
            for t in tasks_list:
                self.taskQ.put(t)

    def run(self):
        tasknum = 0
        if self.config.has_key("CONCUR_NUM"):
            tasknum = int(self.config["CONCUR_NUM"])
        for i in xrange(tasknum):
            self.down_processes.append(threading.Thread(target = qvod_download_proc, args = (self,)))
        for t in self.down_processes:
            t.setDaemon(True)
            t.start()

        while True:
            qvod_db = ""
            if self.config.has_key("QVODTASK_DB"):
                qvod_db = self.config["QVODTASK_DB"]
            self.get_tasks()
            time.sleep(20)

def qvod_download_proc(instance):
    """
    get task from downloaderMgr, 
    start downloader.download_proc,
    update db
    """
    logger.info("start qvod download...")
    down_prex = ""
    if instance.config.has_key("DOWN_PREX"):
        down_prex = instance.config["DOWN_PREX"]

    dbhost = instance.config["db_host"]
    dbname = instance.config["db_name"]
    dbuser = instance.config["db_user"]
    dbpass = instance.config["db_pass"]

    while True:
        task = instance.taskQ.get()
        logger.info("task: %s", str(task))
        taskid = task.idx
        qvod_url = task.qvod_url
        hash_code = task.hash_code
        filename = task.filename
        status = task.status
        try:
            conn = torndb.Connection(dbhost, dbname, dbuser, dbpass)
            sql = "update qvod_tasks set updated_at = current_timestamp, status = 'processing' where id = %d" % taskid
            logger.debug("update status to processing, sql: %s", sql)
            conn.execute(sql)
            conn.close()
        except Exception, err:
            logger.error("update task status error!")
            logger.error("%s", str(traceback.format_exc()))

        if qvod_url.__class__ is unicode:
            qvod_url = qvod_url.encode("utf-8")
        trunks = downloader.verify_url(str(qvod_url))
        logger.debug("trunks is: %s", str(trunks))
        movie = ""
        if trunks:
            movie_len, hash_code, movie = trunks
        movie = movie.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
        suffix = '.'.join(('', movie.split('.')[-1]))
        filename = hash_code + suffix
        time.sleep(10)
        ret = downloader.download_proc(qvod_url, filename)

        time.sleep(5)

        download_url = down_prex + filename
        logger.info("%s, %s", down_prex, filename)
        try:
            conn = torndb.Connection(dbhost, dbname, dbuser, dbpass)
            sql = ""
            if ret:
                sql = "update qvod_tasks set updated_at = current_timestamp, status = 'succeed', download_url = '%s', filename = '%s'  where id = %d" % \
                        (download_url, movie, taskid)
            else:
                sql = "update qvod_tasks set updated_at = current_timestamp, status = 'error' where id = %d" % taskid
            logger.debug("update task status after download, sql: %s", sql)
            conn.execute(sql)
            conn.close()
        except Exception, err:
            logger.error("update task status after downloading error!")
            logger.error("%s", str(traceback.format_exc()))

if __name__ == '__main__':
    install_logger()
    logger.info("download Manager starting ...")
    Mgr = downloaderMgr()
    Mgr.setDaemon(False)
    Mgr.start()

