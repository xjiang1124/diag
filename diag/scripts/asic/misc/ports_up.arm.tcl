source .tclrc.diag.arm

#cap_snake_test_mtp { snake_num  { pktsize 8000 } { mac_serdes_int_lpbk 1 } { hbm_speed 1600 }  { is_mtp 1 } { core_freq 833.0 } { delete_stream_cfg 1 } {duration 60} {fan_ctrl 0} {tgt_temp 105} {mac_speed "mac100g"} {is_arm 0} }
cap_snake_test_mtp 4 8000 0 1600 1 833.0 1 60 0 105 "mac100g"

puts "Snake Done"

