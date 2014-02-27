#!/usr/bin/env python
import os
import threading
import time
import portalocker
from portalocker import lock, unlock, LOCK_SH

def func():
	start = time.time()
	with file('a.txt', 'w') as f:
		lock(f, LOCK_SH)
		time.sleep(0.2)
		f.seek(0,2)
		f.write(str(os.getpid()) + ', ' + str(time.time()) + '\n')
		unlock(f)
	end = time.time()
	print start,end, start-end
	
taskq = []

for i in xrange(40):
	taskq.append(threading.Thread(target = func, args = ()))
for t in taskq:
	t.setDaemon(True)
	t.start()

time.sleep(15)