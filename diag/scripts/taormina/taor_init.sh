#!/bin/sh

export DIAG_HOME=/home/diag/
export DIAG_DIR=$DIAG_HOME/diag
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIAG_HOME/diag/asic/depend_libs/tool/lib64:$DIAG_HOME/diag/asic/depend_libs/mtp_hack:$DIAG_HOME/diag/asic/asic_lib:$DIAG_HOME/diag/asic/depend_libs/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIAG_HOME/diag/asic/lib/tcl8.6
export PATH=$PATH:$DIAG_HOME/diag/asic/lib/

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
