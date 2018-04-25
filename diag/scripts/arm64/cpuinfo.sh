# !/bin/bash
cat /proc/cpuinfo | grep Intel | wc | awk -F " " '{print $1}'
