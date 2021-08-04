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

cd $ASIC_SRC/ip/cosim/tclsh
if {$MTP_TYPE == "MTP_ELBA"} {
    puts "Elba MTP"
    source .tclrc.diag.elb.new
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
elb_print_voltage_temp

puts "Getting ASIC status - Done"

