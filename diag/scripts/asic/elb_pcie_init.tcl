# !/usr/bin/tclsh
#
# package require cmdline

source ./cmdline.tcl
set parameters {
    {slot.arg       ""          "Slot number"}
    {port.arg       "0xa"       "jtag port number"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot        $arg(slot)
set port        $arg(port)

set slot_list [split $slot ""]
puts "slot list $slot_list"

cd /home/diag/diag/asic/asic_src/ip/cosim/tclsh
source .tclrc.diag.elb

foreach slot $$slot_list {
    puts "slot: $slot port $port"
    diag_open_j2c_if $port $slot
    elb_soc_pcie_pll_init 0 0
    elb_soc_i_rom_enable 0 0
    elb_soc_pcie_pll_lock 0 0 -1
    csr_write {elb0.pp.pp[0].cfg_pp_sd_async_reset_n} 0xffff
    csr_write {elb0.pp.pp[1].cfg_pp_sd_async_reset_n} 0xffff
    diag_close_j2c_if $port $slot
}
puts "FINISH SETTING UP PCIE PLL"

