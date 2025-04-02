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
    {pentrust_1.arg  ""              "Pentrust image 1"}
    {pentrust_2.arg  ""              "Pentrust image 2"}
    {non_esec_1.arg  ""              "non esec image 1"}
    {non_esec_2.arg  ""              "non esec image 2"}
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
set pentrust_1  $options(pentrust_1)
set pentrust_2  $options(pentrust_2)
set non_esec_1  $options(non_esec_1)
set non_esec_2  $options(non_esec_2)
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
    reset_to_proto_mode cold 

    sal_print_voltage_temp_from_j2c

    plog_msg "erase fw_ptr"
    qspi_erase_range 0x78010000 0x10000
    #set ret [sal_prog_qspi $fw_ptr 0x78010000]
    #if {$ret != 0} {
    #    plog_msg "Failed to program fw_ptr"
    #    diag_close_j2c_if $port $slot
    #    return $ret
    #}
    plog_msg $esec_1
    set ret [sal_prog_qspi $esec_1 0x78020000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_1"
        diag_close_j2c_if $port $slot
        return $ret
    }
    plog_msg $esec_2
    set ret [sal_prog_qspi $esec_2 0x78030000]
    if {$ret != 0} {
        plog_msg "Failed to program esec_2"
        diag_close_j2c_if $port $slot
        return $ret
    }
    plog_msg "erase pentrust_1"
    qspi_erase_range 0x78040000 0x20000

    plog_msg "erase pentrust_2"
    qspi_erase_range 0x78060000 0x20000

    plog_msg "erase non_esec_1"
    qspi_erase_range 0x78080000 0x20000

    plog_msg "erase non_esec_2"
    qspi_erase_range 0x780A0000 0x20000

    plog_stop
    diag_close_j2c_if $port $slot
    return $ret
}

