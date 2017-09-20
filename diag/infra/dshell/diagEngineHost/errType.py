class errType:
    def __init__(self):
        self.mapV = dict()
        # INFO_GENERAL
        self.mapV["DIAGMGR_SUCCESS"] = 0
        self.mapV["DIAGMGR_INVALID_PARAM"] = 1
        self.mapV["DIAGMGR_FAIL"] = -1
        # INFO_DIAGMGR
        self.mapV["DIAGMGR_SKIP"] = 100
        self.mapV["DIAGMGR_TIMEOUT"] = 101
        self.mapV["DIAGMGR_INVALID_TEST"] = 102
        self.mapV["DIAGMGR_PERM_SKIP"] = 103

        self.mapN = dict()
        # INFO_GENERAL
        self.mapN[0] = "DIAGMGR_SUCCESS"
        self.mapN[1] = "DIAGMGR_INVALID_PARAM"
        self.mapN[-1] = "DIAGMGR_FAIL"
        # INFO_DIAGMGR
        self.mapN[100] = "DIAGMGR_SKIP"
        self.mapN[101] = "DIAGMGR_TIMEOUT"
        self.mapN[102] = "DIAGMGR_INVALID_TEST"
        self.mapN[103] = "DIAGMGR_PERM_SKIP"

    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
