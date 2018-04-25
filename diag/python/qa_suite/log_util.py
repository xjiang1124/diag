#!/usr/bin/env python
import sys

file_name = sys.argv[1]
pass_signature = "TEST PASSED!"
fail_signature = "TEST FAILED!"
pass_cnt = 0
fail_cnt = 0

f = open(file_name, "w")

for line in sys.stdin:
    if pass_signature in line:
        pass_cnt += 1
    elif fail_signature in line:
        fail_cnt += 1
        #print(line)
    print(line)
    f.write(line)

print("Passed {} tests, failed {} tests".format(pass_cnt, fail_cnt))

f.close()
