#! /usr/bin/python3
import argparse
import os
import pdb
import sys
import time

parser = argparse.ArgumentParser(description='Diag CI/CD Integration')
parser.add_argument('--testbed', dest='testbed_json', default=None,
                    required=True, help='Testbed JSON')
parser.add_argument('--asic', dest='asic', default=None,
                    required=True, help='ASIC for test')
parser.add_argument('--image-manifest', dest='image_manifest', default=None,
                    required=True, help='Image manifest')
parser.add_argument('--diag-images', dest='diag_images', default=None,
                    required=True, help='Diag Image Location')
parser.add_argument('--asic-images', dest='asic_images', default=None,
                    required=True, help='ASIC Image Location')
parser.add_argument('--cfg-folder', dest='cfgfolder', default=None,
                    required=True, help='Folder to generate config-yaml')
parser.add_argument('--testsuite', dest='testsuite', default=None,
                    required=True, help='Testsuite to run')
parser.add_argument('--test-type', dest='testtype', default='sanity',
                    help='Test-type: sanity, precheckin, regression')
parser.add_argument('--diag-version', dest='diag_tool_version', default='latest',
                    help='Diag tool version to use')
parser.add_argument('--asic-version', dest='asic_lib_version', default='latest',
                    help='ASIC library version to use')
parser.add_argument('--logfile', dest='logfile', default="mtb_mfg_run.log",
                    help='Log filename')


GlobalOptions = parser.parse_args()
GlobalOptions.logdir = None

