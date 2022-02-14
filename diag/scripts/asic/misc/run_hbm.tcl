proc cap_l1_hbm_ctc_loop { {num_ite 1} {tgt_temp 90}} {
    for {set i 0} {$i < $num_ite} {incr i} { 
        plog_msg "=== Ite #$i ==="
        pen_aapl_hbm_diag_ctc 0x1
        pen_aapl_hbm_run_ctc_diag 0x1
        die_temp_fan_control $tgt_temp
    }
}

set sn [lindex $argv 0]
set slot_num [lindex $argv 1]
set hbm_freq [lindex $argv 2]
set temp [lindex $argv 3]
set num_ite [lindex $argv 4]

puts "sn: $sn; slot_num: $slot_num; hbm_freq $hbm_freq; temp: $temp; ite: $num_ite"

set ASIC_LIB_BUNDLE "/home/diag/diag/asic/"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"
set DIAG_SRC "/home/diag/diag/scripts/asic/"

set log_file $sn.log

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.new

plog_start $log_file 1000000

diag_open_j2c_if 10 $slot_num
#proc cap_jtag_chip_rst { j2c_port j2c_slot {use_zmq 0} {zmq_conn ""} { first_article 1 } { proto_mode 1 } {bit6_power_cycle 0} {core_freq 833} {arm_freq 2200}}
cap_jtag_chip_rst 10 $slot_num 0 "" 1 1 0 1100.0

#cap_nwl_setup_pll_raw 1 $hbm_freq
#cap_nwl_hbm_init 0 0 $hbm_freq "sbus_master.hbm.0x055c_2002.rom" 0
cap_nwl_hbm_init 0 0 $hbm_freq "sbus_master.hbm.0x055f_2002.rom" 0

cap_l1_hbm_ctc_loop $num_ite $temp

puts "HBM test Done"

plog_stop

