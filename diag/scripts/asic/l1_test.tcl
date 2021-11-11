# !/usr/bin/tclsh
puts "argv: $argv"

proc test_proc {input} {
    return $input
}

set sn       [lindex $argv 0]
set slot     [lindex $argv 1]
set mode     [lindex $argv 2]
set int_lpbk [lindex $argv 3]
set vmarg    [lindex $argv 4]
set use_zmq  [lindex $argv 5]
set offload  [lindex $argv 6]
set esecEn   [lindex $argv 7]
set port 10

puts "sn: $sn; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; use_zmq: $use_zmq; offload: $offload; esecEn: $esecEn"
set err_cnt 0

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)

catch {
    set ELBA0_ID $::env(ELBA0_J2C_ID)
    set ELBA1_ID $::env(ELBA1_J2C_ID)
}

source /home/diag/diag/scripts/asic/asic_tests.tcl

set zmq_conn tcp://127.0.0.1:55000/
global G_USE_ZMQ
global G_ZMQ_CONN
global G_SLOT
set G_USE_ZMQ $use_zmq
set G_ZMQ_CONN $zmq_conn
set G_SLOT $slot
set arm_freq 3000

puts "sn: $sn; slot: $slot"
cd $ASIC_SRC/ip/cosim/tclsh

if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_CAPRI") || ($MTP_TYPE == "MTP_TURBO_ELBA")} {
    set uut "UUT_$slot"
    set card_type $::env($uut)
    puts "card type: $card_type; UUT: $uut"

    if {$MTP_TYPE == "MTP_TURBO_ELBA"} {
        set port [get_port_turbo $slot]
        set slot 1
    }

    if {[string first "LACONA" $card_type] != -1} {
        set arm_freq 2000
    }
    if {$MTP_TYPE == "MTP_ELBA" || ($MTP_TYPE == "MTP_TURBO_ELBA")} {
        puts "Elba MTP"
        set ddr_freq 3200
        if { $card_type == "LACONA32DELL"   ||
             $card_type == "LACONA32"       ||
             $card_type == "PENSANDO" } {
            set ddr_freq 2400
        }

        set l1_cmd "elb_l1_screen_diag $sn 10 $slot $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq $ddr_freq $int_lpbk $vmarg $offload $esecEn" 
        source .tclrc.diag.elb.new
    }
    if {$MTP_TYPE == "MTP_CAPRI"} {
        puts "Capri MTP"
        if { $card_type == "NAPLES25"    ||
             $card_type == "NAPLES25SWM" ||
             $card_type == "NAPLES25SWMDELL" ||
             $card_type == "NAPLES25OCP" ||
             $card_type == "NAPLES25WFG"} {
            set core_freq 417.0
        } else {
            set core_freq 833.0
        }

        set l1_cmd "cap_l1_screen_diag $sn 10 $slot 0 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn"
        source .tclrc.diag.new
    }
} elseif {$MTP_TYPE == "MTP_TOR"} {
    puts "TOR MTP"
    exec cat /home/diag/diag/scripts/taormina/vtysh_port_shutdown.sh | vtysh
    if { $slot == 1 } {
        if { $ELBA0_ID == "" } {
        } else {
            set port $ELBA0_ID
            set l1_cmd "elb_l1_screen_diag $sn $port 10 $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 3200 $int_lpbk $vmarg $offload $esecEn" 
        }
    } else {
        if { $ELBA1_ID == "" } {
        } else {
            set port $ELBA1_ID
            set l1_cmd "elb_l1_screen_diag $sn $port 10 $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 3200 $int_lpbk $vmarg $offload $esecEn" 
        }
    }
    source .tclrc.diag.elb.new
} else {
   puts "[ERROR] l1_test.tcl INVALID PLATFORM/MTP TYPE\n"
   return -1
}

set err_cnt_init [ plog_get_err_count ]

# esec_l1 reboot wati time
set ::CAP_GPIO3_PWR_OFF_DUR 5000

if {$use_zmq == 0} {
    puts "Regular L1"
    diag_open_j2c_if $port $slot
    set err_cn [eval $l1_cmd]
    set err_cnt 0

    diag_close_j2c_if $port $slot
} else {
    puts "ZMQ L1"
    diag_open_zmq_if $zmq_conn $slot
    set err_cnt [cap_l1_screen_diag $sn 10 $slot 1 $zmq_conn 0 1 1 1 1 $core_freq $int_lpbk $vmarg $offload $esecEn]

    diag_close_zmq_if
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot

}

set err_cnt_fnl [ plog_get_err_count ]

# Print twice for DSP to capture signature
if { $err_cnt_init != $err_cnt_fnl } {
    puts "L1 TEST FAILED"
    puts "L1 TEST FAILED"
} else {
    puts "L1 TEST PASSED"
    puts "L1 TEST PASSED"
}

