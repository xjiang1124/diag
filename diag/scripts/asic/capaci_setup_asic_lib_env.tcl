# !/usr/bin/tclsh
#
#package require cmdline
#
source ./cmdline.tcl
set parameters {
    {slot.arg       ""              "Slot number"}
    {diag_dir.arg   "/fs/nos/diag/" "Diag home directory"}
    {jtag_speed.arg 74              "Jtag speed Divider"}
}

array set arg [cmdline::getoptions argv $parameters]
set slot        $arg(slot)
set DIAG_DIR    $arg(diag_dir)
set JTAG_SPEED  $arg(jtag_speed)



#source asic_tests.tcl

puts "slot: $slot"


set ASIC_LIB_BUNDLE "$DIAG_DIR/nic"
set ASIC_SRC "$ASIC_LIB_BUNDLE/asic_src"
set ASIC_LIB "$ASIC_LIB_BUNDLE/asic_lib"
set ASIC_GEN "$ASIC_SRC"

if { $slot >6 || $slot<1} {
    puts "ERROR: Slot number must be 1-6"
    return -1
}


### SETUP J2C ###################################
#######        SET RESET MASK        ############
#######        RESET J2C.            ############
#######        SET J2C MUX TO INTERNAL ##########
#######        SET J2C SPEED TO 500KHZ ##########
#################################################
#export $slot=1
#./jtag_accpcie spiwrite $slot 0x3c0 0x990000
#./jtag_accpcie spiread $slot 0x3c0
#./jtag_accpcie wg $slot 0x24 0xD
#./jtag_accpcie rg $slot 0x24 
#./jtag_accpcie wg $slot 0x20 0x4A
#./jtag_accpcie rg $slot 0x20
#./jtag_accpcie wg $slot 0x28 0x1
#./jtag_accpcie rg $slot 0x28 
#################################################
if {[catch {exec $DIAG_DIR/jtag_accpcie spiwrite $slot 0x3c0 0x990000} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie spiread $slot 0x3c0} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x24 0xD} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
} 
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x24} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x20 $JTAG_SPEED} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x20} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie wg $slot 0x28 0x1} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x28} result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
if {[catch {exec $DIAG_DIR/jtag_accpcie rg $slot 0x20 | grep "DATA READ" | awk {{print $4}} } result] == 0} { 
    puts "$result"
} else { 
    puts "$result\nCOMMAND FAILED"
    exit -1
}
set j2cspeed [expr $result]
puts "Read J2C Divider for Clock Speed -> $j2cspeed"
if {$j2cspeed != [expr $JTAG_SPEED]} {
    puts "J2C CLOCK DIVIDER LOOKS INCORRECT FROM REGISTER 0x20 IN THE J2C MAILBOX"
    puts "READ $j2cspeed.   EXPECT $JTAG_SPEED"
    exit -1
}

cd $ASIC_SRC/ip/cosim/tclsh

puts ""
puts "---------------------------------------------------------------------- "
puts "TO START THE ASIC LIBRARY FROM HERE, EXECUTE THE FOLLOWING STEPS BELOW."
puts "CHECK THAT _msrd READS BACK 1.  IF IT DOES NOT J2C IS NOT WORKING."
puts "---------------------------------------------------------------------- "
puts ""
puts "cd $ASIC_SRC/ip/cosim/tclsh"
puts "tclsh"
puts "source .tclrc.diag.elb"

puts "set port $slot"
puts "diag_open_j2c_if \$port 0x10"
puts "_msrd"
puts ""





