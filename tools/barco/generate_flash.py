#!/usr/bin/env python

""" Copyright (c) 2017-2018 Silex Inside. All Rights reserved """

import binascii
import optparse
import utils

def main():
   # Parse arguments
   parser = optparse.OptionParser(description="Generate flash content")
   parser.add_option("--esecA", help="esecure packed firmware input", metavar="FILE.bin")
   parser.add_option("--esecB", help="esecure packed firmware input", metavar="FILE.bin")
   parser.add_option("--hostA", help="host packed firmware input", metavar="FILE.bin")
   parser.add_option("--hostB", help="host packed firmware input", metavar="FILE.bin")
   parser.add_option("--esecA_addr", help="esecure firmware image A address",  metavar="NUMBER", type=int, default=0xFFFFFFFF)
   parser.add_option("--esecB_addr", help="esecure firmware image B address",  metavar="NUMBER", type=int, default=0xFFFFFFFF)
   parser.add_option("--hostA_addr", help="host firmware image A address",  metavar="NUMBER", type=int, default=0xFFFFFFFF)
   parser.add_option("--hostB_addr", help="host firmware image B address",  metavar="NUMBER", type=int, default=0xFFFFFFFF)
   parser.add_option("--size", help="size of the output image", metavar="NUMBER", type=int, default=64*1024)
   parser.add_option("--empty", help="generate empty flash", action="store_true")
   parser.add_option("--output", "-o", help="basename for flash content output (generated in binary (.bin) & hexadecimal word (.hex) format)", metavar="FILE")
   options, args = parser.parse_args()

   # Check arguments
   if args:
      parser.error("too many arguments")
   if not options.output:
      parser.error("missing --output argument")

   # Read inputs
   esecA = utils.read(options.esecA)
   esecB = utils.read(options.esecB)
   hostA = utils.read(options.hostA)
   hostB = utils.read(options.hostB)

   # Generate flash
   output = utils.gen_flash(options.empty,options.size,options.esecA_addr,options.esecB_addr,options.hostA_addr,options.hostB_addr,esecA,esecB,hostA,hostB)

   # Write output
   utils.write(options.output+'.bin',  output)
   utils.write(options.output+'.hex',  output, tohex=True)

utils.run(main)
