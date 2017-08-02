#!/usr/bin/env python

import os
from os import walk
import errno
import sys
import re
import yaml
import pprint
import redis
from collections import OrderedDict

# Interactive mode packages
from IPython import embed
from traitlets.config.loader import Config
from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.embed import InteractiveShellEmbed

#=========================================================
# To load yaml file in order
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


#=========================================================
# create output folder
def create_folder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

#=========================================================
# Parser card list
# Input: card name or card type
#        In case of card type, all cards for that type will
#        be returned as a list.
#        If 'ALL' is specified, all cards will be returned as a list
# Output: card list
def parse_card_list(config_dict, key):
    card_list = []
    platform_config = config_dict['PLATFORM_CONFIG']
    card_type_list = platform_config.keys()

    if key == None or key == '':
        return None
    if key == 'ALL':
        # return all bard
        for _, cards in platform_config.items():
            c_list = cards.split()
            for c in c_list:
                card_list.append(c)
    elif key in card_type_list:
        # input is card type
        card_list = platform_config[key].split()
    else:
        # input is card name
        for card_type, cards in platform_config.items():
            c_list = cards.split()
            keys = key.split()
            for k in keys:
                if key in c_list:
                    card_list.append(key)

    return card_list


#=========================================================
# Delete all files in the given directory
# Input: target folder
def del_all_files(path):
    print 'Removing all files in', path, '...'
    for (dirpath, dirnames, filenames) in walk(path):
        for fn in filenames:
            os.remove(path+'/'+fn)
    print 'All files removed'

#=========================================================
# Initialization
pp = pprint.PrettyPrinter()
input_path = './dspYaml/'
output_path = './OUTPUT/'

# Delete all files under OUTPUT/
del_all_files(output_path)

#=========================================================
# Output format
# CARD_NAME#DSP
fmt_dsp = '{}#DSP'
# CARD_NAME#DSP#INFO
fmt_dsp_info = '{}#DSP#INFO'

# CARD_NAME#TEST#TEST_NAME
fmt_test = '{}#TEST#{}'
# CARD_NAME#TEST#INFO#TEST_NAME
fmt_test_info = '{}#TEST#INFO#{}'

# CARD_NAME#PARAM#DSP_NAME#TEST_NAME#PARAM_NAME
fmt_param = '{}#PARAM#{}#{}#{}'
# CARD_NAME#PARAM#INFO#DSP_NAME#TEST_NAME#PARAM_NAME
fmt_param_info = '{}#PARAM#INFO#{}#{}#{}'

