#!/usr/bin/env python

import sys
import time
#from concurrent.futures import ThreadPoolExecutor as Executor
from concurrent.futures import ProcessPoolExecutor as Executor
from time import sleep
from IPython.core.debugger import Pdb

def stop_process_pool(executor):
    print "P0"
    #Pdb.set_trace()
    print executor._processs.items()
    for pid, thread in executor._processs.items():
        print "P1", pid
        thread.terminate()
    print "P2"
    executor.shutdown()

#def timeout_func(self, fnc, *args, **kwargs):
def timeout_func(fnc, *args, **kwargs):
    with Executor() as p:
        f = p.submit(fnc, *args)
        #print kwargs["timeout"]
        #future = concurrent.futures.as_completed(f)
        try:
            #concurrent.futures.as_completed(func(*args), timeout=swargs["timeout"])
            #ret = furure.result(timeout=kwargs["timeout"])
            print f.result(timeout=kwargs["timeout"])

        #except concurrent.futures._base.TimeoutError:
        except:
            print "Timeout happend"
            #f.cancel()
            stop_process_pool(f)
            print "hello"
            ret = -1
        else:
            print "ret:", 0
            ret = 0

    return ret
        #return f.result(timeout=kwargs["timeout"])

#def someFunc(tempArg=123, timeout=0):
def someFunc(tempArg):
    print time.time(), "before", tempArg
    for i in range(tempArg):
        print "idx:", i
        sleep(1)
    print time.time(), "after", tempArg
    return 0

#def topTest(func, *args, **kwargs):
def topTest(*args, **kwargs):
    try:
        ret = timeout_func(someFunc, *args, **kwargs)
    except:
        ret = -1

    return ret

#ret = topTest(someFunc, 1, timeout=2)
#print ret
#sys.exit()
print "============"

with Executor() as executor:
    f1 = executor.submit(topTest, 5, timeout=1)
    #f2 = executor.submit(topTest, 1, timeout=2)
    val1 = f1.result()
    #val2 = f2.result()

#print val1, val2
print val1
sys.exit()
print "============"

def multiTests(func, *args, **kwargs):
    with Executor() as executor:
        f1 = executor.submit(func, *args, **kwargs)
        val1 = f1.result()
        print "val1:", val1

    #print val1
    
multiTests(topTest, 2, timeout=1)

#ret = timeout_func(someFunc, 1, timeout=10)
#print ret
