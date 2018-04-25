#!/usr/bin/env python

import sys
import time
#from concurrent.futures import ThreadPoolExecutor as Executor
from concurrent.futures import ProcessPoolExecutor as Executor
from time import sleep
from pebble import concurrent

from pebble import ProcessPool
from concurrent.futures import TimeoutError

def function(foo, bar=0):
    for i in range(5):
        print time.time(), "idx:", i, foo, bar
        sleep(1)

    return foo + bar

def task_done(future):
    try:
        future.result()  # blocks until results are ready
    except TimeoutError as error:
        print("Function took longer than %d seconds" % error.args[1])
    except Exception as error:
        print("Function raised %s" % error)
        print(error.traceback)  # traceback of the function

with ProcessPool(max_workers=20, max_tasks=6) as pool:
    for i in range(0, 5):
        future = pool.schedule(function, args=[i, 30-i], timeout=2)
        future.add_done_callback(task_done)

sys.exit()

#@concurrent.thread(timeout=10)
@concurrent.process(timeout=10)
def someFunc(tempArg):
    print time.time(), "before", tempArg
    for i in range(tempArg):
        print "idx:", i
        sleep(1)
    print time.time(), "after", tempArg
    return 0

print "Hello"
future = someFunc(3)
ret = future.result()
print "ret:", ret
