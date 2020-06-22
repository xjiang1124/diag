#!/usr/bin/env tclsh
package require Expect

set temp_ctl_ip "192.168.74.205"
proc check_temp {_ip} {
log_user 0
spawn telnet $_ip 5025
expect "'^]'."
send ":SOURCE:CLOOP1:PVALUE?\r"
expect  "*.*"
set a $expect_out(buffer)
set retVal [lindex [split $a] 4]
send "\35"
expect "telnet>"
# Tell Telnet to quit.
send "quit\r"
expect eof
return $retVal
}
proc set_temp {_ip _val} {
log_user 0
spawn telnet $_ip 5025
expect "'^]'."
send ":SOURCE:CLOOP1:SPOINT $_val\r"
send ":SOURCE:CLOOP1:SPOINT?\r"
expect "*.*"
send "\35"
set a $expect_out(buffer)
expect "telnet>"
# Tell Telnet to quit.
exp_send -- "quit\r"
expect eof
#    puts [split $a]
return [lindex [split $a] 9]
}

proc temp_loop {{temp_list {5 25 50}} {num_loop 1}} {
    set temp_ctl_ip "192.168.74.205"
    plog_msg $temp_ctl_ip

    for {set loop 0} {$loop < $num_loop} {incr loop} {
        plog_msg "temp_list $temp_list"
        foreach temp $temp_list {
            set_temp $temp_ctl_ip $temp
            plog_msg "temp $temp"
            sleep 300
            for {set ite 0} {$ite < 10} {incr ite} {
                set t [check_temp $temp_ctl_ip]
                plog_msg "Current temperature: $t"
                sleep 300
            }
        }
        set temp_list [lreverse $temp_list]
    }
}
