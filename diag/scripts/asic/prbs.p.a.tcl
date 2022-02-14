source .tclrc.diag.arm

set card_type $::env(CARD_TYPE)
puts "card_type: $card_type"
set srds_list [cap_get_pcie_srds_list $card_type]
puts "srds_list: $srds_list"
cap_upload_pcie_spico
cap_pcie_srds_prbs $srds_list 60 16g 0 prbs31 1

puts "Snake Done"

