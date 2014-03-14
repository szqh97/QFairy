#!/usr/bin/env python
import os
import sys
import threading
import sqlite3
import traceback
import time
from filelock import FileLock
testdb = "./test.db"

class taskMgr(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.tasks = []
    def run(self):
        print "aaa"
        for i in xrange(4):
            self.tasks.append(threading.Thread(target = func, args = ("./test.db",)))
        for t in self.tasks:
            t.setDaemon(True)
            t.start()
        while True:
            try:
                with FileLock(testdb, timeout = 30):
                    conn  = sqlite3.connect(testdb)
                    cursor = conn.cursor()
                    cursor.execute("select * from t")
                    items = cursor.fetchall()
                    conn.close()
                    print "the length of items is ", len(items)
            except Exception, err:
                print traceback.format_exc()
            time.sleep(0.1)

def func(testdb):
    while True:
        time.sleep(0.1)
        try:
            with FileLock(testdb, timeout=30):
                conn = sqlite3.connect(testdb)
                cursor = conn.cursor()
                cursor.execute('''insert into t (name) values ("aaa")''')
                print "insert aaa"
                conn.commit()
                conn.close()
        except Exception, err:
            print traceback.format_exc()


if __name__ == '__main__':
    mgr = taskMgr()
    mgr.setDaemon(True)
    mgr.run()
    


