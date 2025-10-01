# python dict for test to it's arguments mapping table

test2args = {
    # Test suit level common arguments, if specified, it will apply to all the test commands according to test case setting
    "TEST_SUITE_COMMON" : {
        # "ARGUMENT_SPEC"              : "--somearg",
        # "DEFAULT"                    : "hod",
        # "68-0015"                    : "nod_550",
        # "68-0015-02"                 : "hod_1100",
    },
    # Test case level common arguments, if specified, it will apply to all test commands according to test case setting
    "TEST_CASE_COMMON"  : {
        "ARGUMENT_SPEC"              : "-mode",
        "DEFAULT"                    : "hod",
        # Ortano section
        "68-0021"                    : "hod_1100",              #68-0021-02 XX    ORTANO2 MICROSOFT
        "68-0034"                    : "hod_1100",              #68-0034-01 XX    ORTANO2ADI MICROSOFT
        "68-0015"                    : "hod",                   #68-0015-02 XX    ORTANO2 ORACLE
        "68-0026"                    : "hod",                   #68-0026-01 XX    ORTANO2ADI ORACLE
        "68-0028"                    : "hod",                   #68-0028-01 XX    ORTANO2ADI IBM
        "68-0029"                    : "hod",                   #68-0029-01 XX    ORTANO2 Interposer
        "68-0077"                    : "hod",                   #68-0077-01 XX    ORTANO2 SOLO
        "68-0095"                    : "hod",                   #68-0095-01 XX    ORTANO2 SOLO-L
        "68-0090"                    : "hod_1100",              #68-0090-01 XX    ORTANO2 SOLO MICROSOFT
        "68-0091"                    : "hod_1100",              #68-0091-01 XX    ORTANO2ADI CR MICROSOFT
        "68-0049"                    : "hod",                   #68-0049-03 XX    ORTANO2ADI CR
        # Pomonte section
        "0PCFPC"                     : "nod",                   #0PCFPC X/A       POMONTE DELL
        # Lacona section
        "P47930"                     : "nod_525",               #P47930-001       LACONA32 HPE
        "0X322F"                     : "nod_525",               #0X322F X/A       LACONA32 DELL
        "0W5WGK"                     : "nod_525",               #0X322F X/A       LACONA32 DELL
        # Ginestra section
        "68-0074"                    : "hod_1100",              #68-0074          Ginextra_D4
        "68-0075"                    : "hod_1100",              #68-0075          Ginextra_D5
    },
    "DDR_BIST"         : {
        ##### For DDR_BIST test, we call 'tclsh ddr_bist.tcl', so the args here are actually for the script ddr_bist.tcl
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        # tips for ginestra,    -vdd_margin_pct -arm_margin_pct -margin_pct (no matter vmagin high or low, both are 3 3 3 now); for ddr_freq D4 3200; D5 4800 and 5600
        "IS_SUITE_COMMON_ARGS_APPLY" : True, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : True,
        "ARGUMENT_SPEC"              : "-sn          -slot           -hc                 -ctrl_pi        -addr_space     -dual_rank      -ddr_freq           -ddr5       -vmarg         -pc         -vdd_margin_pct         -arm_margin_pct         -margin_pct",
        "DEFAULT"                    : "XYZ          N/A             -                   -               -               -               -                   -           normal         0           -                       -                       -",
        "P47930"                     : "N/A          N/A             N/A                 N/A             N/A             1               2400                N/A         N/A            N/A         -                       -                       -",
        "0X322F"                     : "N/A          N/A             N/A                 N/A             N/A             1               2400                N/A         N/A            N/A         -                       -                       -",
        "0W5WGK"                     : "N/A          N/A             N/A                 N/A             N/A             1               2400                N/A         N/A            N/A         -                       -                       -",
        "68-0074"                    : "N/A          N/A             N/A                 N/A             N/A             N/A             3200                N/A         N/A            0           -                       -                       -",
        "68-0075"                    : "N/A          N/A             N/A                 N/A             N/A             N/A             5600                N/A         N/A            0           3                       3                       3",
    },
    "SNAKE_ELBA"       : {
        ##### SNAKE_ELBA Test call nic_test.py script, so args here are actually for nic_test.py, example nic_test.py -snake -slot_list='6,8' -wtime=600 -vmarg normal -snake_num=4 -dura=3 -mode=hod
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option 
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        "IS_SUITE_COMMON_ARGS_APPLY" : True, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : True,
        "ARGUMENT_SPEC"              : "--slot_list     -wtime              -vmarg         -snake_num        -dura         -int_lpbk        -num_retry",
        "DEFAULT"                    : "N/A             600                 normal         4                 3             +                5",
        "68-0015"                    : "N/A             N/A                 N/A            N/A               N/A           N/A              N/A",
        "P47930"                     : "N/A             300                 N/A            6                 120           N/A              N/A",
        "0X322F"                     : "N/A             300                 N/A            6                 120           N/A              N/A",
        "0W5WGK"                     : "N/A             300                 N/A            6                 120           N/A              N/A",
        "68-0029"                    : "N/A             600                 N/A            4                 3             +                N/A",
        "68-0074"                    : "N/A             600                 N/A            6                 120           +                N/A",
        "68-0075"                    : "N/A             600                 N/A            6                 120           +                N/A",
    },
}