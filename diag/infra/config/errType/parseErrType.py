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
input_path = './'
output_path = './OUTPUT/'

# Delete all files under OUTPUT/
del_all_files(output_path)

#=========================================================
# yaml parser
errfile = input_path+"errType.yaml"
with open(errfile) as stream:
    try:
        #config_dict = yaml.load(stream)
        errDict = ordered_load(stream, yaml.SafeLoader)
    except yaml.YAMLError as exc:
        print exc
        sys.exit()

create_folder(output_path)

# golang output
goHeader = """package errType

const(
"""
goEnding = ")"
errFmt = "    {:<20} = {}\n"
infoFmt = "    // {}\n"

infoFilter = "INFO"

goOutputFile = output_path+'errType.go'
f = open(goOutputFile, 'w')
f.write(goHeader)
for err, value in errDict.items():
    if err.find("INFO") >= 0:
        errInfo = infoFmt.format(err)
        f.write(errInfo)
    else:
        # Check comment part
        errStr = errFmt.format(err.title(), value)
        f.write(errStr)

f.write(goEnding)
f.close()

# Python output
pyHeader = """class errType:
    def __init__(self):
        self.mapV = dict()
"""

pyFunc = """\n    def toName(self, value):
        return self.mapN[value]

    def toValue(self, name):
        return self.mapV[name]
"""

pyMid = "\n        self.mapN = dict()\n"
pyMapVFmt = "        self.mapV[\"{}\"] = {}\n"
pyMapNFmt = "        self.mapN[{}] = \"{}\"\n"
pyInfoFmt = "        # {}\n"

infoFilter = "INFO"

pyOutputFile = output_path+'errType.py'
f = open(pyOutputFile, 'w')
f.write(pyHeader)
for err, value in errDict.items():
    if err.find("INFO") >= 0:
        pyErrInfo = pyInfoFmt.format(err, value)
        f.write(pyErrInfo)
    else:
        # Check comment part
        pyMapVStr = pyMapVFmt.format(err.title(), value)
        f.write(pyMapVStr)

f.write(pyMid)
for err, value in errDict.items():
    if err.find("INFO") >= 0:
        pyErrInfo = pyInfoFmt.format(err, value)
        f.write(pyErrInfo)
    else:
        # Check comment part
        pyMapNStr = pyMapNFmt.format(value, err.title())
        f.write(pyMapNStr)

f.write(pyFunc)
f.close()

