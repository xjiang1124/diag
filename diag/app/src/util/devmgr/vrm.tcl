#!/usr/bin/env tclsh

proc vrm_get_iout {devName} {
    set result [exec ./devmgr -uut=UUT_1 -dev=$devName -riout]
    return $result
}

proc vrm_get_vout {devName} {
    set result [exec ./devmgr -uut=UUT_1 -dev=$devName -rvout]
    return $result
}

proc vrm_set_vout {devName voutMv} {
    set result [exec ./devmgr -uut=UUT_1 -dev=$devName -margin -mgmode=mv -vout=$voutMv]
    return $result
}

set result [vrm_get_vout CAP0_CORE_DVDD]
puts "vout: $result"

set vout 850
puts "Set vout to $vout mv"
vrm_set_vout CAP0_CORE_DVDD $vout

set result [vrm_get_vout CAP0_CORE_DVDD]
puts "vout: $result"

set result [vrm_get_iout CAP0_CORE_DVDD]
puts "iout: $result"

