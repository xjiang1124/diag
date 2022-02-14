#!/usr/bin/python3

import os
import logging

from glopts import GlobalOptions

if GlobalOptions.logdir == None:
    folder = os.path.join(GlobalOptions.topdir, 'log')
    GlobalOptions.logdir = folder

try:
    os.makedirs(GlobalOptions.logdir, exist_ok = True)
except Exception as e:
    pass

def InitLogger():
    logger = logging.getLogger('MfgSanity')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if GlobalOptions.logdir and GlobalOptions.logfile:
        log_file = os.path.join(GlobalOptions.logdir, GlobalOptions.logfile)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
