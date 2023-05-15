from libdefs import Factory

GLB_CFG_MFG_TEST_MODE = False
SKIP_EMMC_PSLC_CHECK = True
ALLOW_TEST_FROM_TERMSERVER = True #False
ENABLE_CONSOLE_SANITY_CHECK = True

Factory_network_config = {
    Factory.P1: {
        "Networks": [u"192.168.8.0/22"],
        "Flexflow": "10.192.39.48"
    },
    Factory.LAB: {
        "Networks": [u"10.9.0.0/16"],
        "Flexflow": ""
    }
}

