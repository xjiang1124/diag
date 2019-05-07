#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Generate a KEK (key-encryption-key)")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--frk", help="Manufacturer's firmware root key", metavar="FILE.frk")
   parser.add_option("--cert", help="Developer's certificate", metavar="FILE.cert")
   parser.add_option("--output", "-o", help="basename for output files (extension .kek will be added) - mandatory", metavar="FILE")
   parser.add_option("--overwrite", help="overwrite existing files", action="store_true")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.algo:
      parser.error("missing --algo argument")
   if not options.output:
      parser.error("missing --output argument")
      
   # Read inputs
   firmware_root_key = utils.read(options.frk)
   certificate = utils.read(options.cert, utils.get_cert_size(options.algo))

   # Generate KEK
   KEK = utils.get_KEK(firmware_root_key, certificate)

   # Write outputs
   utils.write(options.output+".kek", KEK, options.overwrite)   

utils.run(main)
