source .tclrc.diag.arm

set card_type $::env(CARD_TYPE)
puts "card_type: $card_type"
set srds_list [cap_get_eth_srds_list $card_type]
puts "srds_list: $srds_list"
cap_upload_spico
cap_eth_srds_prbs $srds_list 60 25g 0


puts "Snake Done"

