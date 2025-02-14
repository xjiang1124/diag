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
set port        $slot
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

if { $slot == "" } {
    error "Need slot arg"
    exit
}

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal
source /home/diag/diag/scripts/asic/sal_diag_utils.tcl

proc sal_get_err_cnt { proc_to_run } {
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

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd

    set pub_ek [sal_chlng_read_pub_ek_str]
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

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $turbo_slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    sal_arm_reset

    ssi_cpld_write 0x29 0x80
    sal_set_esec_enable_pin
    sal_power_cycle_chk 25 $port $turbo_slot
    
    set err_cnt [sal_get_myerr_cnt sal_chlng_enroll_puf_str 0 1 1]

    set pub_ek [sal_chlng_read_pub_ek_str]
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

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd

    set cmd_cm [list sal_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    set cmd_sm [list sal_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

    set err_cnt_cm [sal_get_myerr_cnt $cmd_cm 0 1 1]
    set err_cnt_sm [sal_get_myerr_cnt $cmd_sm 0 1 1]

    set err_cnt [expr {$err_cnt_cm + $err_cnt_sm}]

    plog_stop
    return $err_cnt
}

proc post_check { sn slot } {
    plog_start post_check_${sn}_slot${slot}.log

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd

    set ret [sal_secure_post_check 10 $port $turbo_slot]
    elb_close_if port $turbo_slot
    plog_stop
    return $ret
}

proc show_status { sn slot } {
    plog_start show_status_${sn}_slot${slot}.log

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    sal_arm_reset

    sal_show_esec_pins
    sal_dump_cpld_sts_spi
    sal_dump_cpld_sts_smb $slot

    sal_close_if $port $turbo_slot
    plog_stop
    return 0
}

proc img_prog {slot fw_ptr esec_1 esec_2 host_1 host_2} {
    plog_start puf_enroll_slot${slot}.log

    set port $slot

    exec fpgautil spimode $slot off
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

    _msrd

    diag_open_j2c_if $port $slot
    puts "_msrd"
    set rtn [eval _msrd]
    puts $rtn

    #sal_arm_reset
    reset_to_proto_mode no_proto

    sal_print_voltage_temp_from_j2c

    set ret [sal_prog_qspi $fw_ptr 0x78010000]
    if {$ret != 0} {
        plog_msg "Failed to program fw_ptr"
        return $ret
    }
    plog_msg $esec_1
    set ret [sal_prog_qspi $esec_1 0x78020000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_1"
        return $ret
    }
    plog_msg $esec_2
    set ret [sal_prog_qspi $esec_2 0x78030000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_2"
        return $ret
    }
    plog_msg $host_1
    set ret [sal_prog_qspi $host_1 0x78040000]
    if {$ret != 0} {
        plog_msg "Failed to program host_1"
        return $ret
    }
    plog_msg $host_2
    set ret [sal_prog_qspi $host_2 0x78060000]
    if {$ret != 0} {
        plog_msg "Failed to program host_2"
        return $ret
    }

    plog_stop
    return $ret
}

proc efuse_prog {slot sn} {
    plog_start efuse_prog_slot${slot}_sn_${sn}.log

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    sal_arm_reset

    set ret [sal_prog_efuse rand_sn_${sn}.txt $port $turbo_slot]

    plog_stop
    return $ret
}

proc efuse_test {slot} {
    set ret 0
    set bit_loc 127

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    
    #Set to 417 for now.  With CPLD's where EFUSE VDDQ can be disabled/enabled.  On a SWM it will not set an efuse bit at 833Mhz if we enable EFUSE VDDQ after asic reset
    #set freq 417

    set cpld_rev [ssi_cpld_read 0x00]
    set cpld_ver [ssi_cpld_read 0x80]
    
    sal_arm_reset

    cpu_force_global_flags 1

    sal_efuse_vddq_enable

    set bit_read_back [sal_efuse_get_bit $bit_loc $port $turbo_slot]
    if {$bit_read_back == 1} {
        plog_msg "Efuse bit $bit_loc is already programmed; read back $bit_read_back"
    }

    sal_efuse_set_bit $bit_loc $port $turbo_slot
    set bit_read_back [sal_efuse_get_bit $bit_loc $port $turbo_slot]
    if {$bit_read_back != 1} {
        plog_err "Failed to valid efuse bit; read back $bit_read_back"
        set return -1
    }

    sal_efuse_vddq_disable

    diag_close_j2c_if $slot $slot

    return $ret
}

proc esec_gather_pac {sn usb_port slot PN MAC MTP
        {CLIENT_KEY "certs/client.key.pem"} 
        {CLIENT_CERT "certs/client-bundle.cert.pem"}
        {TRUST_ROOTS "certs/rootca.cert.pem"}
        {BACKEND_URL "192.168.67.213:12266#192.168.67.214:12266"}
        {pac_cnt 25} } {

    unset -nocomplain ::CAP_EK_CACHE

    set card_type [sal_get_card_type]
    set pub_ek_fn "pub_ek.tcl.txt"
    set SN $sn

    for {set j 0} {$j < $pac_cnt} {incr j 1} {
        set timestamp_pre [clock seconds]
        set tt [ clock format [clock seconds] -format "%m_%d_%Y_%T" ]
        plog_msg ""
        plog_msg "esec_gather_pac : Iter:$j Begin:: Date:$tt"
        plog_msg ""

        sal_power_cycle_chk 25 $usb_port $slot
        qspi_erase 0
        
        #============================
        # PUF enroll
        set err_cnt [sal_get_err_cnt sal_chlng_enroll_puf_str]

        set pub_ek [sal_chlng_read_pub_ek_str]
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

        if { [catch {exec /home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn $SN -pn "$PN" -mac $MAC -card_type $card_type -mtp MTP -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL} msg ]} {
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
        set cmd_cm [list sal_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
        set cmd_sm [list sal_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

        set err_cnt_cm [sal_get_err_cnt $cmd_cm]
        set err_cnt_sm [sal_get_err_cnt $cmd_sm]

        sal_populate_pac_cache $j [expr ($j==0)] 0

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
    sal_mem_pwr_up_cache_clear

    esec_gather_pac $sn $usb_port $slot $PN $MAC $MTP $CLIENT_KEY $CLIENT_CERT $TRUST_ROOTS $BACKEND_URL $pac_cnt
    
    #dump pac
    sal_dump_pac_cache
    
    #find the optimal pac
    sal_eval_pac_score_all
    
    #find pac with highest score
    set xx [ sal_get_best_pac_score ]
    if { $xx == -1 } {
        plog_err "elb_esec_prog_optimal_pac :: Failed, PAC is likely to be bad or sub optimal, erasing qspi block 0"
        qspi_erase 0
        plog_err "elb_esec_prog_optimal_pac :: Unable to Enroll the chip. Exiting...."
        return -1
    }
    
    #program pac with best score
    sal_program_pac $xx
    plog_msg "elb_esec_prog_optimal_pac :: $xx of ek cache $::CAP_EK_CACHE($xx)"
    
    #capture and store the last pac
    sal_qspi_pwr_up_chk 830 1
        
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

    set port [mtp_get_j2c_port $slot]
    set turbo_slot [mtp_get_j2c_slot $slot]

    diag_open_j2c_if $port $turbo_slot
    _msrd
    sal_arm_reset
    ssi_cpld_write 0x29 0x80
    sal_set_esec_enable_pin

    set ret [esec_prog_optimal_pac $sn $usb_port $turbo_slot $PN $MAC $MTP $CLIENT_KEY $CLIENT_CERT $TRUST_ROOTS $BACKEND_URL $pac_cnt]

    if { $ret == 0 } {
        plog_msg "ESEC Optimal PAC passed"
    } else {
        plog_msg "ESEC Optimal PAC failed"
        return -1
    }

    set timestamp_post [clock seconds]

    #============================
    # Boot Test
    set ret [sal_secure_post_check 10 $port $turbo_slot]

    if { $ret == 0 } {
        plog_msg "ESEC boot test passed"
    } else {
        plog_err "ESEC boot test failed"
        return -1
    }

    set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    sal_arm_reset
    sal_dump_qspi csp 0x70000000 0x10000 csp_${sn}_${cur_time}.txt 0
    plog_msg "CSP recorded"

    set timestamp_final [clock seconds]

    set time_key_prog [expr {$timestamp_post - $timestamp_pre}]
    set time_boot_test [expr {$timestamp_final - $timestamp_post}]
    
    plog_msg "Key Prog Time: $time_key_prog"
    plog_msg "Boot Test Time: $time_boot_test"

    diag_close_j2c_if $port $turbo_slot
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
    set port $slot

    plog_msg "sn: $sn; slot: $slot; port: $port"
    plog_start esec_all_${sn}_slot${slot}.log

    exec fpgautil spimode $slot off
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

    _msrd

    diag_open_j2c_if $port $slot
    puts "_msrd"
    set rtn [eval _msrd]
    puts $rtn

    #sal_arm_reset
    reset_to_proto_mode no_proto

    sal_print_voltage_temp_from_j2c

    set card_type [sal_get_card_type]
    ssi_cpld_write 0x29 0x80
    sal_set_esec_enable_pin
    sal_power_cycle_chk 25 $port $slot
    
    set timestamp_pre [clock seconds]
    #============================
    # PUF enroll
    set err_cnt [sal_get_err_cnt sal_chlng_enroll_puf_str]

    set pub_ek [sal_chlng_read_pub_ek_str]
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

    if { [catch {exec /home/diag/diag/python/esec/scripts/esec_prog.sh -sign_ek -sn $SN -pn "$PN" -mac $MAC -card_type $card_type -mtp MTP -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL} msg ]} {
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
    #set cmd_cm [list sal_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    #set cmd_sm [list sal_chlng_init_otpf_str 0 0 1 0 70  $sm_file]
    set cmd_cm [list sal_chlng_init_otpf_str 0 0 0 0 439 $cm_file]
    set cmd_sm [list sal_chlng_init_otpf_str 0 0 1 0 70  $sm_file]

    set err_cnt_cm [sal_get_err_cnt $cmd_cm]
    set err_cnt_sm [sal_get_err_cnt $cmd_sm]

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

    if { [catch {eval file delete [glob $DIAG_HOME/diag/tools/pki/crc32_ek_*.bin]} msg] } {
        plog_msg "Information about it: $::errorInfo"
    }

    #============================
    # Boot Test
    ##set ret [sal_secure_post_check 10 $port $turbo_slot]

    ##if { $ret == 0 } {
    ##    plog_msg "ESEC boot test passed"
    ##} else {
    ##    plog_err "ESEC boot test failed"
    ##    return -1
    ##}

    ##sal_arm_reset

    ##set cur_time [clock format [clock seconds] -format %m%d%y_%H%M%S]
    ##sal_dump_qspi csp 0x70000000 0x10000 csp_${sn}_${cur_time}.txt 0
    ##plog_msg "CSP recorded"

    ##set timestamp_final [clock seconds]

    ##set time_key_prog [expr {$timestamp_post - $timestamp_pre}]
    ##set time_boot_test [expr {$timestamp_final - $timestamp_post}]
    
    ##plog_msg "Key Prog Time: $time_key_prog"
    ##plog_msg "Boot Test Time: $time_boot_test"

    diag_close_j2c_if $port $slot
    plog_stop

    ##return $ret
    return 0
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
        set ret [esec_all $sn $slot $slot $pn $mac $mtp $client_key $client_cert $trust_roots $backend_url]
    }
    "ESEC_ALL_PAC" {
        set ret [esec_all_pac $sn $slot $slot $pn $mac $mtp $client_key $client_cert $trust_roots $backend_url]
    }
    "EFUSE_PROG" {
        set ret [efuse_prot $slot $sn]
    }
    default {
        plog_msg "Invalide stage: $stage"
        set return -1
    }
}

mtp_close_j2c_if $slot

# Print twice for DSP to capture signature
if {$ret == 0} {
    plog_msg "ESEC PROG PASSED"
    plog_msg "ESEC PROG PASSED"
} else {
    plog_msg "ESEC PROG FAILED"
    plog_msg "ESEC PROG FAILED"
}

