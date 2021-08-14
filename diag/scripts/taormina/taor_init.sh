#!/bin/sh

export DIAG_HOME=/home/diag/
export DIAG_DIR=$DIAG_HOME/diag
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIAG_HOME/diag/asic/depend_libs/tool/lib64:$DIAG_HOME/diag/asic/depend_libs/mtp_hack:$DIAG_HOME/diag/asic/asic_lib:$DIAG_HOME/diag/asic/depend_libs/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIAG_HOME/diag/asic/lib/tcl8.6
export PYTHONPATH=$DIAG_HOME/python_files
export PATH=$PATH:$DIAG_HOME/diag/asic/lib:$DIAG_HOME/diag:$DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh
export PATH=$PATH:$DIAG_DIR/asic/lib/tcl8.6

export ASIC_LIB_BUNDLE=$DIAG_HOME/diag/asic
export ASIC_SRC=$ASIC_LIB_BUNDLE/asic_src
export ASIC_LIB=$ASIC_LIB_BUNDLE/asic_lib
export ASIC_GEN=$ASIC_SRC

export MTP_TYPE=MTP_ELBA

export PATH=$PATH:$DIAG_DIR/util/
export PATH=$PATH:$DIAG_DIR/dsp/
export PATH=$PATH:$DIAG_DIR/python/regression
export PATH=$PATH:$DIAG_DIR/python/infra
export PATH=$PATH:$DIAG_DIR/python/infra/dshell
export PATH=$PATH:$DIAG_DIR/python/qa_suite
export PATH=$PATH:$DIAG_DIR/scripts
export PATH=$PATH:$DIAG_DIR/scripts/asic
export PATH=$PATH:$DIAG_DIR/tools

cp /usr/lib/libstdc++.so.6 /fs/nos/home_diag/diag/asic/depend_libs/tool/lib64/libstdc++.so.6

# Elba J2C ID
elba0_id=$(/home/diag/jtag_cpurd_v2 display | grep -A4 "Dev 0" | grep LocId | awk -F " " '{print $3}')
elba1_id=$(/home/diag/jtag_cpurd_v2 display | grep -A4 "Dev 2" | grep LocId | awk -F " " '{print $3}')
export ELBA0_J2C_ID=$elba0_id
export ELBA1_J2C_ID=$elba1_id

# Temporary fix
cp $DIAG_HOME/diag/tools/jtag_cpurd_v2 $DIAG_HOME/diag/util/

