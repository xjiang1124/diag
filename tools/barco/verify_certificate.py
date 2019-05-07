#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Verify a certificate")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--pk", help="manufacturer's public key", metavar="FILE.pk")
   parser.add_option("--input", "-i", help="certificate to be verified - mandatory", metavar="FILE.cert")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.input:
      parser.error("missing --input argument")
   if not options.algo:
      parser.error("missing --algo argument")

   # Read input
   bin_certificate = utils.read(options.input)

   # Decode certificate
   print utils.decode_certificate(options.algo, bin_certificate)

   # Verify certificate
   if options.pk:
      verifying_key = utils.read(options.pk, utils.get_pubkey_size(options.algo))
      if utils.verify_certificate(options.algo, bin_certificate, verifying_key):
         print "Certificate %s is valid" % options.input
      else:
         raise utils.RunError("certificate %s has invalid signature" % options.input)

utils.run(main)
