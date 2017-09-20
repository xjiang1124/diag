class errType:
    def __init__(self):
        self.mapV = dict()
        # INFO_GENERAL
        self.mapV["SUCCESS"] = 0
        self.mapV["FAIL"] = -1
        self.mapV["INVALID_PARAM"] = 1
        self.mapV["SKIP"] = 2
        self.mapV["TIMEOUT"] = 3
        self.mapV["INVALID_TEST"] = 4
        self.mapV["PERM_SKIP"] = 5
        # INFO_DIAGMGR
        self.mapV["DIAGMGR_SKIP"] = 100
        self.mapV["DIAGMGR_TIMEOUT"] = 101
        self.mapV["DIAGMGR_INVALID_TEST"] = 102
        self.mapV["DIAGMGR_PERM_SKIP"] = 103

        self.mapN = dict()
        # INFO_GENERAL
        self.mapN[0] = "SUCCESS"
        self.mapN[-1] = "FAIL"
        self.mapN[1] = "INVALID_PARAM"
        self.mapN[2] = "SKIP"
        self.mapN[3] = "TIMEOUT"
        self.mapN[4] = "INVALID_TEST"
        self.mapN[5] = "PERM_SKIP"
        # INFO_DIAGMGR
        self.mapN[100] = "DIAGMGR_SKIP"
        self.mapN[101] = "DIAGMGR_TIMEOUT"
        self.mapN[102] = "DIAGMGR_INVALID_TEST"
        self.mapN[103] = "DIAGMGR_PERM_SKIP"

    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
