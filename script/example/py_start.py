#!/usr/bin/env python

from IPython.terminal.prompts import Prompts, Token
import os
from IPython import embed

class MyPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, 'DiagSH[0] ')]
    def out_prompt_tokens(self, cli=None):
        return [(Token.OutPrompt, 'DiagOut ')]

print "Hello"

var1 = 1086
var2 = "interactive"

ip = get_ipython()
ip.prompts = MyPrompt(ip)

def func_hello (who):
    print 'Hello', who

