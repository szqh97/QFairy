#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date:  2014-02-19 10:32:39
import os
import sys
import time
import Queue
import sqlite3
import threading
import downloader
import multiprocessing

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

    def get_tasks(taskdb):
        tasks_list = None
        try:
            conn = sqlite3.connect(taskdb)
            cursor = conn.cursor()
            sql = "select id, qvod_url, hash_code, filename, status from qvod_task where status = 0 and id > %d order by id" % self.cur_task_id)
            cursor.execute(sql)
            tasks_list = cursor.fetchall()
            conn.close()
        except Exception, err:
            print "get qvod downlaod tasks error"

        if len(tasks_list) > 0:
            self.cur_task_id = tasks_list[-1][0]
            for t in tasks_list:
                taskQ.put(t)

    def run(self):
        tasknum = 0
        if self.config.has_key("CONCUR_NUM"):
            tasknum = int(self.config["CONCUR_NUM"])
        for i in xrange(tasknum):
            self.down_processes.append(threading.Thread(target = qvod_download_proc, args = (instance,)))
        for t in self.down_processes:
            t.setDaemon(True)
            t.start()

        while True:
            qvod_db = ""
            if sef.config.has_key("QVODTASK_DB"):
                qvod_db = self.config["QVODTASK_DB"]
            self.get_tasks(qvod_db)
            time.sleep(20)

def qvod_download_proc(instance):
    """
    get task from downloaderMgr, 
    start downloader.download_proc,
    update db
    """
    qvod_db = ""
    down_prex = ""
    if  instance.config.has_key("QVODTASK_DB"):
        qvod_db = instance.config["QVODTASK_DB"]
    if instance.config.has_key("DOWN_PREX"):
        down_prex = instance.config["DOWN_PREX"]

    while True:
        task = instance.taskQ.get()
        taskid, qvod_url, hash_code, filename, status = task
        try:
            conn = sqlite3.connect(qvod_db)
            cursor = conn.cursor()
            sql = "update qvod_task set updated_at = current_timestamp, status = 1, where id = %d" % taskid
            cursor.execute(sql)
            conn.commit()
            conn.close()
        except Exception, err:
            pass

        #sssss"
        trunks = download.verify_url(qvod_url)
        if trunks:
            movie_len, hash_code, movie = trunks
        movie = movie.replace(' ', "\ ").replace('(', "\(").replace(')', "\)")
        suffix = '.'.join(('', movie.split('.')[-1]))
        filename = hash_code + suffix

        ret = download.download_proc(qvod_url, filename)

        download_url = download_prex + filename
        try:
            conn = sqlite3.connect(qvod_db)
            cursor = conn.cursor()
            sql = ""
            if ret:
                sql = "update qvod_task set updated_at = current_timestamp, status = 2, download_url = %s, filename = %s  where id = %d" % \
                        (download_url, movie, taskid)
            else:
                sql = "update qvod_task set updated_at = current_timestamp, status = 3 where id = %d" % taskid
            cursor.execute(sql)
            conn.commit()
            conn.close()
        except Exception, err:
            pass

if __name__ == '__main__':
    Mgr = downloaderMgr()
    Mgr.start()






            
    
    

