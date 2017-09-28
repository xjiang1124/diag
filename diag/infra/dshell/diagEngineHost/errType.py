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
        self.mapV["INVALID_LOCK"] = 6
        # INFO_DIAGMGR
        self.mapV["DIAGMGR_SKIP"] = 100
        self.mapV["DIAGMGR_TIMEOUT"] = 101
        self.mapV["DIAGMGR_INVALID_TEST"] = 102
        self.mapV["DIAGMGR_PERM_SKIP"] = 103
        # INFO_TEMPSENSOR
        self.mapV["TEMPSENSOR_INVALID_ID"] = 200
        self.mapV["TEMPSENSOR_OVER_LIMIT"] = 201
        # INFO_I2C
        self.mapV["I2C_RD_FAIL"] = 300
        self.mapV["I2C_WR_FAIL"] = 301

        self.mapN = dict()
        # INFO_GENERAL
        self.mapN[0] = "SUCCESS"
        self.mapN[-1] = "FAIL"
        self.mapN[1] = "INVALID_PARAM"
        self.mapN[2] = "SKIP"
        self.mapN[3] = "TIMEOUT"
        self.mapN[4] = "INVALID_TEST"
        self.mapN[5] = "PERM_SKIP"
        self.mapN[6] = "INVALID_LOCK"
        # INFO_DIAGMGR
        self.mapN[100] = "DIAGMGR_SKIP"
        self.mapN[101] = "DIAGMGR_TIMEOUT"
        self.mapN[102] = "DIAGMGR_INVALID_TEST"
        self.mapN[103] = "DIAGMGR_PERM_SKIP"
        # INFO_TEMPSENSOR
        self.mapN[200] = "TEMPSENSOR_INVALID_ID"
        self.mapN[201] = "TEMPSENSOR_OVER_LIMIT"
        # INFO_I2C
        self.mapN[300] = "I2C_RD_FAIL"
        self.mapN[301] = "I2C_WR_FAIL"

    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
