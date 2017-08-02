#!/usr/bin/env python

import os
import sys
import redis
import logging
from time import sleep

from IPython import embed
from traitlets.config.loader import Config
from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.embed import InteractiveShellEmbed

#==========================================================
# Logger init
logger = logging.getLogger('root')
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

#==========================================================
# All the keys

# CARD name dictionary, e.g. HSET CARD_DICT NIC1 NAPLES
cardDictKey = 'CARD_DICT'

# DSP key, e.g. SADD/SMEMBERS DSP:NIC1:NAPLES
dspKey = 'DSP:{}:{}'

# DSP TEST, e.g. SADD/SMEMBERS TEST:NAPLES:PMBUS
dspTestKey = 'TEST:{}:{}'

# Param key, e.g. HSET PARAM:NAPLES:PMBUS:INTR timeout 50
paramKey = 'PARAM:{}:{}:{}'

# Test request, e.g. set TEST_ID:NIC1:PMBUS:101 INTR
testKey = 'TEST_ID:{}:{}:{}'
# Test parameter, e.g. set TEST_PARAM:NIC1:PMBUS:101 " -timeout=120 -ite=3 -mask=0x11 -dshid=3"
testParamKey = 'TEST_PARAM:{}:{}:{}'
# Test queue, e.g., lpush QUEUE:NIC1:PMBUS 101
testQueKey = 'QUEUE:{}:{}'

# Test result, e.g. GET TEST_RESULT:testId
testResultKey = 'TEST_RESULT:{}'

#==========================================================
# e.g. NIC1
cardName = os.environ['CARD_TYPE']
# e.g. NAPLES
brdName = os.environ['CARD_NAME']

# Init redis
redisIP = os.environ['REDIS_IP']
r = redis.StrictRedis(host=redisIP, port=6379, db=0)

#==========================================================
def getBrdName(cardNm):
    brdNm = r.hget(cardDictKey, cardNm)
    return brdNm

def parseCardInfo(cardNm='', dspNm='', testNm=''):
    # Invalid input
    messageFmt = 'Invalid input! cardNm: {}, dspNm: {}, testNm: {}'
    if (cardNm=='' and dspNm=='' and testNm=='') or \
       (cardNm!='' and dspNm=='' and testNm!=''):
        message = messageFmt.format(cardNm, dspNm, testNm)
        print cardNm=='', dspNm=='', testNm==''
        logger.error(message)
        return -1

    # In ase cardNm is empty, take it as local card
    if cardNm == '':
        cardNm = cardName
    brdNm = getBrdName(cardNm)

    if dspNm=='':
        # cardNm pnly case: get all tests under all DSPs
        dspList = r.smembers(dspKey.format(cardNm,brdNme))
    else:
        # One DSP only
        dspList = [dspNm]
    print dspList

    # Get test list
    tests = []
    for dsp in dspList:
        if testNm == '':
            # Get tests per dsp
            testList = r.smembers(dspTestKey.format(brdName, dsp))
            for test in testList:
                testItem = [cardNm, dsp, test]
                tests.append(testItem)
        else:
            tests.append([cardNm, dsp, testNm])
    return tests

def parseTestParam(cardNm='', dspNm='', testNm='', param=dict()):
    # Get all default parameters
    brdNm = getBrdName(cardNm)
    paramKeyStr = paramKey.format(brdNm, dspNm, testNm)
    dftParamList = r.hkeys(paramKeyStr)
    paramDict = dict()
    for dftParam in dftParamList:
        dftParamValue = r.hget(paramKeyStr, dftParam)
        paramDict[dftParam] = dftParamValue

    # Apply user setting to param list
    for p, v in param.items():
        paramDict[p] = v

    return paramDict

