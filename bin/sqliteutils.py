#!/usr/bin/env python
# -*- coding: utf8 -*-
# AUTHOR: li_yun@vobile.cn
# DATE:  2014-03-13 14:46:02
import sqlite3
from filelock import FileLock
import os
import traceback


def valid_db(dbname):
    if not os.path.isfile(dbname):
        raise Exception("%s is not exists" %dbname)
    return True

def sqlite_query(dbname, sql):
    valid_db(dbname)
    items = None
    try:
        with FileLock(dbname, timeout = 30):
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            cursor.execute(sql)
            items = cursor.fetchall()
            conn.close()
    except Exception, err:
        print str(traceback.format_exc())
    return items

def sqlite_exec(dbname, sql):
    valid_db(dbname)
    try:
        with FileLock(dbname, timeout = 30):
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            conn.close()
    except Exception, err:
        print str(traceback.format_exc())

