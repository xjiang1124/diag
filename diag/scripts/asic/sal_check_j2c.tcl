# !/usr/bin/tclsh

source /home/diag/diag/scripts/asic/cmdline.tcl

set usage {
    {slot.arg           ""                      "Slot number"}
    {ite.arg            10                      "Number of iteration"}
    {use_j2c.arg        0                       "Whether to use J2C to check; Default is OW"}
    {use_gpio3.arg      0                       "Whether to use GPIO3; Default is no"}
    {use_pwr_ok_rst.arg 0                      "Toggle power ok reset"}
    {stop_on_error.arg  0                       "Stop on error"}
}
# rename argv variables to call them more easily
array set arg [cmdline::getoptions argv $usage]
foreach argname [array names arg] { set $argname $arg($argname) }
if { $slot == "" } { puts "Missing required --slot arg" ; exit }
parray arg

set ASIC_SRC $::env(ASIC_SRC)

cd $ASIC_SRC/ip/cosim/tclsh
source .tclrc.diag.sal

set port $slot
set slot $slot
set ::slot  $slot
set ::port  $port

plog_msg "$env(PATH)"

exec fpgautil spimode $slot off
exec jtag_accpcie_salina clr $slot

for {set i 0} {$i < $ite} {incr i} {

    plog_msg "\n\n\n============================"
    plog_msg "=== TCL Ite $i ==="
    
    set err_cnt_init [ plog_get_err_count ]
    
    after 500
    diag_close_ow_if $port $slot
    after 500
    diag_open_ow_if $port $slot
    after 2000
    sal_ow_axi
    
    set dd 0
    set cnt 0
    while { ($dd==0) && ($cnt<10) } {
        csr_write sal0.ms.ms.cfg_ow 3
        after 500
        set dd [ rd sal0.ms.ms.cfg_ow ]
        incr cnt
    }
    set ret 0
    if { $cnt  >= 10 } {
        plog_err "\n\n==== J2C / OW is not working.... Ping HW team\n\n"
        plog_err "PC_TEST_J2C FAILED"
        set ret 1
    }

#    if { ($ret!=0) && ($stop_on_error!=0) } {
#        exit 0
#    }

    # Check OW APB
    set ow_apb_good 0
    if {$use_j2c == 0} {
        sal_ow
        sal_ow_apb
        set val [regrd 0 0]
        if {$val == 0x006a0003} {
            plog_msg "OW APB is good"
            set ow_apb_good 1
        } else {
            plog_msg "OW APB is bad"
        }
    }

    if {$use_j2c == 1} {
        sal_j2c
        set j2c_secure 1
        plog_msg "J2C mode"
    } else {
        sal_ow
        sal_ow_axi
        plog_msg "OW AXI mode"
    }
 
    set val [regrd 0x0 0x90000]
    plog_msg "regrd 0x0 0x90000: $val"

    regwr 0x0 0x30200000 0x1234
    set val [regrd 0x0 0x30200000]
    plog_msg "regrd 0x0 0x30200000: $val"

    set val [_msrd]
    set ow_axi_good 0
    if { $val != 0x1 } {
        plog_err "OW sanity test failed!"
        plog_err "PC_TEST_J2C FAILED"
        set ret 1
        if {$use_j2c == 0} {
            plog_msg "OW AXI is bad"
            set ow_axi_good 0
        }
    } else {
        plog_msg "OW AXI is good"
        set ow_axi_good 1
    }

    set core_pll_good 1
    if { $ret!=0 } {
        try {
            source ~/xin/jtag_core_clk_obs_pad.tcl
            set core_pll [sal_jtag_core_clk_obs_pad]

            if {$core_pll == 110} {
                set core_pll_good 1
            } else {
                set core_pll_good 0
            }

            plog_msg "core_pll: $core_pll"
        } on error {msg opt} {
            plog_msg "Something wrong"
        } finally {
            plog_msg "JTAG core pll obs done"
        }

        if { $stop_on_error!=0 } {
            break
        }
    }
   
    if {$use_gpio3 == 1} {
        plog_msg "=== GPIO3 Power Cycling ==="
        sal_pcc
    } 
    
    if {$use_pwr_ok_rst == 1} {
        plog_msg "=== CPLD Toggling power ok reset ==="
        set bus [expr {$slot + 2}]
        catch {exec i2cset -y $bus 0x4a 0x1 0x40}
        after 1000
        exec i2cset -y $bus 0x4a 0x1 0x0
    } 

}

# Check PLL failure signature
if { ($ow_apb_good == 1) && ($ow_axi_good == 0) && ($core_pll_good == 0) } {
    plog_err "ASIC PLL failure has happened!"
}


set err_cnt  [ expr ( [plog_get_err_count] - $err_cnt_init ) ]
if {$err_cnt != 0} {
    plog_err "PC_TEST_J2C FAILED"
} else {
    plog_msg "PC_TEST_J2C PASSED"
}

exit 0
