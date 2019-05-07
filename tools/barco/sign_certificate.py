#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import os
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Sign a certificate")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--sk", help="manufacturer's signing key - mandatory", metavar="FILE.sk")
   parser.add_option("--input", "-i", help="certificate to be signed - mandatory", metavar="FILE.txt")
   parser.add_option("--output", "-o", help="basename for output files", metavar="FILE")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.input:
      parser.error("missing --input argument")
   if not options.algo:
      parser.error("missing --algo argument")
   if not options.output:
      options.output = os.path.splitext(options.input)[0]+".cert"
   if options.input==options.output:
      parser.error("input and output files are identical")

   # Read inputs
   txt_certificate = utils.read(options.input)
   signing_key = utils.read(options.sk, utils.get_privkey_size(options.algo))

   # Sign certificate
   bin_certificate = utils.sign_certificate(options.algo, txt_certificate, signing_key)

   # Write outputs
   utils.write(options.output+".cert", bin_certificate)
   utils.write(options.output+".hex", bin_certificate, tohex=True)

utils.run(main)
