# !/usr/bin/tclsh

set slot [lindex $argv 0]
# test types:
# esam_pktgen_llc_no_mac_sor : no ddr + no mac
# esam_pktgen_llc_sor        :  no ddr + mac
# esam_pktgen_ddr_no_mac_sor : ddr + no mac
# esam_pktgen_ddr_sor        : ddr + mac  <-- stress both ddr and mac
set test_type [lindex $argv 1]
set fn [lindex $argv 2]

set ASIC_LIB_BUNDLE "/home/diag/snake_test/nic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"

#catch {exec turn_on_slot.sh off $slot }
#catch {exec turn_on_slot.sh on $slot}
#after 10000
#catch {exec turn_on_slot.sh on $slot}
#after 1000
#exec jtag_accpcie_salina clr $slot
cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port
diag_close_j2c_if $port $slot
diag_open_j2c_if $port $slot
diag_close_j2c_if $port $slot

after 500
diag_close_ow_if $port $slot
after 500
diag_open_ow_if $port $slot
after 2000
sal_ow_axi

set dd 0
set cnt 0
while { ($dd==0) && ($cnt<10) } {
    csr_write sal0.ms.ms.cfg_ow 3
    after 500
    set dd [ rd sal0.ms.ms.cfg_ow ]
    incr cnt
}
set ret 1
if { $cnt  >= 10 } {
    plog_err "\n\n==== J2C / OW is not working.... Ping HW team\n\n"
    return
}

set val [_msrd]
if { $val != 0x1 } {
    puts "OW sanity test failed!"
    exit 0
}

csr_write sal0.txs.txs\[0].base 0xaabbcc
rds sal0.txs.txs\[0].base
#set err_cnt_init [ plog_get_err_count ]
plog_start $fn
# start test snake test
cd ../$test_type
if {$test_type == "esam_pktgen_ddr_no_mac_sor" || $test_type == "esam_pktgen_ddr_sor"} {
    cdn_ddr5_init 3200
}
if {$test_type == "esam_pktgen_llc_sor" || $test_type == "esam_pktgen_ddr_sor"} {
    sal_aw_srds_powerup_init
    sal_front_panel_port_up
}
# check for lback, should all be 0
sal_mx_gmii_lpbk_get 0 0 0
sal_mx_gmii_lpbk_get 0 1 0
sal_mx_pcs_lpbk_get 0 0 0
sal_mx_pcs_lpbk_get 0 1 0

sal_asic_init 2
sal_top_stream_load_snake_traffic 0 10
sal_top_stream_start_snake_traffic 0 10
sal_top_stream_load_snake_traffic 0 20
sal_top_stream_start_snake_traffic 0 20


# check if pkt is running
sal_top_get_cntr 0
sleep 30
plog_msg "read PMIC"
smbus_read_byte_data 0 0x4f 0xc
smbus_read_byte_data 0 0x4f 0xd
smbus_read_byte_data 0 0x4f 0xe
smbus_read_byte_data 0 0x4f 0xf
sal_top_get_cntr 0
find_avg_rate 5 4000

sal_top_stream_stop_snake_traffic 0
plog_msg "Counters after stop snake"
sal_top_get_cntr 0
sal_pf_cntrs
sal_top_eos 0
plog_stop
exit 0

#set err_cnt_fnl [ plog_get_err_count ]
#diag_close_ow_if $port $slot
#puts "SNAKE TEST DONE"
