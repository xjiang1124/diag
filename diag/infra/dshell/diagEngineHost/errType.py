class errType:
    def __init__(self):
        self.mapV = dict()
        # INFO_GENERAL
        self.mapV["Success"] = 0
        self.mapV["Invalidparam"] = 1
        self.mapV["Fail"] = -1
        # INFO_DIAGMGR
        self.mapV["Skip"] = 100
        self.mapV["Timeout"] = 101
        self.mapV["Invalidtest"] = 102
        self.mapV["Permskip"] = 103

        self.mapN = dict()
        # INFO_GENERAL
        self.mapN[0] = "Success"
        self.mapN[1] = "Invalidparam"
        self.mapN[-1] = "Fail"
        # INFO_DIAGMGR
        self.mapN[100] = "Skip"
        self.mapN[101] = "Timeout"
        self.mapN[102] = "Invalidtest"
        self.mapN[103] = "Permskip"

    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
