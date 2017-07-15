#!/usr/bin/env python

import os
import sys
import re
import yaml
import pprint
import redis

# Interactive mode packages
from IPython import embed
from traitlets.config.loader import Config
from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.embed import InteractiveShellEmbed

#=========================================================
# Initialization
rds = redis.StrictRedis(host='localhost', port=6379, db=0)
pp = pprint.PrettyPrinter()

#=========================================================
# Output format
fmt_dsp = '{}#DSP'
fmt_dsp_info = '{}#DSP#INFO'
fmt_test = '{}#TEST#{}'
fmt_test_info = '{}#TEST#INFO#{}'
fmt_param = '{}#PARAM#{}'
fmt_param_info = '{}#PARAM#INFO#{}'

#=========================================================
# Parser card list
# Input: card name or card type
#        In case of card type, all cards for that type will
#        be returned as a list.
# Output: card list
def parser_card_list(config_dict, key):
    card_list = []
    platform_config = config_dict['PLATFORM_CONFIG']
    card_type_list = platform_config.keys()

    # input is card type
    if key in card_type_list:
        card_list = platform_config[key].split()

    # input is card name
    for card_type, cards in platform_config.items():
        c_list = cards.split()
        if key in c_list:
            card_list.append(key)

    return card_list


#=========================================================
# yaml parser
config_file = "platform_config.yaml"
with open(config_file) as stream:
    try:
        config_data = yaml.load(stream)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

card_list = parser_card_list(config_data, 'NIC')
print card_list

card_list = parser_card_list(config_data, 'NAPLES')
print card_list

dsp_file = "pmbus.yaml"
with open(dsp_file) as stream:
    try:
        dsp_dict = yaml.load(stream)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

#print fmt_dsp.format(dsp_dict['DSP']['NAME'])#

# Get all test entries
r = re.compile('TEST#.*')
test_pre_list = filter(r.match, dsp_dict['DSP'].keys()) 
test_list = []
for test_pre in test_pre_list:
    test_list.append(test_pre.split('#')[1])

for test in test_list:
    test_dict = dsp_dict['DSP']['TEST#'+test]
    # Iterate on each platform. 
    # Final output is per card_name
    pf_dict = dsp_dict['DSP']['TEST#'+test]['PLATFORM']
    for c_type in pf_dict.keys():
        if pf_dict[c_type] == None:
            continue
        # in case of 'ALL', get all cards
        if pt_dict[c_type] == 'ALL':
