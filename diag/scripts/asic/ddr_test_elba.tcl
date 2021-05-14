# !/usr/bin/tclsh
#
#package require cmdline
source ./cmdline.tcl
set parameters {
    {slot.arg       ""          "Slot number"}
    {mode.arg       "nod"       "ASIC mode"}
    {diag_dir.arg   "/home/diag/" "Diag home directory"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot        $arg(slot)
set mode        $arg(mode)
set DIAG_DIR    $arg(diag_dir)

puts "slot: $slot; mode: $mode"

set ASIC_LIB_BUNDLE "$DIAG_DIR/diag/asic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "$DIAG_DIR/diag/scripts/asic/"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.elb.new

plog_start ddr_test_slot$slot.log
diag_open_j2c_if 10 $slot
elb_card_rst 10 $slot $mode 3200 1600 0 0 "127.0.0.1" 1 1 normal 0 0

sknobs_set_value elb0/mc/use_hardcoded_training 0
run_ddr1 3200; mc_init_start; mc_init_done
ddr_train_chk

plog_stop

