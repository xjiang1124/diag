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
        self.cardDictKeyFmt = 'CARD_DICT'
  
        # card key, e.g. keys EXP:CARD:NIC1*
        self.cardAllKeyFmt = 'EXP:CARD:{}*'
   
        # card key, e.g. GET EXT:CARD:CARD:NIC1:NAPLES
        self.cardKeyFmt = 'EXP:CARD:{}:{}'
     
        # DSP key, e.g. SADD/SMEMBERS DSP:NIC1:NAPLES
        self.dspKeyFmt = 'DSP:{}:{}'
         
        # DSP key, e.g. GET EXP:DSP:NIC1:NAPLES:PMBUS
        self.dspExpAllKeyFmt = 'EXP:DSP:{}:{}*'
        
        # DSP key, e.g. GET EXP:DSP:NIC1:NAPLES:PMBUS
        self.dspExpKeyFmt = 'EXP:DSP:{}:{}:{}'

        # DSP TEST, e.g. SADD/SMEMBERS TEST:NAPLES:PMBUS
        self.dspTestKeyFmt = 'TEST:{}:{}'
        
        # Param key, e.g. HSET PARAM:NAPLES:PMBUS:INTR timeout 50
        self.paramKeyFmt = 'PARAM:{}:{}:{}'
        
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
        brdNm = self.r.hget(self.cardDictKeyFmt, cardNm)
        return brdNm

    def parseCardInfo(self, cardNm='', dspNm='', testNm=''):
        # Invalid input
        messageFmt = 'Invalid input! cardNm: {}, dspNm: {}, testNm: {}'
        if (cardNm=='' and dspNm=='' and testNm=='') or \
           (cardNm!='' and dspNm=='' and testNm!=''):
            message = messageFmt.format(cardNm, dspNm, testNm)
            self.logger.error(message)
            return [], -1
    
        # In ase cardNm is empty, take it as local card
        if cardNm == '':
            cardNm = self.cardName
        if self.checkCardExist(cardNm) == False:
            return [], -1

        brdNm = self.getBrdName(cardNm)
    
        if dspNm=='':
            # cardNm pnly case: get all tests under all DSPs
            #dspList = self.r.smembers(dspKeyFmt.format(cardNm,brdNme))
            dspListTemp = self.r.keys(self.dspExpAllKeyFmt.format(cardNm, brdNm))
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
            keyExist = self.r.exists(self.dspExpKeyFmt.format(cardNm, brdNm, dspNm))
            if keyExist == True:
                #if dspNm == "DIAGMGR":
                #    print "DIAGMGR is not an active DSP"
                #    return [], -1
                dspList = [dspNm]
            else:
                print "_NOT_ a live DSP:", dspNm
                return [], -1

        # Get test list
        tests = []
        for dsp in dspList:
            if testNm == '':
                # Get tests per dsp
                testList = self.r.smembers(self.dspTestKeyFmt.format(self.brdName, dsp))
                for test in testList:
                    testItem = [cardNm, dsp, test]
                    tests.append(testItem)
            else:
                tests.append([cardNm, dsp, testNm])
        return tests, 0

    def parseTestParam(self, cardNm='', dspNm='', testNm='', param=dict()):
        # Get all default parameters
        brdNm = self.getBrdName(cardNm)
        paramKey = self.paramKeyFmt.format(brdNm, dspNm, testNm)
        dftParamList = self.r.hkeys(paramKey)
        paramDict = dict()
        for dftParam in dftParamList:
            dftParamValue = self.r.hget(paramKey, dftParam)
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
        testList, err = self.parseCardInfo(cardNm, dspNm, testNm)
        if err == -1:
            return [], -1
        #print testList
        
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
            brdN = self.getBrdName(cardN)
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

    def dispatchTestList (self, testList):
        print '=== Test started ==='
        for test in testList:
            self.dispatchTest(test)

    def waitForTestFinish (self, testList):
        testDone = False
        fmtTestDone = "--- Test Done: {}:{}:{} ---"
        while True:
            for test in testList:
                self.listenToDsp()
    
                testId = test[3]
                testResultKey = self.testResultKeyFmt.format(testId)
                testResult = self.r.get(testResultKey)
                #print testId, testResult
                # Test result shows up
                if testResult != None and test[5] == None:
                    test[5] = testResult
                    testDoneStr = fmtTestDone.format(test[0], test[1], test[2])
                    print testDoneStr
    
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
        testResultFmt = '{:6} {:10} {:10} {:11}'
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
    
        testList, err = self.parseTestInfo(cardName, dspName, testName, param)
        if err == -1:
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

    def checkCardExist(self, cardTp):
        key = "CARD_DICT"
        cardNm = self.r.hget(key, cardTp)
        key = self.cardKeyFmt
        return self.r.exists(key.format(cardTp, cardNm))

    def checkDspExist(self, cardTp, dspNm):
        if self.checkCardExist(cardTp) == False:
            return False

        key = "CARD_DICT"
        cardNm = self.r.hget(key, cardTp)
        key = self.dspExpKeyFmt

        return self.r.exists(key.format(cardTp, cardNm, dspNm))

    def getCardNmFromDict(self, cardTp):
        return self.r.hget("CARD_DICT", cardTp.upper())

    def getCardList(self, cardTp=""):
        cardTp = cardTp.upper()
        cards = []
        if cardTp == "":
            key = "EXP:CARD*"
            # Get all cards
            cardListFull = self.r.keys(key)
            for cardFull in cardListFull:
                cards.append(cardFull.split(":")[2])
        else:
            exist = self.checkCardExist(cardTp)
            if exist != True:
                print "_NOT_ a live card:", cardTp
                return [], -1
            cards = [cardTp]
        return cards, 0

    def getDspList(self, cardTp=""):
        cardTp = cardTp.upper()
        if self.checkCardExist(cardTp) != True:
            print "_NOT_ a live card:", cardTp
            return [], -1

        #print fmtDsp.format("DSP_NAME", "STATUS")
        cardNm = self.getCardNmFromDict(cardTp)
        dspListFull = self.r.keys(self.dspExpAllKeyFmt.format(cardTp, cardNm))
        dspList = []
        for dspFull in dspListFull:
            dspList.append(dspFull.split(":")[4])
        return dspList, 0

    def getTestList(self, cardTp="", dspNm=""):
        cardTp = cardTp.upper()
        if self.checkCardExist(cardTp) != True:
            print "_NOT_ a live card:", cardTp
            return [], -1

        dspNm = dspNm.upper()
        if self.checkDspExist(cardTp, dspNm) != True:
            print "_NOT_ a live dsp:", cardTp+":"+dspNm
            return [], -1

        testList = self.r.smembers(self.dspTestKeyFmt.format(self.getBrdName(cardTp), dspNm))
        return testList, 0

