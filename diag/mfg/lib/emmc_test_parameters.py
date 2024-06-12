# python dict for test to it's arguments mapping table

test2args = {
    # Test suit level common arguments, if specified, it will apply to all the test commands according to test case setting
    "TEST_SUITE_COMMON"              : {
        # "ARGUMENT_SPEC"             : "--somearg",
        # "DEFAULT"                   : "hod",
        # "68-0015"                   : "nod_550",
        # "68-0015-02"                : "hod_1100",
    },
    # Test case level common arguments, if specified, it will apply to all test commands according to test case setting
    "TEST_CASE_COMMON"               : {
        # "ARGUMENT_SPEC"             : "--mode",
        # "DEFAULT"                   : "hod",
        # "P47930-001"                : "nod_525",
        # "0X322FX06"                 : "nod_550",
        # "0X322FA00"                 : "nod_550",
        # "68-0015-02"                : "nod_550",
        # "68-0015-03"                : "hod_1100",
    },
    "FIO_RANDOM-WRITE-BS4K-1G"       : {
        ##### For FIO test, we call the binary tool fio, so the args here are actually for the fio
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        "IS_SUITE_COMMON_ARGS_APPLY" : False, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Write-BS4K-1G   --ioengine=posixaio --rw=randwrite --bs=4k --numjobs=1 --size=1g   --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-WRITE-BS4K-1G         posixaio            randwrite       4k              1               1g           1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-WRITE-BS4K-1G         posixaio            randwrite       4k              1               1g           1              20                +                 1",
    },
    "FIO_RANDOM-WRITE-BS4K-512M"     : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Write-BS4K-512M --ioengine=posixaio --rw=randwrite --bs=4k --numjobs=1 --size=512m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-WRITE-BS4K-512M       posixaio            randwrite       4k              1               512m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-WRITE-BS4K-512M       posixaio            randwrite       4k              1               512m         1              20                +                 1",
    },
    "FIO_RANDOM-WRITE-BS4K-256M"     : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Write-BS4K-256M --ioengine=posixaio --rw=randwrite --bs=4k --numjobs=1 --size=256m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-WRITE-BS4K-256M       posixaio            randwrite       4k              1               256m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-WRITE-BS4K-256M       posixaio            randwrite       4k              1               256m         1              20                +                 1",
    },
    "FIO_RANDOM-WRITE-BS4K-128M"     : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Write-BS4K-128M --ioengine=posixaio --rw=randwrite --bs=4k --numjobs=1 --size=128m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-WRITE-BS4K-128M       posixaio            randwrite       4k              1               128m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-WRITE-BS4K-128M       posixaio            randwrite       4k              1               128m         1              20                +                 1",
    },
    "FIO_RANDOM-READ-BS4K-1G"        : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Read-BS4K-1G    --ioengine=posixaio --rw=randread  --bs=4k --numjobs=1 --size=1g   --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-READ-BS4K-1G          posixaio            randread        4k              1               1g           1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-READ-BS4K-1G          posixaio            randread        4k              1               1g           1              20                +                 1",
    },
    "FIO_RANDOM-READ-BS4K-512M"      : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Read-BS4K-512M  --ioengine=posixaio --rw=randread  --bs=4k --numjobs=1 --size=512m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-READ-BS4K-512M        posixaio            randread        4k              1               512m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-READ-BS4K-512M        posixaio            randread        4k              1               512m         1              20                +                 1",
    },
    "FIO_RANDOM-READ-BS4K-256M"      : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Read-BS4K-256M  --ioengine=posixaio --rw=randread  --bs=4k --numjobs=1 --size=256m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-READ-BS4K-256M        posixaio            randread        4k              1               256m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-READ-BS4K-256M        posixaio            randread        4k              1               256m         1              20                +                 1",
    },
    "FIO_RANDOM-READ-BS4K-128M"      : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Random-Read-BS4K-128M  --ioengine=posixaio --rw=randread  --bs=4k --numjobs=1 --size=128m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "RANDOM-READ-BS4K-128M        posixaio            randread        4k              1               128m         1              60                +                 1",
        "MATERA_PN_NVME"             : "RANDOM-READ-BS4K-128M        posixaio            randread        4k              1               128m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-WRITE-BS4K-1G"   : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Write-BS4K-1G   --ioengine=posixaio --rw=write     --bs=4k --numjobs=1 --size=1g   --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                       --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-WRITE-BS4K-1G     posixaio            write           4k              1               1g           1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-WRITE-BS4K-1G     posixaio            write           4k              1               1g           1              20                +                 1",
    },
    "FIO_SEQUENTIAL-WRITE-BS4K-512M" : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Write-BS4K-512M --ioengine=posixaio --rw=write     --bs=4k --numjobs=1 --size=512m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-WRITE-BS4K-512M     posixaio            write           4k              1               512m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-WRITE-BS4K-512M     posixaio            write           4k              1               512m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-WRITE-BS4K-256M" : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Write-BS4K-256M --ioengine=posixaio --rw=write     --bs=4k --numjobs=1 --size=256m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-WRITE-BS4K-256M     posixaio            write           4k              1               256m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-WRITE-BS4K-256M     posixaio            write           4k              1               256m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-WRITE-BS4K-128M" : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Write-BS4K-128M --ioengine=posixaio --rw=write     --bs=4k --numjobs=1 --size=128m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-WRITE-BS4K-128M     posixaio            write           4k              1               128m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-WRITE-BS4K-128M     posixaio            write           4k              1               128m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-READ-BS4K-1G"    : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Read-BS4K-1G    --ioengine=posixaio --rw=read      --bs=4k --numjobs=1 --size=1g   --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-READ-BS4K-1G        posixaio            read            4k              1               1g           1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-READ-BS4K-1G        posixaio            read            4k              1               1g           1              20                +                 1",
    },
    "FIO_SEQUENTIAL-READ-BS4K-512M"  : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Read-BS4K-512M  --ioengine=posixaio --rw=read      --bs=4k --numjobs=1 --size=512m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-READ-BS4K-512M      posixaio            read            4k              1               512m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-READ-BS4K-512M      posixaio            read            4k              1               512m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-READ-BS4K-256M"  : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Read-BS4K-256M  --ioengine=posixaio --rw=read      --bs=4k --numjobs=1 --size=256m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-READ-BS4K-256M      posixaio            read            4k              1               256m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-READ-BS4K-256M      posixaio            read            4k              1               256m         1              20                +                 1",
    },
    "FIO_SEQUENTIAL-READ-BS4K-128M"  : {
        "IS_SUITE_COMMON_ARGS_APPLY" : False,
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        #./fio --name=Sequen-Read-BS4K-128M  --ioengine=posixaio --rw=read      --bs=4k --numjobs=1 --size=128m --iodepth=1 --runtime=60 --time_based --end_fsync=1
        "ARGUMENT_SPEC"              : "--name                         --ioengine          --rw            --bs            --numjobs       --size       --iodepth      --runtime         --time_based      --end_fsync",
        "DEFAULT"                    : "SEQUENTIAL-READ-BS4K-128M      posixaio            read            4k              1               128m         1              60                +                 1",
        "MATERA_PN_NVME"             : "SEQUENTIAL-READ-BS4K-128M      posixaio            read            4k              1               128m         1              20                +                 1",
    },
    "STRESSAPPTEST"                  : {
        ##### STRESSAPPTEST Test call /data/nic_util/stressapptest_arm, /data/nic_util/stressapptest_arm  -M 400  -f file.1 -f file.2 -s <test_time_in_sec>
        # Part Number                : Command Arguments List in white space seperated String, put N/A if you want to use default value; For flag only options, + means inclue this option, - means exclude this option 
        # 68-0015 or 68-0015-02      : We can specify part number with two this two format, if both appear in the dict, the one with revision(68-0015-02) take priority
        "IS_SUITE_COMMON_ARGS_APPLY" : False, # Flag to indicate if using the comman test suite and test case arguments, if this key is not show up in this dict, means default to True
        "IS_CASE_COMMON_ARGS_APPLY"  : False,
        "ARGUMENT_SPEC"              : "-M              -f              -f         -s",
        "DEFAULT"                    : "400             file.1          file.2     1800",
        "MATERA_PN_NVME"             : "400             file.1          file.2     180",
    },
}