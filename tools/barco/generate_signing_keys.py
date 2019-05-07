#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Generate a random key pair")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--output", "-o", help="basename for output files (extension .sk and .pk will be added) - mandatory", metavar="FILE")
   parser.add_option("--overwrite", help="overwrite existing files", action="store_true")
   parser.add_option("--seed", help="generate key based on a seed")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.algo:
      parser.error("missing --algo argument")
   if not options.output:
      parser.error("missing --output argument")

   # Generate key pair
   signing_key, verifying_key = utils.create_keypair(options.algo, options.seed)

   # Write outputs
   utils.write(options.output+".sk", signing_key, options.overwrite)
   utils.write(options.output+".pk", verifying_key, options.overwrite)
   utils.write(options.output+".mif", verifying_key+signing_key, options.overwrite, tohex=True)

utils.run(main)
