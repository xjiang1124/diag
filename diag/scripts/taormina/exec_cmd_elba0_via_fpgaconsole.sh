#!/bin/bash

# barf on error
set -e
# configure port, exit immediately, don't reset
picocom -qrX -b 115200 -f h /dev/ttyUL0
# send contents of cmd.txt, line by line, 
# waiting 1 sec in-between, after host sends reply
while read ln; do
     echo "$ln" | picocom -qrix 1000 /dev/ttyUL0
done < /fs/nos/home_diag/diag/scripts/taormina/cmd_elba0.txt