proc dice_img_prog {slot fw_ptr pentrust_1 pentrust_2 non_esec_1 non_esec_2} {
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
    reset_to_proto_mode cold
    sal_print_voltage_temp_from_j2c

    plog_msg $fw_ptr
    set ret [sal_prog_qspi $fw_ptr 0x78010000]
    if {$ret != 0} {
        plog_msg "Failed to program fw_ptr"
        diag_close_j2c_if $port $slot
        return $ret
    }
    plog_msg $pentrust_1
    set ret [sal_prog_qspi $pentrust_1 0x78040000]
    if {$ret != 0} {
        plog_msg "Failed to program pentrust_1"
        return $ret
    }
    plog_msg $pentrust_2
    set ret [sal_prog_qspi $pentrust_2 0x78060000]
    if {$ret != 0} {
        plog_msg "Failed to program pentrust_2"
        return $ret
    }
    plog_msg $non_esec_1
    set ret [sal_prog_qspi $non_esec_1 0x78080000]
    if {$ret != 0} {
        plog_msg "Failed to program non_esec_1"
        return $ret
    }
    plog_msg $non_esec_2
    set ret [sal_prog_qspi $non_esec_2 0x780A0000]
    if {$ret != 0} {
        plog_msg "Failed to program non_esec_2"
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

proc get_entropy_from_hsm {sn
        {CLIENT_KEY "/home/diag/diag/tools/pki/dice_certs/client.key.pem"}
        {CLIENT_CERT "/home/diag/diag/tools/pki/dice_certs/client.crt.pem"}
        {TRUST_ROOTS "/home/diag/diag/tools/pki/dice_certs/rootca.crt"}
        {BACKEND_URL "192.168.67.214:12266"} } {

    if { [catch {exec /home/diag/diag/tools/pki/client_dice.py -k $CLIENT_KEY -c $CLIENT_CERT -t $TRUST_ROOTS -b $BACKEND_URL -sn $sn -n 64 -hsm_rn} msg ]} {
        puts "failed to get entropy from hsm $msg"
        return -1
    }

    set rand_file "/home/diag/diag/asic/asic_src/ip/cosim/tclsh/entropy_$sn.txt"
    set fp [open $rand_file r]
    set input [read $fp]
 
    set str_start 0
    set str_end 7
    set len [string length $input]

    for { set i 0 } { $str_start < $len } { incr i } {
        lappend list_result [ string range $input $str_start $str_end ]
        incr str_start 8
        incr str_end 8
    }
    return $list_result
}

proc esec_set_uds_entropy {sn 
        {CLIENT_KEY "/home/diag/diag/tools/pki/dice_certs/client.key.pem"}
        {CLIENT_CERT "/home/diag/diag/tools/pki/dice_certs/client.crt.pem"}
        {TRUST_ROOTS "/home/diag/diag/tools/pki/dice_certs/rootca.crt"}
        {BACKEND_URL "192.168.67.214:12266"} } {

    # Check if efuse[51:50] is already set
    set bit50 [sal_fuse_get_bit 0 50 0]
    set bit51 [sal_fuse_get_bit 0 51 0]
    if { $bit50 != 0 || $bit51 != 0 } {
        plog_msg "UDS entropy already been programmed, exit here"
        plog_msg "SET UDS ENTROPY SUCCESSFUL"
        sal_fuse_dump
        return 0
    } else {
        set entropy_sum 0
        for {set i 0} {$i < 16} {incr i} {
            set idx [expr $i + 32]
            set fuse_val [sal_fuse_get_line 0 $idx 0]
            set entropy($i) [expr $fuse_val]
            set entropy_sum [expr {$fuse_val | $entropy_sum}]
        }
        if { $entropy_sum != 0 } {
            plog_msg "SET UDS ENTROPY SUCCESSFUL"
            sal_fuse_dump
            return 0
        }
    }

    plog_msg "fuse entropy is not programmed"
    set entropy_list [get_entropy_from_hsm $sn]
    if { $entropy_list == -1 } {
        return -1
    }
    set i 0
    foreach n $entropy_list {
        set entropy($i) "0x$n"
        incr i 1
    }

    sal_fuse_vddq_enable
    set idx 32
    for {set i 0} {$i < 16} {incr i} {
        plog_msg "set fuse line $idx with value $entropy($i)"
        sal_fuse_set_line 0 $idx $entropy($i)
        incr idx 1
    }
    sal_fuse_set_bit 0 50 0
    sal_fuse_set_bit 0 51 0
    sal_fuse_set_bit 0 48 0
    sal_fuse_set_bit 0 49 0
    sal_fuse_vddq_disable

    set ret_code 0
    for {set i 0} {$i < 16} {incr i} {
        set idx [expr $i + 32]
        set fuse_val [sal_fuse_get_line 0 $idx 0]
        if { "$entropy($i)" != "$fuse_val" } {
            plog_msg "ERROR: ENTROPY VALUE INCORRECT Line: $idx expected: $entropy($i) read: $fuse_val"
            set ret_code [expr $ret_code + 1]
        }
    }

    set ret_code 0
    set bit50 [sal_fuse_get_bit 0 50 0]
    set bit51 [sal_fuse_get_bit 0 51 0]
    if { $bit50 == 0 || $bit51 == 0 } {
        plog_msg "set UDS entropy Auto-Clear FAILED"
        set ret_code [expr $ret_code + 1]
    }
    set bit48 [sal_fuse_get_bit 0 48 0]
    set bit49 [sal_fuse_get_bit 0 49 0]
    if { $bit48 == 0 || $bit49 == 0 } {
        plog_msg "set UDS entropy read disable FAILED"
        set ret_code [expr $ret_code + 1]
    }
    sal_fuse_dump

    if { $ret_code == 0 } {
        plog_msg "SET UDS ENTROPY SUCCESSFUL"
    } else {
        plog_msg "SET UDS ENTROPY FAILED. error code $ret_code"
    }
    return $ret_code
}

proc esec_get_uds_csr { } {
    sal_chlng_wr 0 0 8
    sal_chlng_wr 0 0 0xFF060000

    set val [sal_chlng_rd 0 0]
    set len [expr $val & 0xFFFF]
    set len [expr $len - 4]
    set ret_code [expr $val  >> 16]
    set ret_code [expr $ret_code  & 0x0000FFFF]
    if { $ret_code == 0 } {
       plog_msg "\nUDS csr (of length $len bytes) retreival successful"
    } else {
       puts "\nUDS csr retreival failed. error code $ret_code"
       exit
    }

    set extra [expr $len % 4]
    set s ""
    for {set i 0} {$i < $len/4} {incr i} {
        set val [sal_chlng_rd 0 0]
        set a [expr $val & 0xFF]
        append  s  [format %02x $a]
        set  a  [format %2x $a]
        set b [expr {$val >> 8} & 0xFF]
        append  s  [format %02x $b]
        set c [expr {$val >> 16} & 0xFF]
        append  s  [format %02x $c]
        set d [expr {$val >> 24} & 0xFF]
        append  s  [format %02x $d]
    }

    if {$extra == 1} {
        set val [sal_chlng_rd 0 0]
        set a [expr $val & 0xFF]
        append  s  [format %02x $a]
    } elseif {$extra == 2} {
        set val [sal_chlng_rd 0 0]
        set a [expr $val & 0xFF]
        append  s  [format %02x $a]
        set b [expr {$val >> 8} & 0xFF]
        append  s  [format %02x $b]
    } elseif {$extra == 3} {
        set val [sal_chlng_rd 0 0]
        set a [expr $val & 0xFF]
        append  s  [format %02x $a]
        set b [expr {$val >> 8} & 0xFF]
        append  s  [format %02x $b]
        set c [expr {$val >> 16} & 0xFF]
        append  s  [format %02x $c]
    }
    set fpb_tn "./uds_csr_hex.csr"
    set fpb    "./uds_csr_der.csr"
    set fpb_t [open $fpb_tn w]
    puts -nonewline $fpb_t $s
    close $fpb_t
    #exec xxd -r -p $fpb_tn $fpb
    exec hex2bin $fpb_tn $fpb
    #exec rm $fpb_tn

    set DIAG_HOME $::env(DIAG_HOME)

    puts "\nDER Hex dump:"
    puts $s
    puts "\nUDS csr file created : $fpb\n"
    puts [exec  openssl req -inform DER -in $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/$fpb -noout -text]

    return 0
}

proc esec_set_uds_cert {sn
    {CLIENT_KEY "/home/diag/diag/tools/pki/dice_certs/client.key.pem"}
    {CLIENT_CERT "/home/diag/diag/tools/pki/dice_certs/client.crt.pem"}
    {TRUST_ROOTS "/home/diag/diag/tools/pki/dice_certs/rootca.crt"}
    {BACKEND_URL "192.168.67.214:12266"} } {

    set DIAG_HOME $::env(DIAG_HOME)
 
    if { [catch {exec /home/diag/diag/tools/pki/client_dice.py -k $CLIENT_KEY -c $CLIENT_CERT -t $TRUST_ROOTS -b $BACKEND_URL -sn $sn -s "$DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/"} msg ]} {
        puts "failed to get entropy from hsm $msg"
        return -1
    }

    set fn "$DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_der.crt" 
    #set fn "$DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_der.csr" 
    set fs [file size $fn]

    set tempfn "$DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/uds_csr_der.crt.tmp"
    puts "Reading UDS certificate DER data (length $fs bytes) from $fn"
    exec xxd -c 4 -p $fn $tempfn
    set fp [open $tempfn "r"]

    sal_chlng_wr 0 0 12
    sal_chlng_wr 0 0 0xFF070000
    sal_chlng_wr 0 0 $fs

    while { [gets $fp data] >= 0 } {
        set val [scan $data %x]
        if { $fs >=4 } {
            set a [expr $val & 0xFF]
            set  s  [format %02x $a]
            set b [expr {$val >> 8} & 0xFF]
            append  s  [format %02x $b]
            set c [expr {$val >> 16} & 0xFF]
            append  s  [format %02x $c]
            set d [expr {$val >> 24} & 0xFF]
            append  s  [format %02x $d]
        } elseif { $fs >=3 } {
            set a [expr $val & 0xFF]
            set  s  [format %02x $a]
            set b [expr {$val >> 8} & 0xFF]
            append  s  [format %02x $b]
            set c [expr {$val >> 16} & 0xFF]
            append  s  [format %02x $c]
        } elseif { $fs >=2 } {
            set a [expr $val & 0xFF]
            set  s  [format %02x $a]
            set b [expr {$val >> 8} & 0xFF]
            append  s  [format %02x $b]
        } elseif { $fs >=1 } {
            set a [expr $val & 0xFF]
            set  s  [format %02x $a]
        }
        set f_hex "0x"
        append f_hex $s
        sal_chlng_wr 0 0 $f_hex
        set fs [expr $fs - 4]
    }
    close $fp
    #exec rm $tempfn

    set ret [sal_chlng_rd 0 0]
    set ret_code [expr $ret  >> 16]
    set ret_code [expr $ret_code  & 0x0000FFFF]
    if { $ret_code == 0 } {
        puts "UDS certificate provisioning successful"
    } else {
        puts "UDS certificate provisioning failed. error code $ret_code"
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
    reset_to_proto_mode cold
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

proc esec_dice_all {slot sn 
        {CLIENT_KEY "/home/diag/diag/tools/pki/dice_certs/client.key.pem"}
        {CLIENT_CERT "/home/diag/diag/tools/pki/dice_certs/client.crt.pem"}
        {TRUST_ROOTS "/home/diag/diag/tools/pki/dice_certs/rootca.crt"}
        {BACKEND_URL "192.168.67.214:12266"} } {

    set port $slot

    plog_msg "slot: $slot"
    plog_start esec_dice_all_slot${slot}.log

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
    reset_to_proto_mode cold 
    sal_print_voltage_temp_from_j2c

    ssi_cpld_write 0x20 0x7
    after 1000
    sal_pc
    after 1000
 
    sal_chlng_get_status_str

    set ret [esec_set_uds_entropy $sn $CLIENT_KEY $CLIENT_CERT $TRUST_ROOTS $BACKEND_URL] 
    if { $ret == 0 } {
        plog_msg "set entropy passed"
    } else {
        plog_msg "set entropy failed"
        diag_close_j2c_if $port $slot
        plog_stop
        return -1
    }

    sal_pc
    after 1000

    set ret [esec_get_uds_csr] 
    if { $ret == 0 } {
        plog_msg "GET UDS csr successful"
    } else {
        plog_msg "GET UDS csr failed"
        diag_close_j2c_if $port $slot
        plog_stop
        return -1
    }

    set ret [esec_set_uds_cert $sn] 
    if { $ret == 0 } {
        plog_msg "SET UDS CERTIFICATE successful"
    } else {
        plog_msg "SET UDS CERTIFICATE failed"
        diag_close_j2c_if $port $slot
        plog_stop
        return -1
    }

    diag_close_j2c_if $port $slot
    plog_stop
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
    "DICE_IMG_PROG" {
        set ret [dice_img_prog $slot $fw_ptr $pentrust_1 $pentrust_2 $non_esec_1 $non_esec_2]
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
    "ESEC_DICE_ALL" {
        set ret [esec_dice_all $slot $sn $client_key $client_cert $trust_roots $backend_url]
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

