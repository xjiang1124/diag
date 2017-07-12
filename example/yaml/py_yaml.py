#!/usr/bin/env python

import os
import sys

import yaml

# Interactive mode packages
from IPython import embed
from traitlets.config.loader import Config
from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.embed import InteractiveShellEmbed

#=========================================================
# yaml parser
yaml_dict = dict()

yaml_file = "pmbus.yaml"
with open(yaml_file) as stream:
    try:
        yaml_data = yaml.load(stream)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

for dsp, dsp_items in yaml_data.items():
    for item_key, item_value in dsp_items.items():
        if item_key == 'COMMON':
            common_dict = dict()
            for common_key, common_value in item_value.items():
                if common_key == 'PARAM':
                    param_dict = dict()
                    for param_name, param_items in common_key.items():


sys.exit()
#=========================================================
# Interactive mode
class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, 'DiagSH[0] ')]
    def out_prompt_tokens(self, cli=None):
        return [(Token.Prompt, 'DiagOut[0] ')]

try:
    get_ipython
except NameError:
    banner  ='Entering Diag Shell'
    exit_msg = 'Exiting Diag Shell' 
    cfg = Config()
    prompt_config = cfg.TerminalInteractiveShell.prompts_class
    prompt_config.in_template = 'DiagSH: '
    
else:
    banner = '*** Nested interpreter ***'
    exit_msg = '*** Back in main IPython ***'

ipshell = InteractiveShellEmbed(banner1=banner, exit_msg=exit_msg)

ipshell.prompts = MyPrompt(ipshell)

ipshell()


