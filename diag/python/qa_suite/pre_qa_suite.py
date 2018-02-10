#!/usr/bin/env python

import sys
sys.path.append("../lib")
import common

# Generate tmuxanitor script
filename = "config/chassis_info.yaml"
chassis_config = common.load_yaml(filename)

title = """name: qa_suite_tmux
root: ./
windows:
"""
fmt_win = "  - {}: qa_suite.py pltf={} mode=\"{}\"\n"
file = open('qa_suite_tmux_config.yml', 'w')
file.write(title)
for k, v in chassis_config.iteritems():
    #print fmt_win.format(k, k, v["MODE"])
    file.write(fmt_win.format(k, k, v["MODE"]))

file.close()
