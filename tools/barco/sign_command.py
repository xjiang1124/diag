#!/usr/bin/env python

""" Copyright (c) 2017 Barco Silex. All Rights reserved """

import optparse
import os
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Sign a command")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--sk", help="developer's signing key - mandatory", metavar="FILE.sk")
   parser.add_option("--cmd", help="command word (32-bit) - mandatory")
   parser.add_option("--param", help="command parameter (32-bit) - mandatory")
   parser.add_option("--challenge", help="random challenge")
   parser.add_option("--output", "-o", help="basename for output files", metavar="FILE")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.sk:
      parser.error("missing --sk argument")
   if not options.algo:
      parser.error("missing --algo argument")
   if not options.cmd:
      parser.error("missing --cmd argument")
   elif len(options.cmd) != 32/4:
      parser.error("--cmd argument should be 32-bit")
   if not options.param:
      parser.error("missing --param argument")
   elif len(options.param) != 32/4:
      parser.error("--param argument should be 32-bit")
   if options.challenge:
      if len(options.challenge) != 128/4:
         parser.error("--challenge argument should be 16 bytes")
   if not options.output:
      parser.error("missing --output argument")

   # Read inputs
   signing_key = utils.read(options.sk, utils.get_privkey_size(options.algo))

   # Sign command
   signature = utils.sign_command(options.algo, signing_key, options.cmd, options.param, options.challenge)

   # Write outputs
   utils.write(options.output+".bin", signature)
   utils.write(options.output+".hex", signature, tohex=True)

utils.run(main)
