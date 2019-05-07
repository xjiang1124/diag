#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import optparse
import os
import utils
import binascii

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Add encrypted OTP content to flash")
   parser.add_option("--otp_cm", help="CM OTP content to add", metavar="FILE.bin")
   parser.add_option("--otp_sm", help="SM OTP content to add", metavar="FILE.bin")
   parser.add_option("--flash", help="flash image", metavar="FILE.bin")
   parser.add_option("--addr", help="OTP flash section address",  metavar="NUMBER", type=int)
   parser.add_option("--otp_out", help="Added OTP content (basename)", metavar="FILE")
   parser.add_option("--puf", help="PUF type (light or flex)", choices=['light', 'flex'])

   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")

   # Read input
   flash = utils.read(options.flash)

   otpcm = open(options.otp_cm, 'rb').read()
   otpsm = open(options.otp_sm, 'rb').read()
   flash, otp_section = utils.add_OTP_to_flash(options.puf, flash,options.addr,otpcm,otpsm)

   # Write output
   utils.write(options.flash, flash, tohex=False)
   utils.write(options.flash[:-4]+".hex", flash, tohex=True)
   utils.write(options.otp_out+".bin", otp_section, tohex=False)
   utils.write(options.otp_out+".hex", otp_section, tohex=True)

utils.run(main)
