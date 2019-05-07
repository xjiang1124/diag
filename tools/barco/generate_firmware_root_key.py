#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Generate a random firmware root key")
   parser.add_option("--output", "-o", help="basename for output files (extension .frk will be added) - mandatory", metavar="FILE")
   parser.add_option("--size", help="FRK size", default=16)
   parser.add_option("--overwrite", help="overwrite existing files", action="store_true")
   parser.add_option("--seed", help="generate key based on a seed")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.output:
      parser.error("missing --output argument")

   # Generate key pair
   firmware_root_key = utils.create_random_key(int(options.size), options.seed)

   # Write outputs
   utils.write(options.output+".frk", firmware_root_key, options.overwrite)   
   utils.write(options.output+".mif", firmware_root_key, options.overwrite, tohex=True)

utils.run(main)
