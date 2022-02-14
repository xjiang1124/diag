#! /usr/bin/python3
import argparse
import os
import pdb
import sys
import time

parser = argparse.ArgumentParser(description='Diag CI/CD Integration')
parser.add_argument('--testbed', dest='testbed_json', default=None,
                    help='Testbed JSON', required=True)
parser.add_argument('--asic', dest='asic', default=None,
                    help='ASIC for test', required=True)
parser.add_argument('--version', dest='version', default="latest",
                    help='Diag Sw Version')
parser.add_argument('--logfile', dest='logfile', default="mtb_mfg_run.log",
                    help='Log filename')
parser.add_argument('--logdir', dest='logdir', default=None,
                    help='Log filename')
parser.add_argument('--tmp-folder', dest='tmp_folder', default='/tmp', 
                    help='Temp folder for download assets')
parser.add_argument('--cfg-folder', dest='cfgfolder', default='/tmp',
                    help='Temp folder for download assets')


GlobalOptions = parser.parse_args()

