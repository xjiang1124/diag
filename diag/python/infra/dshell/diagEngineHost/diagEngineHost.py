import os
import sys
import redis
import logging
from time import sleep
from .errType import errType
from inspect import currentframe, getframeinfo

#==========================================================
# Class implementation
class diagEngineHost:
    def __init__(self):
        #==========================================================
        # All the keys
        
        # CARD name dictionary, e.g. HSET CARD_DICT NIC1 NAPLES
        self.cardDictKeyFmt = 'CARD_DICT'
 
        # card key, e.g. keys EXP:CARD:NIC1*
        self.cardAllKeyFmt = 'EXP:CARD:{}*'
    
        # card key, e.g. keys EXP:CARD:NIC1*
        self.nonexpCardAllKey = 'NONEXP:CARD:*'
 
        # card key, e.g. GET EXT:CARD:CARD:NIC1:NAPLES
        self.cardKeyFmt = 'EXP:CARD:{}:{}'
     
        # DSP key, e.g. SADD/SMEMBERS DSP:NIC1:NAPLES
        self.dspKeyFmt = 'DSP:{}:{}'
          
        # DSP key, e.g. GET EXP:DSP:NIC1:NAPLES:PMBUS
        self.dspExpAllKeyFmt = 'EXP:DSP:{}:{}*'
        
        # DSP key, e.g. GET EXP:DSP:NIC1:NAPLES:PMBUS
        self.dspNonexpAllKeyFmt = 'NONEXP:DSP:*'
        
        # DSP key, e.g. GET EXP:DSP:NIC1:NAPLES:PMBUS
        self.dspExpKeyFmt = 'EXP:DSP:{}:{}:{}'

        # DSP TEST, e.g. SADD/SMEMBERS TEST:NAPLES:PMBUS
        self.dspTestKeyFmt = 'TEST:{}:{}'
 
        # DSP CMD, e.g. SADD/SMEMBERS CMD:NAPLES:PMBUS
        self.dspCmdKeyFmt = 'CMD:{}:{}'
       
        # Param key, e.g. HSET PARAM:NAPLES:PMBUS:INTR timeout 50
        self.paramKeyFmt = 'PARAM:{}:{}:{}'
         
        # Param key, e.g. HSET PARAM:NIC1:NAPLES:PMBUS:INTR timeout 50
        self.paramKeySetFmt = 'PARAM:{}:{}:{}:{}'
       
        # Test request, e.g. set TEST_ID:NIC1:PMBUS:101 INTR
        self.testKeyFmt = 'TEST_ID:{}:{}:{}'
        # Test parameter, e.g. set TEST_PARAM:NIC1:PMBUS:101 " -timeout=120 -ite=3 -mask=0x11 -dshid=3"
        self.testParamKeyFmt = 'TEST_PARAM:{}:{}:{}'
        # Test queue, e.g., lpush QUEUE:NIC1:PMBUS 101
        self.testQueKeyFmt = 'QUEUE:{}:{}'
         # Test queue status, e.g., lpush QUEUE:STATUS:NIC1:PMBUS 101
        self.testQueStsKeyFmt = 'QUEUE:STATUS:{}:{}'
       
        # Test result, e.g. GET TEST_RESULT:testId
        self.testResultKeyFmt = 'TEST_RESULT:{}'
         
        # Test history, e.g. GET HIST:NIC1:PMBUS:INTR:FAILURE
        self.testHistKeyFmt = 'HIST:{}:{}:{}:{}'
       
        # Test history, e.g. GET HIST:NIC1:PMBUS:INTR:FAILURE
        self.testHistKeyAsicFmt = 'HIST:{}:{}:{}_NIC{}:{}'

        # Test result for last test, e.g. GET RESULT:NIC1:PMBUS:INTR
        self.testLastResultKeyFmt = 'RESULT:{}:{}:{}'

        # Skip list, e.g. SADD SKIPLIST NIC1:PMBUS:INTR
        self.skiplistKey = "SKIPLIST"
        #==========================================================
        # e.g. NIC1
        self.cardName = os.environ['CARD_NAME']
        # e.g. NAPLES
        self.cardType = os.environ['CARD_TYPE']
        
        # Init redis
        redisIP = os.environ['REDIS_IP']
        pool = redis.ConnectionPool(host=redisIP, port=6379, db=0, decode_responses=True)
        self.r = redis.Redis(connection_pool=pool)

        self.dshid = self.r.incr("DSHID")

        self.errType = errType()

        self.maxNumNic = 10

        #==========================================================
        # Logger init
        self.logger = logging.getLogger('root')
        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        logging.basicConfig(format=FORMAT)
        self.logger.setLevel(logging.DEBUG)

    def __exit__(self, exc_type, exc_value, traceback):
        self.r.execute_command("QUIT")

    def getCardType(self, cardNm):
        cardType = self.r.hget(self.cardDictKeyFmt, cardNm)
        return cardType

    def parseCardInfo(self, cardNm='', dspNm='', testNm='', cmdMode=False):
        # Invalid input
        messageFmt = 'Invalid input! cardNm: {}, dspNm: {}, testNm: {}'
        if (cardNm=='' and dspNm=='' and testNm=='') or \
           (cardNm!='' and dspNm=='' and testNm!=''):
            message = messageFmt.format(cardNm, dspNm, testNm)
            self.logger.error(message)
            return [], -1
    
        cardNm = cardNm.upper()
        dspNm = dspNm.upper()
        if cmdMode == False:
            testNm = testNm.upper()
        else:
            testNm = testNm.lower()

        print("P0", cardNm, dspNm, testNm)
        # In ase cardNm is empty, take it as local card
        if cardNm == '':
            cardNm = self.cardName
        if self.checkCardExist(cardNm) == False:
            print(cardNm, "does not exit!")
            return [], -1

        cardTp = self.getCardType(cardNm)
    
        if dspNm=='':
            # cardNm pnly case: get all tests under all DSPs
            #dspList = self.r.smembers(dspKeyFmt.format(cardNm,brdNme))
            dspListTemp = self.r.keys(self.dspExpAllKeyFmt.format(cardNm, cardTp))
            dspList = []
            for dspFull in dspListTemp:
                dsp = dspFull.split(":")[4]
                # Exclude diagMgr
                if dsp == "DIAGMGR":
                    continue
                dspList.append(dsp)
        else:
            # One DSP only
            # Check whether the dsp is alive
            keyExist = self.r.exists(self.dspExpKeyFmt.format(cardNm, cardTp, dspNm))
            if keyExist == True:
                dspList = [dspNm]
            else:
                print("_NOT_ a live DSP:", dspNm)
                return [], -1

        # Get test list
        tests = []
        fmtSkipOutput = "--- {}:{}:{} is in skiplist ---"
        for dsp in dspList:
            if testNm == '':
                # Get tests per dsp
                if cmdMode == False:
                    testList = self.r.smembers(self.dspTestKeyFmt.format(self.getCardType(cardNm), dsp))
                else:
                    testList = self.r.smembers(self.dspCmdKeyFmt.format(self.getCardType(cardNm), dsp))

                for test in testList:
                    testItem = [cardNm, dsp, test]
                    tests.append(testItem)
            else:
                tests.append([cardNm, dsp, testNm])
        return tests, 0

    def parseTestParam(self, cardNm='', dspNm='', testNm='', param=dict()):
        # Get all default parameters
        brdNm = self.getCardType(cardNm)
        paramKey = self.paramKeyFmt.format(brdNm, dspNm, testNm)
        dftParamList = self.r.hkeys(paramKey)
        paramDict = dict()
        for dftParam in dftParamList:
            dftParamValue = self.r.hget(paramKey, dftParam)
            paramDict[dftParam] = dftParamValue

        # User setting with setParam command
        paramUsrKey = self.paramKeySetFmt.format(cardNm, brdNm, dspNm, testNm)
        usrParamList = self.r.hkeys(paramUsrKey)
        for usrParam in usrParamList:
            usrParamValue = self.r.hget(paramUsrKey, usrParam)
            if usrParamValue == None:
                continue
            paramDict[usrParam] = usrParamValue

        paramDict['dshid'] = self.dshid
    
        # Apply user setting to param list
        for p, v in param.items():
            paramDict[p] = v
    
        return paramDict

    def parseCmdInfo(self, cardNm='', dspNm='', testNm='', param=dict()):
        return self.parseTestInfo(cardNm, dspNm, testNm, param, True)

    def parseTestInfo(self, cardNm='', dspNm='', testNm='', param=dict(), cmdMode=False):
    #def parseTestInfo(self, cardNm='', dspNm='', testNm='', **param):
        cardNm = cardNm.upper()
        dspNm = dspNm.upper()
        if cmdMode == False:
            testNm = testNm.upper()
            print("upper")
        else:
            testNm = testNm.lower()

        testList, err = self.parseCardInfo(cardNm, dspNm, testNm, cmdMode)
        if err == -1:
            print("Failed to parse card info!")
            return [], -1
        
        paramKeyFmt = '{}:{}:{}'
        paramDict = dict()
        for test in testList:
            paramKey = paramKeyFmt.format(test[0], test[1], test[2])
            if testNm != '':
                # There should be only one entry in testList
                testParamDict = self.parseTestParam(test[0], test[1], test[2], param)
            else:
                testParamDict = self.parseTestParam(test[0], test[1], test[2])
            paramDict[paramKey] = testParamDict
        #print paramDict
    
        # Compose test entries
        testL = []
        for test in testList:
            cardN = test[0]
            dspN = test[1]
            testN = test[2]
            brdN = self.getCardType(cardN)
            paramKey = paramKeyFmt.format(cardN, dspN, testN)
            testParamDict = paramDict[paramKey]
            #print testParamDict
            paramStr = ''
            paramFmt = ' -{}={}'
            for paramN, paramV in testParamDict.items():
                paramStr = paramStr+paramFmt.format(paramN, paramV)
    
            # Leave an entry for testID and test result
            testL.append([cardN, dspN, testN, 'testId', paramStr, None])
    
        return testL, 0

    def dispatchTest (self, test):
        cardNm = test[0]
        dspNm = test[1]
        testNm = test[2]
        param = test[4]
    
        testId = self.r.incr('TEST_ID')
        test[3] = testId
    
        # Add test
        testKeyFmtStr = self.testKeyFmt.format(cardNm, dspNm, testId)
        self.r.set(testKeyFmtStr, testNm)
    
        # Add test param
        testParamKey = self.testParamKeyFmt.format(cardNm, dspNm, testId)
        self.r.set(testParamKey, param)
    
        # Dispatch to test queue
        testQueKey = self.testQueKeyFmt.format(cardNm, dspNm)
        self.r.lpush(testQueKey, testId)
        print(testQueKey)

    def remSkippedTest(self, testList):
        while(True):
            repeat = False
            for idx, test in enumerate(testList):
                cardTp = test[0]
                dspNm = test[1]
                testNm = test[2]
                if self.checkIfSkipped(cardTp, dspNm, testNm) == True:
                    fmtSkipOutput = "--- {}:{}:{} is in skiplist ---"
                    skipOutput = fmtSkipOutput.format(cardTp, dspNm, testNm)
                    print(skipOutput)
                    testList = testList[:idx]+testList[idx+1:]
                    repeat = True
                    break
            if repeat == False:
                break
        return testList

    def dispatchTestList (self, testList):
        # Check Skiplist
        testList = self.remSkippedTest(testList)

        print('=== Test started ===')
        for test in testList:
            self.dispatchTest(test)
        return testList

    def waitForTestFinish (self, testList):
        testDone = False
        fmtTestDone = "--- Test Done: {}:{}:{} ---"
        while True:
            if len(testList) == 0:
                testDone = True
            for test in testList:
                self.listenToDsp()
    
                cardNm = test[0]
                dspNm  = test[1]
                testNm = test[2]
                testId = test[3]

                testResultKey = self.testResultKeyFmt.format(testId)
                testResult = self.r.get(testResultKey)
                #print(testId, testResult)
                # Test result shows up
                if testResult != None and test[5] == None:
                    test[5] = testResult
                    testResultStr = self.errType.toName(int(testResult))
                    testDoneStr = fmtTestDone.format(cardNm, dspNm, testNm)
                    print(testDoneStr)

                    # update last test result
                    lastResultKey = self.testLastResultKeyFmt.format(cardNm, dspNm, testNm)
                    print("result:", lastResultKey, testResult)
                    self.r.set(lastResultKey, testResultStr)
    
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
            print(dspOutput)
    
    def showTestResult (self, testList):
        testResultFmt = '{:6} {:10} {:10} {:11}'
        print('=== All tests finished ===')
        print('----------------- Test Result -----------------')
        testResultStr = testResultFmt.format('CARD', 'DSP', 'TEST', 'RESULT')
        print(testResultStr)
        for test in testList:
            testR = self.errType.toName(int(test[5]))
            testResultStr = testResultFmt.format(test[0], test[1], test[2], testR)
            print(testResultStr)
        print('--------------- Test Result Done --------------')
    
    def showTestList(self, testList):
        testResultFmt = '{:<6} {:10} {:10} {:10} {}'
        print('----------------- Test List -----------------')
        testResultStr = testResultFmt.format('IDX', 'CARD', 'DSP', 'TEST', 'PARAM')
        print(testResultStr)
        idx = 0
        for test in testList:
            testResultStr = testResultFmt.format(idx, test[0], test[1], test[2], test[4])
            print(testResultStr)
            idx = idx+1
        print('--------------- Test List Done --------------')


    def runTest (self, cardName='', dspName='', testName='', param=dict()):
    
        testList, err = self.parseTestInfo(cardName, dspName, testName, param)
        if err == -1:
            print("Failed to parse test info!")
            return -1
    
        self.showTestList(testList)

        testList = self.dispatchTestList(testList)
    
        self.waitForTestFinish(testList)
        self.showTestResult(testList)

    def runCmd (self, cardName='', dspName='', testName='', param=dict()):
    
        testList, err = self.parseCmdInfo(cardName, dspName, testName, param)
        if err == -1:
            print("Failed to parse test info!")
            return -1
    
        self.showTestList(testList)

        testList = self.dispatchTestList(testList)
    
        self.waitForTestFinish(testList)
        self.showTestResult(testList)

    def paraRun(self, testItems):
        testListAll = []
        for testitem in testItems:
            testList, err = self.parseTestInfo(testitem[0], testitem[1], testitem[2], testitem[3])
            if err == -1:
                return -1
            testListAll = testListAll + testList
        #print(testListAll)
 
        self.showTestList(testListAll)

        testList = self.dispatchTestList(testListAll)
    
        self.waitForTestFinish(testListAll)
        self.showTestResult(testListAll)

    def setStopOnErr (self, stopOnErr):
        key = "STOP_ON_ERROR"
        if stopOnErr == 0:
            stopOnErrV = 0
            print("Stop_on_error disabled")
        else:
            stopOnErrV = 1
            print("Stop_on_error enabled")
        self.r.set(key, stopOnErrV)

    def checkCardExist(self, cardNm):
        key = "CARD_DICT"
        cardTp = self.r.hget(key, cardNm)
        key = self.cardKeyFmt
        return self.r.exists(key.format(cardNm, cardTp))

    def checkDspExist(self, cardNm, dspNm):
        if self.checkCardExist(cardNm) == False:
            return False

        key = "CARD_DICT"
        cardTp = self.r.hget(key, cardNm)
        key = self.dspExpKeyFmt

        #print "__DBG__", key.format(cardNm, cardTp, dspNm)
        return self.r.exists(key.format(cardNm, cardTp, dspNm))

    def getCardTpFromDict(self, cardNm):
        return self.r.hget("CARD_DICT", cardNm.upper())

    def getCardList(self, cardNm=""):
        cardNm = cardNm.upper()
        cards = []
        if cardNm == "":
            key = "EXP:CARD*"
            # Get all cards
            cardListFull = self.r.keys(key)
            for cardFull in cardListFull:
                cards.append(cardFull.split(":")[2])
        else:
            exist = self.checkCardExist(cardNm)
            if exist != True:
                print("_NOT_ a live card:", cardNm)
                return [], -1
            cards = [cardNm]
        return cards, 0

    def getDspList(self, cardNm="", dspNm=""):
        cardNm = cardNm.upper()
        if self.checkCardExist(cardNm) != True:
            print("_NOT_ a live card:", cardNm)
            return [], -1

        #print fmtDsp.format("DSP_NAME", "STATUS")
        cardTp = self.getCardTpFromDict(cardNm)
        dspListFull = self.r.keys(self.dspExpAllKeyFmt.format(cardNm, cardTp))
        dspList = []
        for dspFull in dspListFull:
            dspList.append(dspFull.split(":")[4])

        # DSP name is empty
        if not dspNm:
            return dspList, 0

        dspNm = dspNm.upper()
        if dspNm in dspList:
            return [dspNm], 0
        else:
            print("_NOT_ a valid DSP name:", dspNm)
            return [], -1

    def getTestList(self, cardNm="", dspNm="", testNm=''):
        cardNm = cardNm.upper()
        if self.checkCardExist(cardNm) != True:
            print("_NOT_ a live card:", cardNm)
            return [], -1

        dspNm = dspNm.upper()
        if self.checkDspExist(cardNm, dspNm) != True:
            print("_NOT_ a live dsp:", cardNm+":"+dspNm)
            return [], -1

        testList = self.r.smembers(self.dspTestKeyFmt.format(self.getCardType(cardNm), dspNm))

        # if given test name is empty, return whole list
        if not testNm:
            return testList, 0

        testNm = testNm.upper()
        if testNm in testList:
            return [testNm], 0
        else:
            print("_NOT_ a valid test:", testNm)
            return [], -1

    def getCmdList(self, cardNm="", dspNm="", testNm=''):
        cardNm = cardNm.upper()
        if self.checkCardExist(cardNm) != True:
            print("_NOT_ a live card:", cardNm)
            return [], -1

        dspNm = dspNm.upper()
        if self.checkDspExist(cardNm, dspNm) != True:
            print("_NOT_ a live dsp:", cardNm+":"+dspNm)
            return [], -1

        testList = self.r.smembers(self.dspCmdKeyFmt.format(self.getCardType(cardNm), dspNm))

        # if given test name is empty, return whole list
        if not testNm:
            return testList, 0

        testNm = testNm.upper()
        if testNm in testList:
            return [testNm], 0
        else:
            print("_NOT_ a valid test:", testNm)
            return [], -1


    def checkIfSkipped(self, cardTp, dspNm, testNm):
        return self.r.sismember(self.skiplistKey, cardTp+":"+dspNm+":"+testNm)

    def skip(self, cardTp="", dspNm="", testNm=""):
        cardTp = cardTp.upper()
        dspNm = dspNm.upper()
        testNm = testNm.upper()

        testList, err = self.parseCardInfo(cardTp, dspNm, testNm)
        fmtSkipMem = "{}:{}:{}"
        for test in testList:
            skipMem = fmtSkipMem.format(test[0], test[1], test[2])
            self.r.sadd(self.skiplistKey, skipMem)

    def unskip(self, cardTp="", dspNm="", testNm=""):
        cardTp = cardTp.upper()
        dspNm = dspNm.upper()
        testNm = testNm.upper()

        testList, err = self.parseCardInfo(cardTp, dspNm, testNm)
        fmtSkipMem = "{}:{}:{}"
        for test in testList:
            skipMem = fmtSkipMem.format(test[0], test[1], test[2])
            self.r.srem(self.skiplistKey, skipMem)

    def setParam(self, cardNm='', dspNm='', testNm='', paramUser=dict()):
        if cardNm == "":
            print("Please specify card name")
            return -1
        if dspNm == "":
            print("Please specify dsp name")
            return -1
        if testNm == "":
            print("Please specify test name")
            return -1

        testInfo, err = self.parseCardInfo(cardNm, dspNm, testNm)
        if err != 0:
            return -1
        cardNm = cardNm.upper()
        dspNm = dspNm.upper()
        testNm = testNm.upper()

        cardTp = self.getCardType(cardNm)
        paramKey = self.paramKeyFmt.format(cardTp, dspNm, testNm)
        for key, value in paramUser.items():
            keyExist = self.r.hexists(paramKey, key)
            if keyExist != True:
                print("Invalid parameter:", key)
            else:
                # Add parameter setting
                paramSetKey = self.paramKeySetFmt.format(cardNm, cardTp, dspNm, testNm)
                self.r.hset(paramSetKey, key, value)

