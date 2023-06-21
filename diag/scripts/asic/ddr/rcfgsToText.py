#!/usr/bin/python
import os
import sys
import re
sys.path.append(os.path.join(os.environ['ASIC_SRC'],'ip','cosim','elba','ddr','regconfig'))
from collections import namedtuple, OrderedDict
import argparse
import copy
import ddr_utils
import json



util = ddr_utils.DdrUtils()

# this is a tuple of ddict , vals
#ref_regconfig = util.read_and_decode_regconfig(['$ASIC_SRC/ip/cosim/elba/ddr/regconfig/modconfig_ref/modconfig.regconfig.h.CTL', '$ASIC_SRC/ip/cosim/elba/ddr/regconfig/modconfig_ref/modconfig.regconfig.h.PHY', '$ASIC_SRC/ip/cosim/elba/ddr/regconfig/modconfig_ref/modconfig.regconfig.h.PI'])

ext = ['CTL','PHY','PI']
regs = [ 'mc0_0', 'mc0_1', 'mc1_0', 'mc1_1', ]
inst = [ 0,0,1,1 ]
core = [ 0,1,0,1 ]
rcfgs ={}


for idx,r in enumerate(regs):
   rcfgs[r] = util.read_and_decode_regconfig(['gen.%s.regconfig.h.%s'%(r,e) for e in ext])
# *********    Old flow :  dump overlay
#   util.regconfig_overlay_dump_file(ref_regconfig,rcfgs[r],'%s_overlay.c'%(r))
# *********    New flow :  dump ddr table
   #util.update_elb_tdfi_settings(rcfgs[r])
   #update_frac_vals(util,r,rcfgs[r])
   dbg_string = '''\
#
# Source file : $ASIC_SRC/ip/cosim/giglio/ddr/regconfig/
# Comment     :
#
'''
   util.regconfig_addr_data_dump_file('%s_%s.txt'%(sys.argv[1], r),rcfgs[r],dbg_string)
   util.regconfig_tcl_dump_file('diag_%s_%s.tcl'%(sys.argv[1], r),rcfgs[r],inst[idx],core[idx],dbg_string)


for i in regs:
    for j in ext:
        outputFile = "%s%sFieldInfo.txt" % (i, j)
        tmp  = json.dumps(rcfgs[i][0][j],
                 skipkeys = True,
                     allow_nan = True,
                     indent = 6)
        f = open(outputFile, "w+")
        f.write(tmp)
        f.close()

for i in regs:
    for j in ext:
        outputFile = "%s%sRegVal.txt" % (i, j)
        tmp  = json.dumps(rcfgs[i][1][j],
                 skipkeys = True,
                     allow_nan = True,
                     indent = 6)
        f = open(outputFile, "w+")
        f.write(tmp)
        f.close()



#How to reload the data

#with open('mc0_0CTLFieldInfo.txt', 'r') as read_file:
#    loaded_dictionaries = json.loads(read_file.read())
#    print(loaded_dictionaries[u'0'])


for i in ext:
    outputFile = "%sgenFunc.tcl" % (i)
    j = 'mc0_0'
    #counter = 0
    add = "0x0"
    if(i == 'PI'):
        add = "0x800"
    if(i == 'PHY'):
        add = "0x2000"
    f = open(outputFile, "w+")
    for l in rcfgs[j][0][i].keys():
        offSet = hex(int(l)+int(add, 16))
        prt = "#################################\n\nproc mc_%s_print {} {\n    puts \"addr: %s\"\n    #fields\n" % (offSet, offSet)
        for m in range(len(rcfgs[j][0][i][l])):
            fieldName = rcfgs[j][0][i][l][m][0]
            fieldAcc = rcfgs[j][0][i][l][m][1]
            start = rcfgs[j][0][i][l][m][2]
            numBits = rcfgs[j][0][i][l][m][3]
            defVal = rcfgs[j][0][i][l][m][4]
            prt = prt + ("    puts \"field_name   :%s \"\n    puts \"field_access :%s \"\n    puts \"field_bitpos :%s \"\n    puts \"field_size   :%s \"\n    puts \"default field_value  :%s \"\n" % (fieldName, fieldAcc, start, numBits, defVal))
        prt = prt + ("} \n\nproc mc_%s_write_reg { inst_id core_id data } {\n    mc_dhs_addr_write  $inst_id $core_id %s $data\n}\n\nproc mc_%s_read_reg { inst_id core_id  } {\n    set rdata [mc_dhs_addr_read $inst_id $core_id %s]\n\n    return $rdata\n}\n\n" % (offSet, offSet, offSet, offSet))
        f.write(prt)
        for m in range(len(rcfgs[j][0][i][l])):
            #counter+=1
            fieldName = rcfgs[j][0][i][l][m][0]
            start = rcfgs[j][0][i][l][m][2]
            numBits = rcfgs[j][0][i][l][m][3]
            tmp = "proc mc_%s_write_field { inst_id core_id data } { \n    gig_mc_reg_read_modify_write 0 $inst_id $core_id %s %s %s $data \n} \n \nproc mc_%s_read_field { inst_id core_id } { \n    set rdata [gig_mc_read_field 0 $inst_id $core_id %s %s %s ] \n\n    return $rdata \n}\n\n" % (fieldName, offSet, start, numBits, fieldName, offSet, start, numBits)
            f.write(tmp)
    #print(counter)
    f.close()






















