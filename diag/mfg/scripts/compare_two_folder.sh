#!/bin/bash

# compare hardlinks in two directories to make sure they are the same
# only the differences are printed, if there is a difference

u="mfg";
s="hw-mftg-data";
p="/mfg_log/";

diff \
  <(find $p -xdev -type f -links +1 -printf '%i %n %p\n' \
    | sort -n \
    | awk '$1>0&&!i[$1] { i[$1]=++c; } $1>0 { $1=i[$1]; } { print; }' \
    | sort -k 1,1n -k2,2nr) \
  <(ssh $u@$s "find $p -xdev -type f -links +1 -printf '%i %n %p\n' \
    | sort -n \
    | awk '\$1>0&&!i[\$1] { i[\$1]=++c; } \$1>0 { \$1=i[\$1]; } { print; }' \
    | sort -k 1,1n -k2,2nr");