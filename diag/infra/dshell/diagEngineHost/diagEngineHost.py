import os
import sys
import redis
import logging
from time import sleep
from errType import errType

#==========================================================
# Class implementation
class diagEngineHost:
    def __init__(self):
        #==========================================================
        # All the keys
        
        # CARD name dictionary, e.g. HSET CARD_DICT NIC1 NAPLES
        self.cardDictKey = 'CARD_DICT'
        
        # DSP key, e.g. SADD/SMEMBERS DSP:NIC1:NAPLES
        self.dspKey = 'DSP:{}:{}'
        
        # DSP TEST, e.g. SADD/SMEMBERS TEST:NAPLES:PMBUS
        self.dspTestKey = 'TEST:{}:{}'
        
        # Param key, e.g. HSET PARAM:NAPLES:PMBUS:INTR timeout 50
        self.paramKey = 'PARAM:{}:{}:{}'
        
        # Test request, e.g. set TEST_ID:NIC1:PMBUS:101 INTR
        self.testKey = 'TEST_ID:{}:{}:{}'
        # Test parameter, e.g. set TEST_PARAM:NIC1:PMBUS:101 " -timeout=120 -ite=3 -mask=0x11 -dshid=3"
        self.testParamKey = 'TEST_PARAM:{}:{}:{}'
        # Test queue, e.g., lpush QUEUE:NIC1:PMBUS 101
        self.testQueKey = 'QUEUE:{}:{}'
        
        # Test result, e.g. GET TEST_RESULT:testId
        self.testResultKey = 'TEST_RESULT:{}'
        
        #==========================================================
        # e.g. NIC1
        self.cardName = os.environ['CARD_TYPE']
        # e.g. NAPLES
        self.brdName = os.environ['CARD_NAME']
        
        # Init redis
        redisIP = os.environ['REDIS_IP']
        self.r = redis.StrictRedis(host=redisIP, port=6379, db=0)

        self.dshid = self.r.incr("DSHID")

        self.errType = errType()

        #==========================================================
        # Logger init
        self.logger = logging.getLogger('root')
        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        logging.basicConfig(format=FORMAT)
        self.logger.setLevel(logging.DEBUG)

    def __exit__(self, exc_type, exc_value, traceback):
        self.r.execute_command("QUIT")

    def getBrdName(self, cardNm):
        brdNm = self.r.hget(self.cardDictKey, cardNm)
        return brdNm

    def parseCardInfo(self, cardNm='', dspNm='', testNm=''):
        # Invalid input
        messageFmt = 'Invalid input! cardNm: {}, dspNm: {}, testNm: {}'
        if (cardNm=='' and dspNm=='' and testNm=='') or \
           (cardNm!='' and dspNm=='' and testNm!=''):
            message = messageFmt.format(cardNm, dspNm, testNm)
            self.logger.error(message)
            return -1
    
        # In ase cardNm is empty, take it as local card
        if cardNm == '':
            cardNm = cardName
        brdNm = self.getBrdName(cardNm)
    
        if dspNm=='':
            # cardNm pnly case: get all tests under all DSPs
            dspList = self.r.smembers(dspKey.format(cardNm,brdNme))
        else:
            # One DSP only
            dspList = [dspNm]
    
        # Get test list
        tests = []
        for dsp in dspList:
            if testNm == '':
                # Get tests per dsp
                testList = self.r.smembers(self.dspTestKey.format(self.brdName, dsp))
                for test in testList:
                    testItem = [cardNm, dsp, test]
                    tests.append(testItem)
            else:
                tests.append([cardNm, dsp, testNm])
        return tests

    def parseTestParam(self, cardNm='', dspNm='', testNm='', param=dict()):
        # Get all default parameters
        brdNm = self.getBrdName(cardNm)
        paramKeyStr = self.paramKey.format(brdNm, dspNm, testNm)
        dftParamList = self.r.hkeys(paramKeyStr)
        paramDict = dict()
        for dftParam in dftParamList:
            dftParamValue = self.r.hget(paramKeyStr, dftParam)
            paramDict[dftParam] = dftParamValue
        paramDict['dshid'] = self.dshid
    
        # Apply user setting to param list
        for p, v in param.items():
            paramDict[p] = v
    
        return paramDict

    def parseTestInfo(self, cardNm='', dspNm='', testNm='', param=dict()):
    #def parseTestInfo(self, cardNm='', dspNm='', testNm='', **param):
        cardNm = cardNm.upper()
        dspNm = dspNm.upper()
        testNm = testNm.upper()
        testList = self.parseCardInfo(cardNm, dspNm, testNm)
        if testList == -1:
            return -1
        #print testList
        
        paramKey = '{}:{}:{}'
        paramDict = dict()
        for test in testList:
            paramKeyStr = paramKey.format(test[0], test[1], test[2])
            if testNm != '':
                # There should be only one entry in testList
                testParamDict = self.parseTestParam(test[0], test[1], test[2], param)
            else:
                testParamDict = self.parseTestParam(test[0], test[1], test[2])
            paramDict[paramKeyStr] = testParamDict
        #print paramDict
    
        # Compose test entries
        testL = []
        for test in testList:
            cardN = test[0]
            dspN = test[1]
            testN = test[2]
            brdN = self.getBrdName(cardN)
            paramKeyStr = paramKey.format(cardN, dspN, testN)
            testParamDict = paramDict[paramKeyStr]
            #print testParamDict
            paramStr = ''
            paramFmt = ' -{}={}'
            for paramN, paramV in testParamDict.items():
                paramStr = paramStr+paramFmt.format(paramN, paramV)
    
            # Leave an entry for testID and test result
            testL.append([cardN, dspN, testN, 'testId', paramStr, None])
    
        return testL

    def dispatchTest (self, test):
        cardNm = test[0]
        dspNm = test[1]
        testNm = test[2]
        param = test[4]
    
        testId = self.r.incr('TEST_ID')
        test[3] = testId
    
        # Add test
        testKeyStr = self.testKey.format(cardNm, dspNm, testId)
        self.r.set(testKeyStr, testNm)
    
        # Add test param
        testParamKeyStr = self.testParamKey.format(cardNm, dspNm, testId)
        self.r.set(testParamKeyStr, param)
    
        # Dispatch to test queue
        testQueKeyStr = self.testQueKey.format(cardNm, dspNm)
        self.r.lpush(testQueKeyStr, testId)

    def dispatchTestList (self, testList):
        print '=== Test started ==='
        for test in testList:
            self.dispatchTest(test)

    def waitForTestFinish (self, testList):
        testDone = False
        while True:
            for test in testList:
                self.listenToDsp()
    
                testId = test[3]
                testResultKeyStr = self.testResultKey.format(testId)
                testResult = self.r.get(testResultKeyStr)
                #print testId, testResult
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
        self.listenToDsp()
    
    def listenToDsp (self):
        while True:
            dspOutput = self.r.rpop ('dshbuf:'+str(self.dshid))
            if dspOutput == None:
                break
            print dspOutput
    
    def showTestResult (self, testList):
        testResultFmt = '{:6} {:10} {:10} {:10}'
        print '=== All tests finished ==='
        print '----------------- Test Result -----------------'
        testResultStr = testResultFmt.format('CARD', 'DSP', 'TEST', 'RESULT')
        print testResultStr
        for test in testList:
            #if test[5] == '0':
            #    testR = 'PASS'
            #elif test[5] == '48879': # skip signature
            #    testR = 'SKIP'
            #else:
            #    testR = "FAIL"
            testR = self.errType.toName(int(test[5]))
            testResultStr = testResultFmt.format(test[0], test[1], test[2], testR)
            print testResultStr
        print '--------------- Test Result Done --------------'
    
    def showTestList(self, testList):
        testResultFmt = '{:<6} {:10} {:10} {:10} {}'
        print '----------------- Test List -----------------'
        testResultStr = testResultFmt.format('IDX', 'CARD', 'DSP', 'TEST', 'PARAM')
        print testResultStr
        idx = 0
        for test in testList:
            testResultStr = testResultFmt.format(idx, test[0], test[1], test[2], test[4])
            print testResultStr
            idx = idx+1
        print '--------------- Test List Done --------------'


    def runTest (self, cardName='', dspName='', testName='', param=dict()):
    
        testList = self.parseTestInfo(cardName, dspName, testName, param)
        if testList == -1:
            return -1
    
        self.showTestList(testList)

        self.dispatchTestList(testList)
    
        self.waitForTestFinish(testList)
        self.showTestResult(testList)

    def setStopOnErr (self, stopOnErr):
        key = "STOP_ON_ERROR"
        if stopOnErr == 0:
            stopOnErrV = 0
            print "Stop_on_error disabled"
        else:
            stopOnErrV = 1
            print "Stop_on_error enabled"
        self.r.set(key, stopOnErrV)

    def showCard (self):
        key = "EXP:CARD*"
        cards = self.r.keys(key)
        print cards
        return 0

