# !/usr/bin/tclsh
#
#package require cmdline

set ASIC_LIB_BUNDLE $::env(ASIC_LIB_BUNDLE)
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

source ./cmdline.tcl


set parameters {
    {sn.arg          "FLM00000001"   "Serial Number"}
    {slot.arg        ""              "Slot number"}
    {use_zmq.arg     0               "Use ZMQ"}
    {zmq_srv_ip.arg  ""              "MTP IP"}
    {zmq_port.arg    "55000"         "ZMQ port"}
    {stage.arg       ""              "Esecure program stage"}
    {fn.arg          ""              "File name"}
    {cm_file.arg     ""              "CM file"}
    {sm_file.arg     ""              "SM file"}
    {fw_ptr.arg      ""              "FW image pointer file"}
    {esec_1.arg      ""              "Esecure image 1"}
    {esec_2.arg      ""              "Esecure image 2"}
    {host_1.arg      ""              "Host image 1"}
    {host_2.arg      ""              "Host image 2"}
    {pn.arg          ""              "Part Number"}
    {mac.arg         ""              "MAC address"}
    {mtp.arg         ""              "MTP name"}
    {client_key.arg  "certs/client.key.pem"                      "Client key"}
    {client_cert.arg "certs/client-bundle.cert.pem"              "client cert"}
    {trust_roots.arg "certs/rootca.cert.pem"                     "Root Cert"}
    {backend_url.arg "192.168.67.213:12266#192.168.67.214:12266" "Backend URL"}
}

set usage "- Usage:"
if {[catch {array set options [cmdline::getoptions ::argv $parameters $usage]}]} {
    puts [cmdline::usage $parameters $usage]
    exit
} else {
    parray options
}

set sn          $options(sn)
set slot        $options(slot)
set use_zmq     $options(use_zmq)
set zmq_srv_ip  $options(zmq_srv_ip)
set zmq_port    $options(zmq_port)
set stage       $options(stage)
set fn          $options(fn)
set cm_file     $options(cm_file)
set sm_file     $options(sm_file)
set fw_ptr      $options(fw_ptr)
set esec_1      $options(esec_1)
set esec_2      $options(esec_2)
set host_1      $options(host_1)
set host_2      $options(host_2)
set pn          $options(pn)
set mac         $options(mac)

set mtp         $options(mtp)
set client_key  $options(client_key)
set client_cert $options(client_cert)
set trust_roots $options(trust_roots)
set backend_url   $options(backend_url)

puts "slot: $slot"

if { $use_zmq != 0 } {
    if { $zmq_srv_ip == "" || $zmq_port == ""} {
        error "Need ZMQ SRV IP and port args"
        exit
    }
}

if { $slot == "" } {
    error "Need slot arg"
    exit
}