#=========================================================
# yaml parser
config_file = input_path+"platform_config.yaml"
with open(config_file) as stream:
    try:
        #config_dict = yaml.load(stream)
        config_dict = ordered_load(stream, yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

for (dirpath, dirnames, filenames) in walk(input_path):
    print filenames

# Exclude unnecessory file like .swp
r = re.compile('.*yaml$')
filenames_true = filter(r.match, filenames)
for filename in filenames_true:

    # bypass config.yaml since it is already loaded
    if filename == "platform_config.yaml": 
        continue

    #=========================================================
    dsp_file = input_path+filename
    with open(dsp_file) as stream:
        try:
            #dsp_dict = yaml.load(stream)
            dsp_dict = ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print exc
            sys.exit()
    
    #print fmt_dsp.format(dsp_dict['DSP']['NAME'])#
    
    r_dsp_dict = OrderedDict()
    r_dsp_info_dict = OrderedDict()
    r_test_dict = OrderedDict()
    r_test_info_dict = OrderedDict()
    r_param_dict = OrderedDict()
    r_param_info_dict = OrderedDict()
    
    # Get all test entries
    r = re.compile('TEST#.*')
    test_pre_list = filter(r.match, dsp_dict['DSP'].keys()) 
    test_list = []
    for test_pre in test_pre_list:
        test_list.append(test_pre.split('#')[1])
    
    # Get all card entries of this dsp
    all_card_list = parse_card_list(config_dict, 'ALL')
    
    # Get parameter from common section
    param_common_dict = dsp_dict['DSP']['COMMON']['PARAM']
    
    for test in test_list:
        #print test
        test_dict = dsp_dict['DSP']['TEST#'+test]
        # Iterate on each platform. 
        # Final output is per card_name
        pf_dict = dsp_dict['DSP']['TEST#'+test]['PLATFORM']
        for c_type in pf_dict.keys():
            if pf_dict[c_type] == None:
                continue
            # in case of 'ALL', get all cards
            if pf_dict[c_type] == 'ALL':
                card_list = parse_card_list(config_dict, c_type)
            else:
                card_list = pf_dict[c_type].split()
    
            # Forming data sturcture
            for card in card_list:
                #print card
                # DSP name
                dsp_key = fmt_dsp.format(card)
                dsp_value = dsp_dict['DSP']['NAME']
                r_dsp_dict[dsp_key] = dsp_value
    
                # DSP info
                dsp_info_key = fmt_dsp_info.format(card)
                dsp_info_value = dsp_dict['DSP']['INFO']
                r_dsp_info_dict[dsp_info_key] = dsp_info_value
    
                # Test
                test_key = fmt_test.format(card, test)
                test_value = test
                r_test_dict[test_key] = test_value
    
                # Test info
                test_key_info = fmt_test_info.format(card, test)
                test_info_value = dsp_dict['DSP']['TEST#'+test]['INFO']
                r_test_info_dict[test_key] = test_info_value
    
                # Apply parameter setting from COMMON section
                # common parameter applies to all test/cmd
                # Can be over written by definitions in TEST section
                for param, param_v in param_common_dict.items():
                    param_key = fmt_param.format(card, dsp_value, test, param)
                    param_value = param_v['VALUE']
                    r_param_dict[param_key] = param_value
                    #print card, test, param_key, param_value
    
                    param_value = param_v['INFO']
                    r_param_info_dict[param_key] = param_value
    
                # Test parameter
                param_dict = test_dict['PARAM']
                for param, all_value in param_dict.items():
                    #print card, test, param
                    param_key = fmt_param.format(card, dsp_value, test, param)
                    if all_value['INFO'] != None:
                        param_info = all_value['INFO']
                        r_param_info_dict[param_key] = param_info
                        #print param_info
    
                    for value_card, value_value in all_value['VALUE'].items():
                        param_value = value_value
                        # adopt setting in case of 'ALL'
                        if value_card == 'ALL': 
                            r_param_dict[param_key] = param_value
                        else:
                            # to support mutiple card with '#'
                            p_cards = value_card.split('#')
                            for p_card in p_cards:
                                p_card_list = parse_card_list(config_dict, p_card)
                                if card in p_card_list:
                                    r_param_dict[param_key] = param_value
    
    #=========================================================
    # Define redis command format
    #fmt_sep = '\n#=========================================================\n'
    #fmt_sep_1 = '#----------------------------------\n'
    fmt_sep = '\n'
    fmt_sep_1 = ''
    
    # DSP: SADD CARD_NAME:DSP DSP_NAME
    fmt_redis_dsp = 'SADD DSP:{} {}\n'
    
    # DSP INFO: SADD CARD_NAME:DSP:INFO DSP_INFO
    fmt_redis_dsp_info = 'SADD DSP:INFO:{} {} \"{}\"\n'
    
    # TEST: SADD CARD_NAME:DSP_NAME:TEST TEST_NAME
    fmt_redis_test = 'SADD TEST:{}:{} {}\n'
    
    # TEST INFO: HSET CARD_NAME:DSP_NAME:TEST:INFO TEST_NAME TEST_INFO
    fmt_redis_test_info = 'HSET TEST:INFO:{}:{} {} \"{}\"\n'
    
    # PARAM: HSET CARD_NAME:DSP_NAME:TEST_NAME:PARAM PARAM_NAME PARAM_VALUE
    fmt_redis_param = 'HSET PARAM:{}:{}:{} {} {}\n'
    
    # PARAM INFO: HSET CARD_NAME:DSP_NAME:TEST_NAME:PARAM PARAM_NAME PARAM_VALUE
    fmt_redis_param_info = 'HSET PARAM:INFO:{}:{}:{} {} \"{}\"\n'
    
    #=========================================================
    # Output to file
    # file naming convention
    # cardName_dspName.redis
    fmt_output_file = '{}_{}.redis'
    create_folder(output_path)
    for dsp_card, dsp in r_dsp_dict.items():
        card = dsp_card.split('#')[0]
        output_file = output_path + fmt_output_file.format(card, dsp)
        f = open(output_file, 'w')
    
        # DSP
        output_str = fmt_redis_dsp.format(card, dsp)
        f.write(output_str)
    
        # DSP INFO
        dsp_info = r_dsp_info_dict[dsp_card+'#INFO']
        output_str = fmt_redis_dsp_info.format(card, dsp, dsp_info)
        f.write(output_str)
    
        # TEST
        # loop through test_dict and find tests under the card
        for test_card, test in r_test_dict.items():
            card_t = test_card.split('#')[0]
            if card == card_t:
                #print test, card
                f.write(fmt_sep)
                output_str = fmt_redis_test.format(card, dsp, test)
                f.write(output_str)
    
                # TEST INFO
                test_info = r_test_info_dict[card+'#TEST#'+test]
                output_str = fmt_redis_test_info.format(card, dsp, test, test_info)
                f.write(output_str)
    
                # PARAM
                for param_card, param_v in r_param_dict.items():
                    card_p = param_card.split('#')[0]
                    test_p = param_card.split('#')[3]
                    param_n = param_card.split('#')[4]
                    if card == card_p and test == test_p:
                        #print param_card, param_v, card, test
                        f.write(fmt_sep_1)
                        output_str = fmt_redis_param.format(card, dsp, test, param_n, param_v)
                        f.write(output_str)
    
                        param_i = r_param_info_dict[card+'#PARAM#'+dsp+'#'+test+'#'+param_n]
                        output_str = fmt_redis_param_info.format(card, dsp, test, param_n, param_i)
                        f.write(output_str)
    
    
    
        f.close()
        
    
    #=========================================================
    # Generate dsp main.go
    print "Starting parsing dsp main package"
 
    fmt_header = """package main

import (
    \"flag\"
    \"common/diagEngine\"
    \"common/dcli\"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = \"{}\"
)
"""
    
    fmt_fileName = "dsp{}.go"
    fmt_testHdl = """
func {}{}Hdl(argList []string) int {{
    fs := flag.NewFlagSet(\"FlagSet\", flag.ContinueOnError)
"""
    
    fmt_testParam = "    {}Ptr := fs.Int(\"{}\", {}, \"Devices bit mask\")\n"
    
    fmt_testParamPrnt = "\"{}\", *{}Ptr"
    
    fmt_testEnding = """
    err := fs.Parse(argList)
    if err != nil {{
        dcli.Println("f", "Parse failed", err)
    }}

    // To avoid compile error: variable not used
    // Need to remove after implementing DSP handler
    dcli.Println("t", {})

    // Inform diag engine that test handler is done
    // Use chan to return error code
    diagEngine.FuncMsgChan <- 0
    return 0
}}
"""
    
    main_1 = """func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
"""
    
    fmt_main_testHdl = "    diagEngine.FuncMap[\"{}\"] = {}{}Hdl\n"
    
    main_3 = """
    dcli.Init("log_"+dspName+".txt")
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
"""
    
    diagEngineParam = ['timeout', 'ite', 'dshid']
    header = fmt_header.format(dsp)
    fileName = fmt_fileName.format(dsp.lower().title())
    f = open(output_path+fileName, 'w')
    
    f.write(header)
    
    # Parse test handler
    # Since there may be different parameter values for one particular parameter, only pick one
    testHdl_dict = OrderedDict()
    testHdl_param_dict = OrderedDict()
    for test in test_list:
        testHdl = fmt_testHdl.format(dsp.lower().title(), test.lower().title())
        f.write(testHdl)
    
        # save test hanlder for test handler mappinbg in main
        main_testHdl = fmt_main_testHdl.format(test, dsp.lower().title(), test.lower().title())
        testHdl_dict[test] = fmt_main_testHdl.format(test, dsp.lower().title(), test.lower().title())
    
        # Parameter
        testHdl_param = []
        param_dict = OrderedDict()
        testParamPrnt = ""
        for param_n, value in r_param_dict.items():
            param_n_l = param_n.split('#')
            param = param_n_l[4]
            param_t = param_n_l[3]
            # Skip parameters timeout and ite since they are processed in diagEngine
            #if param == 'timeout' or param == 'ite':
            if param in diagEngineParam:
                continue
            if param_t == test:
                testParam = fmt_testParam.format(param, param, value)
                param_dict[param] = testParam
    
        paramCount = 0
        # Get parameter string
        for param_p, param_s in param_dict.items():
            f.write(param_s)
    
            # Make a print of parameter list
            ParamPrnt = fmt_testParamPrnt.format(param_p, param_p)
            if paramCount > 0:
                testParamPrnt = testParamPrnt + ', '
            testParamPrnt = testParamPrnt + ParamPrnt
            paramCount = paramCount + 1
    
        testEnding = fmt_testEnding.format(testParamPrnt)
        #testEnding = fmt_testEnding.format("mask")
        f.write(testEnding)
    
        #testHdl_param_dict[test] = param_dict
    
    f.write(main_1)
    for _, m_testHdl in testHdl_dict.items(): 
        f.write(m_testHdl)
    
    f.write(main_3)
    f.close()
    print "Done parsing dsp main package"
