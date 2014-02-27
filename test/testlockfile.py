#!/usr/bin/env python
import os
import threading
import time
import portalocker
from portalocker import lock, unlock, LOCK_SH
from filelock import FileLock
def func():
	start = time.time()
	with FileLock('a.txt'):
		with file('a.txt', 'r+') as f:
			#lock(f, LOCK_SH)
			time.sleep(0.2)
			f.seek(0,2)
			f.write(str(os.getpid()) + ', ' + str(time.time()) + '\n')
			#unlock(f)
	end = time.time()
	print start,end, end -start
	
taskq = []

for i in xrange(40):
	taskq.append(threading.Thread(target = func, args = ()))
for t in taskq:
	t.setDaemon(True)
	t.start()

time.sleep(15)
