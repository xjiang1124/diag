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
set simplified [lindex $argv 8]
set ddr_hc_training [lindex $argv 9]
set run_ddr_test    [lindex $argv 10]
set logEn    [lindex $argv 11]
set pct      [lindex $argv 12]
set joo      [lindex $argv 13]
set port 10

if {$logEn == ""} {
    set logEn 1
}

puts "sn: $sn; slot: $slot; int_lpbk: $int_lpbk; vmarg: $vmarg; use_zmq: $use_zmq; offload: $offload; esecEn: $esecEn; simplified: $simplified; logEn: $logEn; ddr_hc_training: $ddr_hc_training; run_ddr_test: $run_ddr_test; pct: $pct; joo: $joo"
set err_cnt 0

#set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

set MTP_TYPE $::env(MTP_TYPE)
set ASIC_TYPE $::env(ASIC_TYPE)

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

if {($MTP_TYPE == "MTP_ELBA") || ($MTP_TYPE == "MTP_CAPRI") || ($MTP_TYPE == "MTP_TURBO_ELBA") || ($MTP_TYPE == "MTP_MATERA")} {
    set uut "UUT_$slot"
    set card_type $::env($uut)
    puts "card type: $card_type; UUT: $uut"

    set port 10
    if {$MTP_TYPE == "MTP_TURBO_ELBA"} {
        set port [get_port_turbo $slot]
        set slot 1
    }
    if {$MTP_TYPE == "MTP_MATERA"} {
        set port $slot
        set slot $slot
    }

    if {[string first "LACONA" $card_type] != -1} {
        set arm_freq 2000
    }
    if {$MTP_TYPE == "MTP_ELBA" || ($MTP_TYPE == "MTP_TURBO_ELBA") || ($MTP_TYPE == "MTP_MATERA")} {
        puts "Elba MTP"
        set ddr_freq 3200
        if { $card_type == "LACONA32DELL"   ||
             $card_type == "LACONA32"       ||
             $card_type == "PENSANDO" } {
            set ddr_freq 2400
        }
        if { $card_type == "GINESTRA_D4" } {
            set l1_cmd "gig_l1_screen_diag $sn $port $slot $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 3200 $int_lpbk $vmarg $offload $esecEn $logEn $simplified $ddr_hc_training $run_ddr_test"
            source .tclrc.diag.gig
        } elseif { $card_type == "GINESTRA_D5" } {
            set l1_cmd "gig_l1_screen_diag $sn $port $slot $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 5600 $int_lpbk $vmarg $offload $esecEn $logEn $simplified $ddr_hc_training $run_ddr_test $pct $pct $pct"
            source .tclrc.diag.gig
        } elseif { ($card_type == "MALFA")   ||
                   ($card_type == "POLLARA") ||
                   ($card_type == "LENI") ||
                   ($card_type == "LENI48G") } {
            set l1_cmd "sal_l1_screen_diag $sn $port $slot $mode 0 $use_zmq 127.0.0.1 0 1 0 0 1 $arm_freq 6400 $int_lpbk $vmarg $offload $esecEn $logEn $run_ddr_test"
            source .tclrc.diag.sal
            source /home/diag/diag/scripts/asic/sal_diag_utils.tcl
        } else {
            set l1_cmd "elb_l1_screen_diag $sn $port $slot $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq $ddr_freq $int_lpbk $vmarg $offload $esecEn $logEn $simplified $ddr_hc_training $run_ddr_test"
            source .tclrc.diag.elb.new
        }
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
            set l1_cmd "elb_l1_screen_diag $sn $port 10 $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 3200 $int_lpbk $vmarg $offload 0 $logEn 0 0 1" 
        }
    } else {
        if { $ELBA1_ID == "" } {
        } else {
            set port $ELBA1_ID
            set l1_cmd "elb_l1_screen_diag $sn $port 10 $mode 0 $use_zmq 127.0.0.1 0 1 0 1 1 $arm_freq 3200 $int_lpbk $vmarg $offload 0 $logEn 0 0 1" 
        }
    }
    source .tclrc.diag.elb.new
    puts "Resetting Elba"
    diag_open_j2c_if $port 10
    elb_card_rst $port $slot hod 3200 3000 0 0 "127" 0 1 normal 0 0
    diag_close_j2c_if $port $slot
    
} else {
   puts "[ERROR] l1_test.tcl INVALID PLATFORM/MTP TYPE\n"
   return -1
}

set err_cnt_init [ plog_get_err_count ]

# esec_l1 reboot wati time
set ::CAP_GPIO3_PWR_OFF_DUR 5000

if {$use_zmq == 0} {
    if {$ASIC_TYPE == "SALINA"} {
        puts "Salina L1"
        set slot $slot
        set slot $slot

        set ::slot $slot
        set ::port $port
        
        diag_close_j2c_if $port $slot
        diag_open_j2c_if $port $slot
        diag_close_j2c_if $port $slot
        
        after 1000
        diag_close_ow_if $port $slot
        after 1000
        diag_open_ow_if $port $slot
        after 1000
        sal_ow_axi
        
        csr_write sal0.ms.ms.cfg_ow 3
        after 500
        rd sal0.ms.ms.cfg_ow
        
        puts "_msrd"
        set rtn [eval _msrd]
        puts $rtn

        if {$joo == 0} {
            sal_ow
        } else {
            sal_j2c
        }

        reset_to_proto_mode
        sal_print_voltage_temp_from_j2c
        set_pollara_frequency

        set err_cnt_init [ plog_get_err_count ] ;# WA to jtag issue: ignore errs from set_pollara_freq

        set err_cn [eval $l1_cmd]
        set err_cnt 0

        diag_close_j2c_if $port $slot
    } else {
        puts "Regular L1"
        diag_open_j2c_if $port $slot
        set err_cn [eval $l1_cmd]
        set err_cnt 0

        diag_close_j2c_if $port $slot
    }
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

