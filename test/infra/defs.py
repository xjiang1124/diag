#!/usr/bin/python3


from enum import IntEnum


class Result(IntEnum):
    SUCCESS                 = 0
    TESTCASE_FAILURE        = 1
    TESTBED_FAILURE         = 2
    INFRA_FAILURE           = 3