def parseTestInfo(cardNm='', dspNm='', testNm='', param=dict()):
    cardNm = cardNm.upper()
    dspNm = dspNm.upper()
    testNm = testNm.upper()
    testList = parseCardInfo(cardNm, dspNm, testNm)
    print testList
    
    paramKey = '{}:{}:{}'
    paramDict = dict()
    for test in testList:
        paramKeyStr = paramKey.format(test[0], test[1], test[2])
        if testNm != '':
            # There should be only one entry in testList
            testParamDict = parseTestParam(test[0], test[1], test[2], param)
        else:
            testParamDict = parseTestParam(test[0], test[1], test[2])
        paramDict[paramKeyStr] = testParamDict

    # Compose test entries
    testL = []
    for test in testList:
        cardN = test[0]
        dspN = test[1]
        testN = test[2]
        brdN = getBrdName(cardN)
        paramKeyStr = paramKey.format(cardN, dspN, testN)
        testParamDict = paramDict[paramKeyStr]
        #print testParamDict
        paramStr = ''
        paramFmt = ' -{}={}'
        for paramN, paramV in testParamDict.items():
            paramStr = paramStr+paramFmt.format(paramN, paramV)
        paramStr = paramStr+paramFmt.format('dshid', dshid)

        # Leave an entry for testID and test result
        testL.append([cardN, dspN, testN, 'testId', paramStr, None])

    return testL

def dispatchTest(test):
    cardNm = test[0]
    dspNm = test[1]
    testNm = test[2]
    param = test[4]

    testId = r.incr('TEST_ID')
    test[3] = testId

    # Add test
    testKeyStr = testKey.format(cardNm, dspNm, testId)
    r.set(testKeyStr, testNm)

    # Add test param
    testParamKeyStr = testParamKey.format(cardNm, dspNm, testId)
    r.set(testParamKeyStr, param)

    # Dispatch to test queue
    testQueKeyStr = testQueKey.format(cardNm, dspNm)
    r.lpush(testQueKeyStr, testId)

def dispatchTestList (testList):
    for test in testList:
        dispatchTest(test)

def waitForTestFinish (testList):
    testDone = False
    while True:
        for test in testList:
            listenToDsp()

            testId = test[3]
            testResultKeyStr = testResultKey.format(testId)
            testResult = r.get(testResultKeyStr)
            # Test result shows up
            if testResult != None:
                test[5] = testResult

        # Check whether all tests have result back
        for test in testList:
            if test[5] == None:
                testDone = False
                break;
            testDone = True

        # All test done, exit while loop
        if testDone == True:
            break
    listenToDsp()

def listenToDsp ():
    while True:
        dspOutput = r.rpop ('dshbuf:'+str(dshid))
        if dspOutput == None:
            break
        print dspOutput

def showTestResult (testList):
    testResultFmt = '{:6} {:10} {:10} {:>10}'
    print 'All tests finished'
    print '----------------- Test Result -----------------'
    testResultStr = testResultFmt.format('CARD', 'DSP', 'TEST', 'RESULT')
    print testResultStr
    for test in testList:
        if test[5] == 0:
            testR = 'PASS'
        else:
            testR = "FAIL"
        testResultStr = testResultFmt.format(test[0], test[1], test[2], test[5])
        print testResultStr
    print '--------------- Test Result Done --------------'

def runTest (cardName='', dspName='', testName='', **param):

    testList = parseTestInfo(cardName, dspName, testName, param)

    dispatchTestList(testList)

    waitForTestFinish (testList)
    showTestResult(testList)


#==========================================================
# Start inter active mode
dshid = r.incr("DSHID")
promptStr = 'DiagSH[{}]'
prompt = promptStr.format(dshid)

class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, prompt)]
    def out_prompt_tokens(self, cli=None):
        return [(Token.Prompt, prompt)]

try:
    get_ipython
except NameError:
    banner  ='Entering Diag Shell'
    exit_msg = 'Exiting Diag Shell' 
    cfg = Config()
    prompt_config = cfg.TerminalInteractiveShell.prompts_class
    prompt_config.in_template = 'DiagSH: '
    
else:
    banner = '*** Nested DiagSHELL ***'
    exit_msg = '*** Back in main DiagSHELL ***'

ipshell = InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg)

ipshell.prompts = MyPrompt(ipshell)

ipshell()


