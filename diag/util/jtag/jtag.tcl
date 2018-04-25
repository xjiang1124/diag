proc jtag_rst {slot} {
set result [exec ./jtag_cpurd rst $slot]
}

proc jtag_ena {slot} {   
set result [exec ./jtag_cpurd ena $slot]
}

proc jtag_rd {slot address flag} {
#puts "$slot, $address, $flag"
catch {exec ./jtag_cpurd rd $slot $address $flag} result
#puts $result
return $result
}

proc jtag_wr {slot address data flag} {
#puts "$slot, $address, $data, $flag"
set result [exec ./jtag_cpurd wr $slot $address $data $flag]
}
