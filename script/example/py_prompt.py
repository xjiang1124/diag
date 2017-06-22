#!/usr/bin/env python

import os
from IPython import embed
from traitlets.config.loader import Config
from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.embed import InteractiveShellEmbed

var1 = 1086
var2 = "interactive"

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


