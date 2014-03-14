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
    with FileLock(dbname, timeout = 30):
        try:
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            cursor.execute(sql)
            items = cursor.fetchall()
        except Exception, err:
            print str(traceback.format_exc())
        finally:
            conn.close()
    return items

def sqlite_exec(dbname, sql):
    valid_db(dbname)
    with FileLock(dbname, timeout = 30):
        try:
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
        except Exception, err:
            print str(traceback.format_exc())
        finally:
            conn.close()

