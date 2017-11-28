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
        self.mapV["UNSUPPORTED_CARD"] = 7
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
        # INFO_SMB
        self.mapV["SMB_OPEN_FAIL"] = 400
        self.mapV["SMB_CLOSE_FAIL"] = 401
        self.mapV["SMB_READ_FAIL"] = 402
        self.mapV["SMB_WRITE_FAIL"] = 403
        self.mapV["SMB_INF_BUSY"] = 404
        self.mapV["SMB_INF_INVALID"] = 405

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
        self.mapN[7] = "UNSUPPORTED_CARD"
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
        # INFO_SMB
        self.mapN[400] = "SMB_OPEN_FAIL"
        self.mapN[401] = "SMB_CLOSE_FAIL"
        self.mapN[402] = "SMB_READ_FAIL"
        self.mapN[403] = "SMB_WRITE_FAIL"
        self.mapN[404] = "SMB_INF_BUSY"
        self.mapN[405] = "SMB_INF_INVALID"

    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
