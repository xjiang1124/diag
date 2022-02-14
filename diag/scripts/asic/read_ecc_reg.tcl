# !/usr/bin/tclsh

set slots       [lindex $argv 0]

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.elb.new
source /home/diag/diag/scripts/asic/asic_tests.tcl

set reg_list {0x305305e4 0x30530454 0x30530458 0x30530464 0x30530468 0x3053046c 0x30530470}

set slot_list [split $slots ","]

set ret_list [list -1 -1 -1 -1 -1 -1 -1 -1 -1 -1]

plog_msg "ret_list $ret_list"

plog_msg "=== Dumping ECC info ==="
set idx 0
foreach slot $slot_list {
    set ret 0
    
    plog_msg "=== Slot $slot ==="
    
    set port [mtp_get_j2c_port $slot]
    set slot1 [mtp_get_j2c_slot $slot]
    diag_open_j2c_if $port $slot1
    
    diag_open_j2c_if $port $slot1
    foreach reg $reg_list {
        set val [regrd 0 $reg]
        if { $val != 0 } {
            plog_msg "P000 Reg $reg: $val"
            set ret -1
        }
        plog_msg "Reg $reg: $val"
    }
    check_ecc_intr
    elb_ddr_rst_ecc_intr_counter
    diag_close_j2c_if $port $slot1

    #if {$idx == 0} {
    #    set ret -1
    #}

    if {$ret != 0} {
        plog_msg "ECC ERROR HAPPENED on slot $slot"
    } else {
        plog_msg "ECC CLEAN on slot $slot"
        set slot_idx [expr $slot-1]
        lset ret_list $slot_idx 0
    }
    incr idx
}
plog_msg "ECC COLLECTION RESULT $ret_list Done"
plog_msg "ECC COLLECTION DONE"

