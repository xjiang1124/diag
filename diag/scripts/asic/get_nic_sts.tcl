# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

set slot     [lindex $argv 0]
set port 10

set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)

puts "Getting ASIC status - slot: $slot"
source /home/diag/diag/scripts/asic/asic_tests.tcl

cd $ASIC_SRC/ip/cosim/tclsh
if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_TURBO_ELBA")} {
    puts $MTP_TYPE
    source .tclrc.diag.elb.new

    if { $MTP_TYPE == "MTP_TURBO_ELBA" } {
        set port [get_port_turbo $slot]
        set slot 1
    }
} elseif {$MTP_TYPE == "MTP_TOR"} {
    puts "TOR MTP"
    if { $slot == 1 } {
        set port 0x3021
    } else {
        set port 0x3031
    }
    set slot 10
    source .tclrc.diag.elb.new

} else {
    puts "Capri MTP"
    source .tclrc.diag.new
}

diag_open_j2c_if $port $slot
rst_arm0_set 0
ssi_cpld_write 0x20 0x0
elb_print_voltage_temp

if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_TURBO_ELBA") || $MTP_TYPE == "MTP_TOR"} {
    puts "Getting ECC status"
    set ecc_reg_list [list 0x305305e4 0x30530454 0x30530458 0x30530464 0x30530468 0x3053046c 0x30530470]
    foreach ecc_reg $ecc_reg_list {
        set val [regrd 0 $ecc_reg]
        puts "Reg $ecc_reg; value: $val"
    }
}

puts "Getting ASIC status - Done"

