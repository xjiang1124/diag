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
        "ARGUMENT_SPEC"              : "--mode",
        "DEFAULT"                    : "hod",
        "P47930-001"                 : "nod_525",
        "0X322FX06"                  : "nod_550",
        "0X322FA00"                  : "nod_550",
        # "68-0015-02"                : "nod_550",
        # "68-0015-03"                : "hod_1100",
    },
    "DDR_BIST"         : {
        ##### For DDR_BIST test, we call asic run_l1.sh, so the args here are actually for the script run_l1.sh
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        "IS_SUITE_COMMON_ARGS_APPLY" : True, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : True,
        "ARGUMENT_SPEC"              : "--sn         --slot          --int_lpbk          --vmarg         --offload       --esec_en       --simplify          -hc         -ddr",
        "DEFAULT"                    : "XYZ          N/A             0                   normal          1               0               0                   1           1",
        "68-0015"                    : "N/A          N/A             -                   N/A             -               0               -                   N/A         0",
        "P47930-001"                 : "N/A          N/A             -                   normal          N/A             0               N/A                 1           1",
        "0X322FX06"                  : "N/A          N/A             -                   normal          N/A             1               N/A                 0           1",
        "0X322FA00"                  : "N/A          N/A             0                   normal          1               1               N/A                 0           1",
        "68-0029"                    : "N/A          N/A             -                   normal          -               -               -                   0           1",
    },
    "SNAKE_ELBA"       : {
        ##### SNAKE_ELBA Test call nic_test.py script, so args here are actually for nic_test.py, example nic_test.py -snake -slot_list='6,8' -wtime=600 -vmarg normal -snake_num=4 -dura=3 -mode=hod
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option 
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        "IS_SUITE_COMMON_ARGS_APPLY" : True, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : True,
        "ARGUMENT_SPEC"              : "--slot_list     -wtime              -vmarg         -snake_num        -dura         -int_lpbk",
        "DEFAULT"                    : "N/A             600                 normal         4                 3             -",           
        "68-0015"                    : "N/A             N/A                 N/A            N/A               N/A           N/A",
        "P47930-001"                 : "N/A             300                 N/A            6                 120           N/A",
        "0X322FX06"                  : "N/A             300                 N/A            6                 120           N/A",
        "0X322FA00"                  : "N/A             300                 N/A            6                 120           N/A",
        "68-0029"                    : "N/A             600                 N/A            4                 3             +",
    },
}