#==========================================================
# Diag host status class
class diagSts(diagEngineHost):
    def __init__(self):
        diagEngineHost.__init__(self)

    def showCard (self):
        key = "EXP:CARD*"
        fmtShowCard = "{:<15}{:<15}{}"
        fmtKeyDsp = "EXP:DSP:{}*"
        print("========================================")
        #print showCardStr
        #print "----------------------------------------"
        cards = self.r.keys(key)
        for card in cards:
            cardName = card.split(':')[2]
            cardType = card.split(':')[3]
            if cardType != 'HOST':
                cardSts = "idle"
                keyDsp = fmtKeyDsp.format(cardName)
                dspFullList = self.r.keys(keyDsp) 
                for dspFull in dspFullList:
                    dsp = dspFull.split(":")[4]
                    testQueStsKey = self.testQueStsKeyFmt.format(cardName, dsp)
                    queSts = self.r.llen(testQueStsKey)
                    if queSts > 0:
                        cardSts = "active"

                showCardStr = fmtShowCard.format(cardName, cardType, cardSts)
                print(showCardStr)

        #print "========================================"
        return 0

    def showDsp (self, cardNm=""):
        cards, err = self.getCardList(cardNm)
        if err != 0:
            return

        # Display DSPs
        for card in cards:
            fmtCard = "============ {}:{} ============"
            cardTp = self.getCardTpFromDict(card)
            print(fmtCard.format(card, cardTp))
            fmtDsp = "{:<20}{}"
            #print fmtDsp.format("DSP_NAME", "STATUS")
            dspListFull = self.r.keys(self.dspExpAllKeyFmt.format(card, cardTp))
            for dspFull in dspListFull:
                dsp = dspFull.split(":")[4]
                if dsp == "DIAGMGR":
                    continue
                # Get DSP status
                testQueStsKey = self.testQueStsKeyFmt.format(card, dsp)
                queSts = self.r.llen(testQueStsKey)
                if queSts <= 0:
                    sts = "idle"
                else:
                    sts = "active"

                print(fmtDsp.format(dsp, sts))
        return

    def showCmd (self, cardNm="", dspNm=""):
        dspNm = dspNm.upper()
        cards, err = self.getCardList(cardNm)
        if err != 0:
            return

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTest = "{:<20}{}"
        # Display DSPs
        for card in cards:
            cardTp = self.getCardTpFromDict(card)
            print(fmtCard.format(card, cardTp))
            dspList, err = self.getDspList(card)
            if err != 0:
                return
            for dsp in dspList:
                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                print(fmtDsp.format(dsp))
                testList, err = self.getCmdList(card, dsp)
                if err != 0:
                    continue
                # Get DSP status
                testQueStsKey = self.testQueStsKeyFmt.format(card, dsp)
                queSts = self.r.llen(testQueStsKey)

                for test in testList:
                    sts = "idle"
                    if queSts > 0:
                        testId = self.r.lindex(testQueStsKey, -1)
                        testStr = self.testKeyFmt.format(card, dsp, testId)
                        testNm = self.r.get(testStr)
                        if test == testNm:
                            sts = "active"

                    print(fmtTest.format(test, sts))
        return

    def showTest (self, cardNm="", dspNm=""):
        dspNm = dspNm.upper()
        cards, err = self.getCardList(cardNm)
        if err != 0:
            return

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTest = "{:<20}{}"
        # Display DSPs
        for card in cards:
            cardTp = self.getCardTpFromDict(card)
            print(fmtCard.format(card, cardTp))
            dspList, err = self.getDspList(card)
            if err != 0:
                return
            for dsp in dspList:
                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                print(fmtDsp.format(dsp))
                testList, err = self.getTestList(card, dsp)
                if err != 0:
                    continue
                # Get DSP status
                testQueStsKey = self.testQueStsKeyFmt.format(card, dsp)
                queSts = self.r.llen(testQueStsKey)

                for test in testList:
                    sts = "idle"
                    if queSts > 0:
                        testId = self.r.lindex(testQueStsKey, -1)
                        testStr = self.testKeyFmt.format(card, dsp, testId)
                        testNm = self.r.get(testStr)
                        if test == testNm:
                            sts = "active"

                    print(fmtTest.format(test, sts))
        return

    def showHist (self, cardNm="", dspNm="", mode="nor"):
        cardList, err = self.getCardList(cardNm)
        if err != 0:
            return -1

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTestHist = "{:<18}{:<10}{:<10}{:<10}"
        for card in cardList: 
            cardNm = self.getCardTpFromDict(card)
            print(fmtCard.format(card, cardNm))
            dspList, err = self.getDspList(card)
            if err != 0:
                continue

            testHistStr = fmtTestHist.format("TEST_NAME", "PASS", "FAIL", "TIMEOUT")
            print(testHistStr)
            for dsp in dspList:

                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                if (dsp != "ASIC") or (mode == "nor"):
                    print(fmtDsp.format(dsp))
                    testList, err = self.getTestList(card, dsp)
                    if err != 0:
                        continue

                    for test in testList:
                        testHistKey = self.testHistKeyFmt.format(card, dsp, test, "SUCCESS")
                        histSucc = self.r.get(testHistKey)
                        if histSucc == None:
                            histSucc = 0

                        testHistKey = self.testHistKeyFmt.format(card, dsp, test, "FAILURE")
                        histFail = self.r.get(testHistKey)
                        if histFail == None:
                            histFail = 0

                        testHistKey = self.testHistKeyFmt.format(card, dsp, test, "TIMEOUT")
                        histTout = self.r.get(testHistKey)
                        if histTout == None:
                            histTout = 0
                        
                        testHistStr = fmtTestHist.format(test, histSucc, histFail, histTout)
                        print(testHistStr)
                else: # ASIC on MTP
                    for nicIdx in range(1, self.maxNumNic+1):
                        print(fmtDsp.format(dsp+"_NIC"+str(nicIdx)))
                        testList, err = self.getTestList(card, dsp)
                        if err != 0:
                            continue

                        for test in testList:
                            testHistKey = self.testHistKeyAsicFmt.format(card, dsp, test, nicIdx, "SUCCESS")
                            histSucc = self.r.get(testHistKey)
                            if histSucc == None:
                                histSucc = 0

                            testHistKey = self.testHistKeyAsicFmt.format(card, dsp, test, nicIdx, "FAILURE")
                            histFail = self.r.get(testHistKey)
                            if histFail == None:
                                histFail = 0

                            testHistKey = self.testHistKeyAsicFmt.format(card, dsp, test, nicIdx, "TIMEOUT")
                            histTout = self.r.get(testHistKey)
                            if histTout == None:
                                histTout = 0
                            
                            testHistStr = fmtTestHist.format(test, histSucc, histFail, histTout)
                            print(testHistStr)


    def showResult (self, cardNm="", dspNm="", testNm=""):
        cardList, err = self.getCardList(cardNm)
        if err != 0:
            return -1

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTestResult = "{:<15}{:<10}"
        for card in cardList: 
            cardNm = self.getCardTpFromDict(card)
            print(fmtCard.format(card, cardNm))
            dspList, err = self.getDspList(card, dspNm)
            if err != 0:
                continue

            testResultStr = fmtTestResult.format("TEST_NAME", "RESULT")
            print(testResultStr)
            for dsp in dspList:

                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                print(fmtDsp.format(dsp))
                testList, err = self.getTestList(card, dsp, testNm)
                if err != 0:
                    continue

                for test in testList:
                    testResultKey = self.testLastResultKeyFmt.format(card, dsp, test)
                    testResult = self.r.get(testResultKey)
                    if testResult == None:
                        testResult = "Not Tested"
                    
                    testResultStr = fmtTestResult.format(test, testResult)
                    print(testResultStr)

    def showSkip(self):
        skipMems = self.r.smembers(self.skiplistKey)
        print("======== Skip List =======")
        for skip in skipMems:
            #[card, dsp, test] = skip.split(":")
            print(skip)

    def showParam(self, cardNm="", dspNm="", testNm=""):
        if cardNm == "":
            print("Please specify card name")
            return -1
        if dspNm == "":
            print("Please specify dsp name")
            return -1
        if testNm == "":
            print("Please specify test name")
            return -1

        testInfo, err = self.parseCardInfo(cardNm, dspNm, testNm)
        if err != 0:
            return -1

        cardNm = cardNm.upper()
        dspNm = dspNm.upper()
        testNm = testNm.upper()
        cardTp = self.getCardType(cardNm)

        paramKey = self.paramKeyFmt.format(cardTp, dspNm, testNm)
        paramNames = self.r.hkeys(paramKey)

        paramSetKey = self.paramKeySetFmt.format(cardNm, cardTp, dspNm, testNm)

        title = "===== {}:{}:{}:{} =====".format(cardNm, cardTp, dspNm, testNm)
        print(title)

        for key in paramNames:
            val = self.r.hget(paramKey, key)
            valSet = self.r.hget(paramSetKey, key)
            print("----------")
            print("name:", key)
            print("default:", val)
            print("User setting:", valSet)


    # Clean up system
    def cleanSys(self):
        dshbufList = self.r.keys("dshbuf*")
        for dshbuf in dshbufList:
            self.r.delete(dshbuf)
        print("dshbuf cleared")

        queList = self.r.keys("QUEUE:")
        for que in queList:
            self.r.delete(que)
        print("que cleared")


    # Clean up system
    def cleanHist(self):
        histList = self.r.keys("HIST:*")
        for hist in histList:
            self.r.delete(hist)
        print("Test history cleared")

    # Find Lost card
    def findLostCard(self):
        print('--------------- Lost Card --------------')
        lostCardFmt = '{:<10}    {:<10}'
        nonexpKeys = self.r.keys(self.nonexpCardAllKey)
        for card in nonexpKeys:
            cardNm = card.split(":")[2]
            cardTp = card.split(":")[3]

            keyExist = self.r.exists(self.cardKeyFmt.format(cardNm, cardTp))
            if keyExist == False:
                lostCardStr = lostCardFmt.format(cardNm, cardTp)
                print(lostCardStr)
        print('------------ Lost Card Done ------------')

    # Find Lost card
    def findLostDsp(self):
        cardFmt = "============ {}:{} ============"

        print('--------------- Lost DSP --------------')
        nonexpKeys = self.r.keys(self.dspNonexpAllKeyFmt)
        for idx, cardDsp in enumerate(nonexpKeys):
            cardNm = cardDsp.split(":")[2]
            cardTp = cardDsp.split(":")[3]
            dsp    = cardDsp.split(":")[4]

            keyExist = self.r.exists(self.dspExpKeyFmt.format(cardNm, cardTp, dsp))
            if keyExist == False:
                if idx == 0:
                    cardStr = cardFmt.format(cardNm, cardTp)
                    print(CardStr)
                print(dsp)
        print('------------ Lost DSP Done ------------')