#==========================================================
# Diag host status class
class diagSts(diagEngineHost):
    def __init__(self):
        diagEngineHost.__init__(self)

    def showCard (self):
        key = "EXP:CARD*"
        fmtShowCard = "{:<15}{:<15}{}"
        fmtKeyDsp = "EXP:DSP:{}*"
        print "========================================"
        #showCardStr = fmtShowCard.format("CARD_IDX", "CARD_NAME")
        #print showCardStr
        #print "----------------------------------------"
        cards = self.r.keys(key)
        for card in cards:
            cardType = card.split(':')[2]
            cardName = card.split(':')[3]
            if cardName != 'HOST':
                cardSts = "inactive"
                keyDsp = fmtKeyDsp.format(cardType)
                dspFullList = self.r.keys(keyDsp) 
                for dspFull in dspFullList:
                    dsp = dspFull.split(":")[4]
                    testQueStsKey = self.testQueStsKeyFmt.format(cardType, dsp)
                    queSts = self.r.llen(testQueStsKey)
                    if queSts > 0:
                        cardSts = "active"

                showCardStr = fmtShowCard.format(cardType, cardName, cardSts)
                print showCardStr

        #print "========================================"
        return 0

    def showDsp (self, cardTp=""):
        cards, err = self.getCardList(cardTp)
        if err != 0:
            return

        # Display DSPs
        for card in cards:
            fmtCard = "============ {} ============"
            print fmtCard.format(card)
            fmtDsp = "{:<20}{}"
            #print fmtDsp.format("DSP_NAME", "STATUS")
            cardNm = self.getCardNmFromDict(card)
            dspListFull = self.r.keys(self.dspExpAllKeyFmt.format(card, cardNm))
            for dspFull in dspListFull:
                dsp = dspFull.split(":")[4]
                if dsp == "DIAGMGR":
                    continue
                # Get DSP status
                testQueStsKey = self.testQueStsKeyFmt.format(card, dsp)
                queSts = self.r.llen(testQueStsKey)
                if queSts <= 0:
                    sts = "inactive"
                else:
                    sts = "active"

                print fmtDsp.format(dsp, sts)
        return

    def showTest (self, cardTp="", dspNm=""):
        dspNm = dspNm.upper()
        cards, err = self.getCardList(cardTp)
        if err != 0:
            return

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTest = "{:<20}{}"
        # Display DSPs
        for card in cards:
            cardNm = self.getCardNmFromDict(card)
            print fmtCard.format(card, cardNm)
            dspList, err = self.getDspList(card)
            if err != 0:
                return
            for dsp in dspList:
                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                print fmtDsp.format(dsp)
                testList, err = self.getTestList(card, dsp)
                if err != 0:
                    continue
                # Get DSP status
                testQueStsKey = self.testQueStsKeyFmt.format(card, dsp)
                queSts = self.r.llen(testQueStsKey)

                for test in testList:
                    sts = "inactive"
                    if queSts > 0:
                        testId = self.r.lindex(testQueStsKey, -1)
                        testStr = self.testKeyFmt.format(card, dsp, testId)
                        testNm = self.r.get(testStr)
                        if test == testNm:
                            sts = "active"

                    print fmtTest.format(test, sts)
        return

    def showHist (self, cardTp="", dspNm=""):
        cardList, err = self.getCardList(cardTp)
        if err != 0:
            return -1

        fmtCard = "============ {}:{} ============"
        fmtDsp = "-------- {} --------"
        fmtTestHist = "{:<15}{:<10}{:<10}{:<10}"
        for card in cardList: 
            cardNm = self.getCardNmFromDict(card)
            print fmtCard.format(card, cardNm)
            dspList, err = self.getDspList(card)
            if err != 0:
                continue

            testHistStr = fmtTestHist.format("TEST_NAME", "PASS", "FAIL", "TIMEOUT")
            print testHistStr
            for dsp in dspList:

                # Skip DIAGMGR
                if dsp == "DIAGMGR":
                    continue
                print fmtDsp.format(dsp)
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
                    print testHistStr

    # Clean up system
    def sysClean(self):
        dshbufList = self.r.keys("dshbuf*")
        for dshbuf in dshbufList:
            self.r.delete(dshbuf)
        print "dshbuf cleared"

        queList = self.r.keys("QUEUE:")
        for que in queList:
            self.r.delete(que)
        print "que cleared"