if {$use_zmq != 0} {
    set zmq_conn "tcp://${arg(zmq_srv_ip)}:${arg(zmq_port)}/"
    puts "zmq_conn: $zmq_conn"
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag

proc cap_get_err_cnt { proc_to_run } {
   plog_msg "===> running  $proc_to_run"
   set in_err [plog_get_err_count]
   {*}$proc_to_run
   set err_cnt  [ expr ( [plog_get_err_count] - $in_err ) ]
   return $err_cnt
}

proc read_pub_ek { sn slot fn } {
    plog_start read_pub_ek_${sn}_slot${slot}.log
    if {$fn == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000

    set pub_ek [cap_chlng_read_pub_ek_str]
    set fp [open $fn w]
    puts -nonewline $fp $pub_ek
    close $fp

    plog_stop
    return 0
}

proc puf_enroll { sn slot fn } {
    plog_msg "sn: $sn; slot: $slot; fn: $fn"
    plog_start puf_enroll_${sn}_slot${slot}.log
    if {$fn == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
    ssi_cpld_write 0x29 0x80
    cap_set_esec_enable_pin
    cap_power_cycle_chk 25 10 $slot
    
    set err_cnt [cap_get_myerr_cnt cap_chlng_enroll_puf_str 0 1 1]

    set pub_ek [cap_chlng_read_pub_ek_str]
    set fp [open $fn w]
    puts -nonewline $fp $pub_ek
    close $fp

    plog_stop
    return $err_cnt
}

proc otp_init { sn slot cm_file sm_file } {
    plog_msg "sn: $sn; slot: $slot; cm_file: $cm_file; sm_file: $sm_file"
    plog_start otp_init_cm_${sn}_slot${slot}.log
    if {$cm_file == "" || $sm_file == ""} {
        plog_err "File name can not be empty"
        plog_stop
        return -1
    }
    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000

    set cmd_cm [list cap_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    set cmd_sm [list cap_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

    set err_cnt_cm [cap_get_myerr_cnt $cmd_cm 0 1 1]
    set err_cnt_sm [cap_get_myerr_cnt $cmd_sm 0 1 1]

    set err_cnt [expr {$err_cnt_cm + $err_cnt_sm}]

    plog_stop
    return $err_cnt
}

proc post_check { sn slot } {
    plog_start post_check_${sn}_slot${slot}.log

    cap_open_if 10 $slot
    regrd 0 0x6a000000

    set ret [cap_secure_post_check 10 10 $slot]
    cap_close_if 10 $slot
    plog_stop
    return $ret
}

proc show_status { sn slot } {
    plog_start show_status_${sn}_slot${slot}.log

    cap_open_if 10 $slot
    regrd 0 0x6a000000

    cap_show_esec_pins
    cap_dump_cpld_sts_spi
    cap_dump_cpld_sts_smb $slot

    cap_close_if 10 $slot
    plog_stop
    return 0
}

proc img_prog {slot fw_ptr esec_1 esec_2 host_1 host_2} {
    plog_start puf_enroll_slot${slot}.log

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200

    set ret [cap_prog_qspi $fw_ptr 0x70010000]
    if {$ret != 0} {
        plog_msg "Failed to program fw_ptr"
        return $ret
    }
    set ret [cap_prog_qspi $esec_1 0x70020000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_1"
        return $ret
    }
    set ret [cap_prog_qspi $esec_2 0x70040000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_2"
        return $ret
    }
    set ret [cap_prog_qspi $host_1 0x70060000]
    if {$ret != 0} {
        plog_msg "Failed to program host_1"
        return $ret
    }
    set ret [cap_prog_qspi $host_2 0x70080000]
    if {$ret != 0} {
        plog_msg "Failed to program host_2"
        return $ret
    }

    plog_stop
    return $ret
}

proc efuse_test {slot} {
    set ret 0
    set bit_loc 127

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    
    #Set to 417 for now.  With CPLD's where EFUSE VDDQ can be disabled/enabled.  On a SWM it will not set an efuse bit at 833Mhz if we enable EFUSE VDDQ after asic reset
    set freq 417

    set cpld_rev [ssi_cpld_read 0x00]
    set cpld_ver [ssi_cpld_read 0x80]
    
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200

    if {   $cpld_ver == 0x17 && $cpld_rev > 0xa     #NAPLES25SWM:  SET EFUSE VDDQ ENABLE
       ||  $cpld_ver == 0x13 && $cpld_rev > 0x9     #NAPLES25
       ||  $cpld_ver == 0x20 && $cpld_rev > 0x2     #NAPLES25 SWM DELL
       ||  $cpld_ver == 0x12 && $cpld_rev > 0xc     #NAPLES100
       ||  $cpld_ver == 0x1C && $cpld_rev > 0x3     #NAPLES100 IBM
       ||  $cpld_ver == 0x1F && $cpld_rev > 0x1  } {   #NAPLES100 HPE
        set cpld_data [ssi_cpld_read 0x10]
        set cpld_data [expr {$cpld_data | 0x20}]
        ssi_cpld_write 0x10 $cpld_data
    }

    cpu_force_global_flags 1
    set bit_read_back [cap_efuse_get_bit $bit_loc]
    if {$bit_read_back == 1} {
        plog_msg "Efuse bit $bit_loc is already programmed; read back $bit_read_back"
    }

    cap_efuse_set_bit $bit_loc
    set bit_read_back [cap_efuse_get_bit $bit_loc]
    if {$bit_read_back != 1} {
        plog_err "Failed to valid efuse bit; read back $bit_read_back"
        set return -1
    }

    if {   $cpld_ver == 0x17 && $cpld_rev > 0xa     #NAPLES25SWM:  SET EFUSE VDDQ ENABLE
       ||  $cpld_ver == 0x13 && $cpld_rev > 0x9     #NAPLES25
       ||  $cpld_ver == 0x20 && $cpld_rev > 0x2     #NAPLES25 SWM DELL
       ||  $cpld_ver == 0x12 && $cpld_rev > 0xc     #NAPLES100
       ||  $cpld_ver == 0x1C && $cpld_rev > 0x3     #NAPLES100 IBM
       ||  $cpld_ver == 0x1F && $cpld_rev > 0x1  } {   #NAPLES100 HPE
        set cpld_data [ssi_cpld_read 0x10]
        set cpld_data [expr {$cpld_data & 0xDF}]
        ssi_cpld_write 0x10 $cpld_data
    }

    diag_close_j2c_if 10 $slot

    return $ret
}

proc esec_gather_pac {sn usb_port slot PN MAC MTP
        {CLIENT_KEY "certs/client.key.pem"} 
        {CLIENT_CERT "certs/client-bundle.cert.pem"}
        {TRUST_ROOTS "certs/rootca.cert.pem"}
        {BACKEND_URL "192.168.67.213:12266#192.168.67.214:12266"}
        {pac_cnt 25} } {

    unset -nocomplain ::CAP_EK_CACHE

    set card_type [cap_get_card_type]
    set pub_ek_fn "pub_ek.tcl.txt"
    set SN $sn

    for {set j 0} {$j < $pac_cnt} {incr j 1} {
        set timestamp_pre [clock seconds]
        set tt [ clock format [clock seconds] -format "%m_%d_%Y_%T" ]
        plog_msg ""
        plog_msg "esec_gather_pac : Iter:$j Begin:: Date:$tt"
        plog_msg ""

        cap_power_cycle_chk 25 $usb_port $slot
        qspi_erase 0
        
        #============================
        # PUF enroll
        set err_cnt [cap_get_err_cnt cap_chlng_enroll_puf_str]

        set pub_ek [cap_chlng_read_pub_ek_str]
        set ::CAP_EK_CACHE($j) $pub_ek

        set fp [open $pub_ek_fn w]
        puts -nonewline $fp $pub_ek
        close $fp
        plog_msg "Enroll PUF done"

        #============================
        # Signing PUB EK
        set tcl_pwd [pwd]
        set DIAG_HOME $::env(DIAG_HOME)
        cd $DIAG_HOME/diag/tools/pki

        if { [catch {exec /home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn $SN -pn "$PN" -mac $MAC -brd_name $card_type -mtp MTP -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL} msg ]} {
            plog_msg "Information about it: $::errorInfo"
        }
        
        if { [catch { exec crc32 ./signed_ek.pub.bin | tee crc32_ek_$j.bin} msg] } {
            plog_msg "Information about it: $::errorInfo"
            return -1
        } else {
            set crc32Val $msg
            plog_msg "CRC32: $crc32Val"
        }

        cd $tcl_pwd
        plog_msg "Signing EK passed"

        #============================
        # Check EK
        if { [catch { exec /home/diag/diag/python/esec/scripts/esec_prog.sh -ek_check } msg] } {
            plog_msg "Information about it: $::errorInfo"
            return -1
        } else {
            plog_msg $msg
            # Check if EK is good
            if {[string first "Signature Algorithm: ecdsa-with-SHA384" $msg] != -1} {
                plog_msg "EK Check Passed"
            } else {
                plog_msg "EK Check Failed"
                return -1
            }
        }
        
        #============================
        # Gen OTP
        if { [catch { exec /home/diag/diag/python/esec/scripts/esec_prog.sh -gen_otp } msg] } {
            plog_msg "Information about it: $::errorInfo"
            return -1
        } else {
            plog_msg $msg
        }

        #============================
        # OTP init
        set cm_file "./images/OTP_cm.hex"
        set sm_file "./images/OTP_sm.hex"
        set cmd_cm [list cap_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
        set cmd_sm [list cap_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

        set err_cnt_cm [cap_get_err_cnt $cmd_cm]
        set err_cnt_sm [cap_get_err_cnt $cmd_sm]

        cap_populate_pac_cache $j [expr ($j==0)] 0

        set tt [ clock format [clock seconds] -format "%m_%d_%Y_%T" ]
        plog_msg "esec_gather_pac :: Iter:$j Completed::  Date:$tt"

        exec rm $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt
        exec rm $DIAG_HOME/diag/tools/pki/pub_ek.tcl.txt
        eval file delete [glob $DIAG_HOME/diag/tools/pki/signed_ek.pub*bin]

        set timestamp_post [clock seconds]
        set time_key_prog [expr {$timestamp_post - $timestamp_pre}]
        
        plog_msg "Per loop Key Prog Time: $time_key_prog"

    }
}

proc esec_prog_optimal_pac {sn usb_port slot PN MAC MTP
        {CLIENT_KEY "certs/client.key.pem"} 
        {CLIENT_CERT "certs/client-bundle.cert.pem"}
        {TRUST_ROOTS "certs/rootca.cert.pem"}
        {BACKEND_URL "192.168.67.213:12266#192.168.67.214:12266"}
        {pac_cnt 25} } {

    set ::CAP_PAC_FILE_SLOT "${::CAP_PAC_FILE}_${slot}"
    #set ::CAP_DUMP_PAC 1
    set ::CAP_REMOVE_PAC_TMP_FILE 0
    
    #remove memory cache
    cap_mem_pwr_up_cache_clear

    esec_gather_pac $sn $usb_port $slot $PN $MAC $MTP $CLIENT_KEY $CLIENT_CERT $TRUST_ROOTS $BACKEND_URL $pac_cnt
    
    #dump pac
    cap_dump_pac_cache
    
    #find the optimal pac
    cap_eval_pac_score_all
    
    #find pac with highest score
    set xx [ cap_get_best_pac_score ]
    if { $xx == -1 } {
        plog_err "cap_esec_prog_optimal_pac :: Failed, PAC is likely to be bad or sub optimal, erasing qspi block 0"
        qspi_erase 0
        plog_err "cap_esec_prog_optimal_pac :: Unable to Enroll the chip. Exiting...."
        return -1
    }
    
    #program pac with best score
    cap_program_pac $xx
    plog_msg "cap_esec_prog_optimal_pac :: $xx of ek cache $::CAP_EK_CACHE($xx)"
    
    #capture and store the last pac
    cap_qspi_pwr_up_chk 830 1
        
    # Copy winning CRC32
    eval file copy -force -- /home/diag/diag/tools/pki/crc32_ek_$xx.bin /home/diag/diag/tools/pki/crc32_ek.bin

    # clean up
    set DIAG_HOME $::env(DIAG_HOME)
    if { [catch {eval file delete [glob $DIAG_HOME/diag/tools/pki/crc32_ek_*bin]} msg] } {
        plog_msg "Information about it: $::errorInfo"
    }

    return 0
}

proc esec_all_pac {sn usb_port slot PN MAC MTP
        {CLIENT_KEY "certs/client.key.pem"} 
        {CLIENT_CERT "certs/client-bundle.cert.pem"}
        {TRUST_ROOTS "certs/rootca.cert.pem"}
        {BACKEND_URL "192.168.67.213:12266#192.168.67.214:12266"}
        {pac_cnt 25} } {

    set err [plog_get_err_count]
    set timestamp_pre [clock seconds]

    plog_msg "sn: $sn; slot: $slot"
    plog_start esec_all_${sn}_slot${slot}.log

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25" ||
        $card_type == "NAPLES25SWM" ||
        $card_type == "NAPLES25SWMDELL" ||
        $card_type == "NAPLES25OCP"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
    ssi_cpld_write 0x29 0x80
    cap_set_esec_enable_pin

    set ret [esec_prog_optimal_pac $sn $usb_port $slot $PN $MAC $MTP $CLIENT_KEY $CLIENT_CERT $TRUST_ROOTS $BACKEND_URL $pac_cnt]

    if { $ret == 0 } {
        plog_msg "ESEC Optimal PAC passed"
    } else {
        plog_msg "ESEC Optimal PAC failed"
        return -1
    }

    set timestamp_post [clock seconds]

    #============================
    # Boot Test
    set ret [cap_secure_post_check 10 10 $slot]

    if { $ret == 0 } {
        plog_msg "ESEC boot test passed"
    } else {
        plog_err "ESEC boot test failed"
        return -1
    }

    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
    cap_dump_qspi csp 0x70000000 0x10000 csp_${sn}_${cur_time}.txt 0
    plog_msg "CSP recorded"

    set timestamp_final [clock seconds]

    set time_key_prog [expr {$timestamp_post - $timestamp_pre}]
    set time_boot_test [expr {$timestamp_final - $timestamp_post}]
    
    plog_msg "Key Prog Time: $time_key_prog"
    plog_msg "Boot Test Time: $time_boot_test"

    diag_close_j2c_if 10 $slot
    plog_stop

    set err1 [plog_get_err_count]
    if {$err != $err1} {
        set return -1
    }

    return $ret
}

proc esec_all {sn usb_port slot PN MAC MTP
        {CLIENT_KEY "certs/client.key.pem"} 
        {CLIENT_CERT "certs/client-bundle.cert.pem"}
        {TRUST_ROOTS "certs/rootca.cert.pem"}
        {BACKEND_URL "192.168.67.213:12266#192.168.67.214:12266"}
        {pac_cnt 25} } {

    set pub_ek_fn "pub_ek.tcl.txt"
    set SN $sn

    plog_msg "sn: $sn; slot: $slot"
    plog_start esec_all_${sn}_slot${slot}.log

    diag_open_j2c_if 10 $slot
    regrd 0 0x6a000000
    set card_type [cap_get_card_type]
    if {$card_type == "NAPLES25" ||
        $card_type == "NAPLES25SWM" ||
        $card_type == "NAPLES25SWMDELL" ||
        $card_type == "NAPLES25OCP"} {
        set freq 417
    } else {
        set freq 833
    }
    cap_jtag_chip_rst 10 $slot 0 "" 1 1 0 $freq 2200
    ssi_cpld_write 0x29 0x80
    cap_set_esec_enable_pin
    cap_power_cycle_chk 25 10 $slot
    
    set timestamp_pre [clock seconds]
    #============================
    # PUF enroll
    set err_cnt [cap_get_err_cnt cap_chlng_enroll_puf_str]

    set pub_ek [cap_chlng_read_pub_ek_str]
    set fp [open $pub_ek_fn w]
    puts -nonewline $fp $pub_ek
    close $fp
    plog_msg "Enroll PUF done"

    #============================
    # Signing PUB EK
    set tcl_pwd [pwd]
    set DIAG_HOME $::env(DIAG_HOME)
    cd $DIAG_HOME/diag/tools/pki
    #exec cp $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt .

    if { [catch {exec /home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn $SN -pn "$PN" -mac $MAC -brd_name $card_type -mtp MTP -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL} msg ]} {
        plog_msg "Information about it: $::errorInfo"
    }
    
    if { [catch { exec crc32 ./signed_ek.pub.bin | tee crc32_ek.bin} msg] } {
        plog_msg "Information about it: $::errorInfo"
        return -1
    } else {
        set crc32Val $msg
        plog_msg "CRC32: $crc32Val"
    }

    cd $tcl_pwd
    plog_msg "Signing EK passed"

    #============================
    # Check EK
    if { [catch { exec /home/diag/diag/python/esec/scripts/esec_prog.sh -ek_check } msg] } {
        plog_msg "Information about it: $::errorInfo"
        return -1
    } else {
        plog_msg $msg
        # Check if EK is good
        if {[string first "Signature Algorithm: ecdsa-with-SHA384" $msg] != -1} {
            plog_msg "EK Check Passed"
        } else {
            plog_msg "EK Check Failed"
            return -1
        }
    }
    
    #============================
    # Gen OTP
    if { [catch { exec /home/diag/diag/python/esec/scripts/esec_prog.sh -gen_otp } msg] } {
        plog_msg "Information about it: $::errorInfo"
        return -1
    } else {
        plog_msg $msg
    }

    #============================
    # OTP init
    set cm_file "./images/OTP_cm.hex"
    set sm_file "./images/OTP_sm.hex"
    set cmd_cm [list cap_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    set cmd_sm [list cap_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

    set err_cnt_cm [cap_get_err_cnt $cmd_cm]
    set err_cnt_sm [cap_get_err_cnt $cmd_sm]

    set err_cnt [expr {$err_cnt_cm + $err_cnt_sm}]

    if { $err_cnt == 0 } {
        plog_msg "OTP Init Passed"
    } else {
        plog_msg "OTP Init Failed"
        return -1
    }
    set timestamp_post [clock seconds]

    # clean up
    set DIAG_HOME $::env(DIAG_HOME)
    eval file delete [glob $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt]
    eval file delete [glob $DIAG_HOME/diag/tools/pki/pub_ek.tcl.txt]
    eval file delete [glob $DIAG_HOME/diag/tools/pki/signed_ek.pub*bin]

    if { [catch {eval file delete [glob $DIAG_HOME/diag/tools/pki/crc32_ek_*bin]} msg] } {
        plog_msg "Information about it: $::errorInfo"
    }

    #============================
    # Boot Test
    set ret [cap_secure_post_check 10 10 $slot]

    if { $ret == 0 } {
        plog_msg "ESEC boot test passed"
    } else {
        plog_err "ESEC boot test failed"
        return -1
    }

    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    cap_dump_qspi csp 0x70000000 0x10000 csp_${sn}_${cur_time}.txt 0
    plog_msg "CSP recorded"

    set timestamp_final [clock seconds]

    set time_key_prog [expr {$timestamp_post - $timestamp_pre}]
    set time_boot_test [expr {$timestamp_final - $timestamp_post}]
    
    plog_msg "Key Prog Time: $time_key_prog"
    plog_msg "Boot Test Time: $time_boot_test"

    diag_close_j2c_if 10 $slot
    plog_stop

    return $ret
}


if { $use_zmq == 1 } {
    set ::SSI_OPERATION_TIMEOUT_S 10
    diag_zmq_lock_release $zmq_conn $slot
    p
    iag_force_close_zmq_if $zmq_conn $slot

    #diag_open_zmq_if $zmq_conn $slot
} else {
    diag_close_j2c_if 10 $slot
}

set stage [string toupper $stage]
plog_msg "stage: $stage"
switch $stage {
    "PUF_ENROLL" {
        set ret [puf_enroll $sn $slot $fn]
    }
    "READ_PUB_EK" {
        set ret [read_pub_ek $sn $slot $fn]
    }
    "OTP_INIT" {
        set ret [otp_init $sn $slot $cm_file $sm_file]
    }
    "IMG_PROG" {
        set ret [img_prog $slot $fw_ptr $esec_1 $esec_2 $host_1 $host_2]
    }
    "EFUSE_TEST" {
        set ret [efuse_test $slot]
    }
    "POST_CHECK" {
        set ret [post_check $sn $slot]
    }
    "SHOW_STS" {
        set ret [show_status $sn $slot]
    }
    "ESEC_ALL" {
        set ret [esec_all $sn 10 $slot $pn $mac $mtp $client_key $client_cert $trust_roots $backend_url]
    }
    "ESEC_ALL_PAC" {
        set ret [esec_all_pac $sn 10 $slot $pn $mac $mtp $client_key $client_cert $trust_roots $backend_url]
    }
    default {
        plog_msg "Invalide stage: $stage"
        set return -1
    }
}

if { $use_zmq == 1 } {
    diag_zmq_lock_release $zmq_conn $slot
    diag_force_close_zmq_if $zmq_conn $slot
} else {
    diag_close_j2c_if 10 $slot
}

# Print twice for DSP to capture signature
if {$ret == 0} {
    plog_msg "ESEC PROG PASSED"
    plog_msg "ESEC PROG PASSED"
} else {
    plog_msg "ESEC PROG FAILED"
    plog_msg "ESEC PROG FAILED"
}

