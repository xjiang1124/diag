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
fmt_win = "  - {}: ./qa_suite.py pltf={} mode=\"{}\"\n"
fmt_win_skip = "  - {}: echo \"Skipped!\"\n"
file = open('qa_suite_tmux_config.yml', 'w')
file.write(title)
for k, v in chassis_config.iteritems():
    print v["SKIP"]
    #print fmt_win.format(k, k, v["MODE"])
    if v["SKIP"] == True:
        file.write(fmt_win_skip.format(k))
    else:
        file.write(fmt_win.format(k, k, v["MODE"]))

file.close()
