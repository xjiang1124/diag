set core_freq_list {1100 833 417 208}
set arm_freq_list {2200 2000 1600 1100}

for {set i 1} {$i < 11} {incr i} {
    puts "==== Slot $i ==="
    diag_open_j2c_if 10 $i
    #foreach freq $core_freq_list {
    #    set nom [cap_get_nominal_voltag vdd $freq 0]
    #}
    foreach freq $arm_freq_list {
        set nom [cap_get_nominal_voltag arm $freq 0]
    }

    diag_close_j2c_if 10 $i
}

