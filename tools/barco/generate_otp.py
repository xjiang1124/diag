#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import os
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Generate OTP content", usage="%program input.txt output.hex")
   parser.add_option("--algo", help="authentication algorithm")
   parser.add_option("--cm_input", help="CM OTP part input", metavar="FILE.txt")
   parser.add_option("--sm_input", help="SM OTP part input", metavar="FILE.txt")
   parser.add_option("--output", help="basename for output file (extension .mif will be added)", metavar="FILE")
   parser.add_option("--esecboot", help="Type of boot for esecure firmware", choices=['unsecure','secure'], default='unsecure')
   parser.add_option("--hostboot", help="Type of boot for host firmware",    choices=['unsecure','signed','secure'], default='unsecure')
   parser.add_option("--frksize", help="FRK size in bytes", default=16)

   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.algo:
      parser.error("missing --algo argument")
   if not (options.cm_input or options.sm_input):
      parser.error("missing either --cm_input or --sm_input option")
   if not options.output:
      parser.error("missing --output argument")

   output = ''

   if options.cm_input:
      # Generate CM OTP
      txtcm = utils.read(options.cm_input)
      # Get content from txt
      otpcm = utils.OTPCM(options.algo, int(options.frksize))
      otpcm.set_txt(txtcm)
      if options.esecboot != 'unsecure':
         otpcm.set_bits("ESEC_SECUREBOOT", "1")
      #Write to binary
      bincm = otpcm.get_bin()
      output = bincm

   if options.sm_input:
      # Generate CM OTP
      txtsm = utils.read(options.sm_input)
      # Get content from txt
      otpsm = utils.OTPSM(options.algo, int(options.frksize))
      otpsm.set_txt(txtsm)
      if options.hostboot != 'unsecure':
         otpsm.set_bits("HOST_SECUREBOOT", "1")
      #Write to binary
      binsm = otpsm.get_bin()
      output += binsm

   # Write output
   utils.write(options.output+".bin", output)
   utils.write(options.output+".mif", output, tohex=True)

utils.run(main)
