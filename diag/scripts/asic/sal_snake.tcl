# !/usr/bin/tclsh

set slot [lindex $argv 0]

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

set val [_msrd]
if { $val != 0x1 } {
    puts "OW sanity test failed!"
    exit 0
}
#plog_start $fn
#set err_cnt_init [ plog_get_err_count ]

# start test snake test
cd ../esam_pktgen_llc_no_mac_sor
sal_asic_init 2
sal_top_stream_load_snake_traffic 0 10
sleep 1
sal_top_stream_start_snake_traffic 0 10
sleep 1
sal_top_stream_load_snake_traffic 0 20
sleep 1
sal_top_stream_start_snake_traffic 0 20
sleep 1


# check if pkt is running
sal_top_get_cntr 0
sleep 60
sal_top_get_cntr 0
find_avg_rate 0 4000

sal_top_stream_stop_snake_traffic 0
puts "Counters after stop snake"
sal_top_get_cntr 0
sal_top_eos 0

#set err_cnt_fnl [ plog_get_err_count ]
#diag_close_ow_if $port $slot
#puts "SNAKE TEST DONE"
#plog_stop
exit 0