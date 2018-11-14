// This script implements procedures for the ssi.
// Byte addressing is utilized.

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include "cpu.h"
#include "cpu_bus_arm.h"

typedef unsigned int uint32_t;
//typedef unsigned long long uint64_t;

#define SSI_BASE  		0x2800
#define SSI_STRIDE 		0x400

#define SSI_CTRLR0		0x00
#define SSI_CTRLR1		0x04
#define SSI_SSIENR		0x08
#define SSI_SER			0x10
#define SSI_BAUDR		0x14
#define SSI_RXFLR		0x24
#define SSI_SR			0x28
#define SSI_DR			0x60

#define SSI_SR_BUSY		0x1
#define SSI_SR_RFNE		0x8

#define SSI_OPERATION_TIMEOUT_S	40
#define ssi_t_start 0

#define GPIO_BASE  0x4000

#define GPIO_SWPORTA_DR  (GPIO_BASE + 0x0)
#define GPIO_SWPORTA_DDR (GPIO_BASE + 0x4)
#define GPIO_SWPORTA_CTL (GPIO_BASE + 0x8)
#define GPIO_SWPORTB_DR  (GPIO_BASE + 0xc)
#define GPIO_SWPORTB_DDR (GPIO_BASE + 0x10)
#define GPIO_SWPORTB_CTL (GPIO_BASE + 0x14)
#define GPIO_EXT_PORTA   (GPIO_BASE + 0x50)
#define GPIO_EXT_PORTB   (GPIO_BASE + 0x54)

extern void csr_write_addr(unsigned long long addr, uint32_t data, uint32_t flags);
extern uint32_t csr_read_addr(unsigned long long addr, uint32_t flags);
extern void cpu_set_cur_if_name(char * _name);

//char inf_name[] = "pcie";
//int init_flag = 0;
//void init_if() {
//	if(!init_flag) {
//		cpu_set_cur_if_name(inf_name);
//		printf("set interface\n");
//		init_flag = 1;
//	}
//}

void regwr(unsigned int addrh, unsigned int addrl, unsigned char data) {
//    global j2c_secure
//    set secure 0
//    if { $j2c_secure != 2 } { set secure 1 }
//	init_if();
	printf("regwr addr 0x%x, data 0x%x\n", addrl, data);
	csr_write_addr((unsigned long long)addrl, (uint32_t)data, (uint32_t)2);
}

unsigned char regrd(unsigned int addrh, unsigned int addrl) {
//    global j2c_secure
//  set data [csr_read_addr [expr ($addrh << 32) + $addrl] $j2c_secure]
//  set data_hex [format %08x $data]
//	init_if();
	printf("regrd addr 0x%x\n", addrl);
	return(unsigned char)(csr_read_addr((unsigned long long)addrl, (uint32_t)2));
}


unsigned int gpio_ddr(int i) {
  if(i < 8) {
    return GPIO_SWPORTA_DDR;
  } else {
    return GPIO_SWPORTB_DDR;
  }
}

unsigned int gpio_ctl(int i) {
  if(i < 8) {
    return GPIO_SWPORTA_CTL;
  } else {
    return GPIO_SWPORTB_CTL;
  }
}

unsigned int gpio_ext(int i) {
  if(i < 8) {
    return GPIO_EXT_PORTA;
  } else {
    return GPIO_EXT_PORTB;
  }
}

unsigned char gpio_get(int i) {
	unsigned char data;
	unsigned int ext_reg, ext;
//	ddr_reg = gpio_ddr(i);
//	data = regrd(0, ddr_reg);
//	ddr = (data >> (i & 0x7)) & 0x1;
	ext_reg = gpio_ext(i);
	data = regrd(0, ext_reg);
	ext = (data >> (i & 0x7)) & 0x1;
//    printf("gpio %d, dir %s, value %d\n", i, (ddr)?"in":"out", ext);
    return ext;
}

unsigned char gpio_get_byte() {
	unsigned char data = 0, tmp;
	for(int i = 6; i < 14; i++)
	{
		tmp = gpio_get(i);
		data |= tmp << (i - 6);
	}
	return data;
}

void ssi_writereg (unsigned char dev, unsigned char reg, unsigned char val) {
//  global SSI_BASE SSI_STRIDE
//  # puts [format "WR: %d:%02x <= %08x" $dev $reg $val]
	printf("ssi_writereg reg 0x%x, val 0x%x\n", reg, val);
  regwr(0, (SSI_BASE + (dev * SSI_STRIDE) + reg), val);
}

//proc ssi_writereg { dev reg val } {
//  global SSI_BASE SSI_STRIDE
//  # puts [format "WR: %d:%02x <= %08x" $dev $reg $val]
//  regwr 0 [expr $SSI_BASE + ($dev * $SSI_STRIDE) + $reg] $val
//}

unsigned char ssi_readreg(unsigned char dev, unsigned char reg) {
  return regrd(0, SSI_BASE + (dev * SSI_STRIDE) + reg);
//  # puts [format "RD: %d:%02x => %08x" $dev $reg $val]
}

//proc ssi_readreg { dev reg } {
//  global SSI_BASE SSI_STRIDE
//  set val [regrd 0 [expr $SSI_BASE + ($dev * $SSI_STRIDE) + $reg]]
//  # puts [format "RD: %d:%02x => %08x" $dev $reg $val]
//  return $val
//}

// Initialize the SPI controller for a transaction
void ssi_init(unsigned char dev, unsigned char scpol, unsigned char scph, unsigned char tmod, unsigned char rxlen) {
  // Set transaction start time
//  upvar #0 ssi_t_start t_start
//  set t_start [clock seconds]

  // Disable master and output-enable
  ssi_writereg(dev, SSI_SSIENR, 0);
  ssi_writereg(dev, SSI_SER, 0);

  // Set SPI format, TX-only mode, 8-bit data frame
  // Baud divider 16
  ssi_writereg(dev, SSI_CTRLR0, (tmod << 8) | (scpol << 7) | (scph << 6) | 0x7);
  ssi_writereg(dev, SSI_BAUDR, 32);

  // Set len Rx data bytes
  if(tmod >= 2) {
    if(rxlen == 0) {
      printf("bad rxlen\n");
    }
    ssi_writereg(dev, SSI_CTRLR1, rxlen - 1);
  }

  // Enable
  ssi_writereg(dev, SSI_SSIENR, 1);
}

//# Initialize the SPI controller for a transaction
//proc ssi_init { dev scpol scph tmod rxlen } {
//  global SSI_SSIENR SSI_SER SSI_CTRLR0 SSI_CTRLR1 SSI_BAUDR
//
//  # Set transaction start time
//  upvar #0 ssi_t_start t_start
//  set t_start [clock seconds]
//
//  # Disable master and output-enable
//  ssi_writereg $dev $SSI_SSIENR 0
//  ssi_writereg $dev $SSI_SER 0
//
//  # Set SPI format, TX-only mode, 8-bit data frame
//  # Baud divider 16
//  ssi_writereg $dev $SSI_CTRLR0 [expr ($tmod << 8) | ($scpol << 7) | ($scph << 6) | 0x7]
//  ssi_writereg $dev $SSI_BAUDR 16
//
//  # Set len Rx data bytes
//  if { $tmod >= 2 } {
//    if { $rxlen == 0 } {
//      error "bad rxlen"
//    }
//    ssi_writereg $dev $SSI_CTRLR1 [expr $rxlen - 1]
//  }
//
//  # Enable
//  ssi_writereg $dev $SSI_SSIENR 1
//}

// Push data to the TX FIFO
void ssi_tx(unsigned char dev, unsigned char* txbuf, unsigned char size) {
	for(int i = 0; i < size; i++)
	{
		ssi_writereg(dev, SSI_DR, txbuf[i]);
	}
}

//# Push data to the TX FIFO
//proc ssi_tx { dev txbuf } {
//  global SSI_DR
//  foreach b $txbuf {
//    ssi_writereg $dev $SSI_DR $b
//  }
//}

// Enable the Serial Slave (chip-select); releasing the TX FIFO
void ssi_enable_cs(unsigned char dev, unsigned char cs) {
  ssi_writereg(dev, SSI_SER, (1 << cs));
}

//# Enable the Serial Slave (chip-select); releasing the TX FIFO
//proc ssi_enable_cs { dev cs } {
//  global SSI_SER
//  ssi_writereg $dev $SSI_SER [expr 1 << $cs]
//}

// Check for timeout
void ssi_check_timeout() {
//  global SSI_OPERATION_TIMEOUT_S ssi_t_start
//  if { ([clock seconds] - $ssi_t_start) > $SSI_OPERATION_TIMEOUT_S } {
//    error "Operation timed out"
//  }
}

//# Check for timeout
//proc ssi_check_timeout {} {
//  global SSI_OPERATION_TIMEOUT_S ssi_t_start
//  if { ([clock seconds] - $ssi_t_start) > $SSI_OPERATION_TIMEOUT_S } {
//    error "Operation timed out"
//  }
//}

// Wait until the SSI controller is inactive
void ssi_wait_done(unsigned char dev) {
  while(ssi_readreg(dev, SSI_SR) & SSI_SR_BUSY) {
    ssi_check_timeout();
  }
}

//# Wait until the SSI controller is inactive
//proc ssi_wait_done { dev } {
//  global SSI_SR SSI_SR_BUSY
//  while { [ssi_readreg $dev $SSI_SR] & $SSI_SR_BUSY } {
//    ssi_check_timeout
//  }
//}

// Receive loop
//unsigned char ssi_rx(unsigned char dev, unsigned char dummy, unsigned char len, unsigned char* rxdat) {
//	unsigned char data, i = 0;
//	while(len > 0) {
//		ssi_check_timeout();
//		data = ssi_readreg(dev, SSI_SR);
//		if(data & SSI_SR_RFNE) {
//		  data = ssi_readreg(dev, SSI_DR)
//		  if(dummy == 0) {
//			rxdat[i++] = data;
//			len--;
//		  } else {
//			dummy--;
//		  }
//		}
//	}
//	ssi_wait_done(dev);
//	data = ssi_readreg(dev, SSI_RXFLR);
//	if(data > 0) {
//		printf("Unexpected RXFIFO data 0x%x\n", data);
//	}
//	return data;
//}

// read has one dummy cycle
unsigned char ssi_rx(unsigned char dev, unsigned char* rxdat) {
	unsigned char data;
	unsigned int dummy = 1, len = 1;
	while(len > 0) {
		ssi_check_timeout();
		data = ssi_readreg(dev, SSI_SR);
		if(data & SSI_SR_RFNE) {
		  data = ssi_readreg(dev, SSI_DR);
		  if(dummy == 0) {
			*rxdat = data;
			len--;
		  } else {
			dummy--;
		  }
		}
	}
	ssi_wait_done(dev);
	data = ssi_readreg(dev, SSI_RXFLR);
	if(data > 0) {
		printf("Unexpected RXFIFO data 0x%x\n", data);
	}
	return data;
}

//# Receive loop
//proc ssi_rx { dev dummy len } {
//  global SSI_DR SSI_SR SSI_RXFLR SSI_SR_RFNE
//  set rxdat {}
//  while { $len > 0 } {
//    ssi_check_timeout
//    if { [ssi_readreg $dev $SSI_SR] & $SSI_SR_RFNE } {
//      set b [ssi_readreg $dev $SSI_DR]
//      if { $dummy == 0 } {
//        lappend rxdat [expr $b & 0xff]
//        incr len -1
//      } else {
//        incr dummy -1
//      }
//    }
//  }
//  ssi_wait_done $dev
//  set rxflr [ssi_readreg $dev $SSI_RXFLR]
//  if { $rxflr > 0 } {
//    error [format "Unexpected RXFIFO data \[RXFLR=%d\]" $rxflr]
//  }
//  return $rxdat
//}

void ssi_dump_buf(unsigned char addr, unsigned char* buf) {
//  set len [llength $buf]
//  for { set i 0 } { $i < $len } { incr i } {
//    if { $i % 16 == 0 } {
//      puts -nonewline [format "%08x:" [expr $addr + $i]]
//    }
//    puts -nonewline [format " %02x" [lindex $buf $i]]
//    if { $i % 16 == 15 } {
//      puts ""
//    }
//  }
//  if { $i % 16 != 0 } {
//    puts ""
//  }
}

//proc ssi_dump_buf { addr buf } {
//  set len [llength $buf]
//  for { set i 0 } { $i < $len } { incr i } {
//    if { $i % 16 == 0 } {
//      puts -nonewline [format "%08x:" [expr $addr + $i]]
//    }
//    puts -nonewline [format " %02x" [lindex $buf $i]]
//    if { $i % 16 == 15 } {
//      puts ""
//    }
//  }
//  if { $i % 16 != 0 } {
//    puts ""
//  }
//}

// READ (0x0b), Address, 1 dummy byte, Data...
void ssi_cpld_write(unsigned char addr, unsigned char data) {
  // Initialize EEPROM-style read with 1 rx byte
  ssi_init(0, 0, 0, 3, 2);

  unsigned char buf[3];
  buf[0] = '\x02';
  buf[1] = addr;
  buf[2] = data;
  // Write Tx FIFO
  ssi_tx(0, buf, sizeof(buf));

  // Enable the SPI serial shifter
  ssi_enable_cs(0, 0);

//  # Fetch data
//  set res [ssi_rx 0 1 1]
//
//  # Dump response
//  ssi_dump_buf $addr $res
}

//# READ (0x0b), Address, 1 dummy byte, Data...
//proc ssi_cpld_write { addr data} {
//  # Initialize EEPROM-style read with 1 rx byte
//  ssi_init 0 0 0 3 2
//
//  # Write Tx FIFO
//  ssi_tx 0 [list 0x02 $addr $data]
//
//  # Enable the SPI serial shifter
//  ssi_enable_cs 0 0
//
//  # Fetch data
//  set res [ssi_rx 0 1 1]
//
//  # Dump response
//  ssi_dump_buf $addr $res
//}

//proc ssi_cpld_write_field { addr offset mask val } {
//   set rd_val [ssi_cpld_read $addr]
//
//   set ch_val [expr $rd_val & (~($mask << $offset)) | ($val << $offset)]
//
//   ssi_cpld_write $addr $ch_val
//}
//
//proc ssi_cpld_read_field { addr offset mask } {
//   set rd_val [ssi_cpld_read $addr]
//   set ch_val [expr ($rd_val >> $offset ) & $mask]
//   return $ch_val
//}

// READ (0x0b), Address, 1 dummy byte, Data...
unsigned char ssi_cpld_read(unsigned char addr) {
	unsigned char data;
	// Initialize EEPROM-style read with 1 rx byte
	ssi_init(0, 0, 0, 3, 2);

	unsigned char buf[2];
	buf[0] = '\x0b';
	buf[1] = addr;
//	buf[2] = 0;
//	buf[3] = 0;
	// Write Tx FIFO
	ssi_tx(0, buf, sizeof(buf));

	// Enable the SPI serial shifter
	ssi_enable_cs(0, 0);

	// Fetch data
	ssi_rx(0, &data);

//	# Dump response
//	ssi_dump_buf $addr $res
	data = gpio_get_byte();

	return data;
}

//# READ (0x0b), Address, 1 dummy byte, Data...
//proc ssi_cpld_read { addr } {
//  # Initialize EEPROM-style read with 1 rx byte
//  ssi_init 0 0 0 3 2
//
//  # Write Tx FIFO
//  ssi_tx 0 [list 0x0b $addr]
//
//  # Enable the SPI serial shifter
//  ssi_enable_cs 0 0
//
//  # Fetch data
//  set res [ssi_rx 0 1 1]
//
//  # Dump response
//  ssi_dump_buf $addr $res
//
//  return $res
//}

#if 0
proc ssi_cpld_read_core_pll_mul { } {
  ssi_cpld_read_field 0x11 0 0x3
}

proc ssi_cpld_read_cpu_pll_mul { } {
  ssi_cpld_read_field 0x11 2 0x3
}

proc ssi_cpld_read_flash_pll_mul { } {
  ssi_cpld_read_field 0x11 4 0x1
}

proc ssi_cpld_read_proto_disable { } {
  ssi_cpld_read_field 0x20 0 0x1
}

proc ssi_cpld_read_secure_enable { } {
  ssi_cpld_read_field 0x20 1 0x1
}

proc ssi_cpld_read_hw_lock { } {
  ssi_cpld_read_field 0x20 2 0x1
}

proc ssi_cpld_write_proto_disable { val } {
  ssi_cpld_write_field 0x20 0 0x1 $val
}

proc ssi_cpld_write_esecure_enable { val } {
  ssi_cpld_write_field 0x20 1 0x1 $val
}

proc ssi_cpld_write_hw_lock { val } {
  ssi_cpld_write_field 0x20 2 0x1 $val
}

proc ssi_cpld_power_cycle { } {
  ssi_cpld_write_field 0x1 7 0x1 0x0
  ssi_cpld_write_field 0x1 7 0x1 0x1
}

proc ssi_cpld_pims_reset { } {
  ssi_cpld_write_field 0x10 7 0x1 0x0
  ssi_cpld_write_field 0x10 7 0x1 0x1
}


# SPI Flash Access
# READ ID
# COMMAND: 9F
# DATA: ...
proc ssi_readid { dev cs scpol scph } {
  # read 16 bytes (16 data) in EEPROM mode
  ssi_init $dev $scpol $scph 3 16

  # Write Tx FIFO
  ssi_tx $dev { 0x9f }

  # Enable the SPI serial shifter
  ssi_enable_cs $dev $cs

  # Receive loop (1 dummy + 16 data)
  set res [ssi_rx $dev 0 16]
  ssi_dump_buf 0 $res
}

# SPI Flash Access
# READ SERIAL FLASH DISCOVERY PARAMETERS
# COMMAND: 5A 00 00 00
# DUMMY BYTES: 1
# DATA: ...
proc ssi_read_sfdp { dev cs scpol scph } {
  # read 17 bytes (1 dummy + 16 data) in EEPROM mode
  ssi_init $dev $scpol $scph 3 17

  # Write Tx FIFO
  ssi_tx $dev { 0x5a 0x00 0x00 0x00 }

  # Enable the SPI serial shifter
  ssi_enable_cs $dev $cs

  # Receive loop (1 dummy + 16 data)
  set res [ssi_rx $dev 1 16]
  ssi_dump_buf 0 $res
}

# SPI Flash READ
# COMMAND: 13 ADDR ADDR ADDR ADDR
# DATA: ...
proc ssi_flash_read { addr len } {
  set dev 0
  set cs 1

  # Initialize EEPROM-style read with len rx bytes
  ssi_init $dev 0 0 3 $len

  # Write Tx FIFO
  set txbuf { 0x13 }
  lappend txbuf [expr ($addr >> 24) & 0xff]
  lappend txbuf [expr ($addr >> 16) & 0xff]
  lappend txbuf [expr ($addr >> 8) & 0xff]
  lappend txbuf [expr ($addr >> 0) & 0xff]
  ssi_tx $dev $txbuf

  # Enable the SPI serial shifter
  ssi_enable_cs $dev $cs

  # Fetch data
  set res [ssi_rx $dev 0 $len]

  # Dump response
  ssi_dump_buf $addr $res
}

# SPI Flash Write Enable
# COMMAND: 06
proc ssi_flash_write_enable {} {
  global SSI_DR
  set dev 0
  set cs 1

  # TX-only mode transaction
  ssi_init $dev 0 0 1 0

  # Write Tx FIFO
  ssi_writereg $dev $SSI_DR 0x6

  # Enable the SPI serial shifter
  ssi_enable_cs $dev $cs

  # Wait for complete
  ssi_wait_done $dev
}

# SPI Flash Write
# COMMAND: 12 ADDR ADDR ADDR ADDR DAT...
proc ssi_flash_write { addr wrdat } {
}

proc ssi_mdio_write { addr data } {
    ssi_cpld_write 0x7 $addr
    ssi_cpld_write 0x8 [expr ($data >> 8) & 0xff]
    ssi_cpld_write 0x9 [expr ($data >> 0) & 0xff]
    ssi_cpld_write 0x6 [expr (0xc << 3) | 0x4 | 0x1]
    ssi_cpld_write 0x6 0
}
#endif

unsigned long long int xtoi(char *hexstring)
{
	unsigned long long int i = 0;

	if ((*hexstring == '0') && (*(hexstring+1) == 'x'))
		  hexstring += 2;
	while (*hexstring)
	{
		char c = toupper(*hexstring++);
		if ((c < '0') || (c > 'F') || ((c > '9') && (c < 'A')))
			break;
		c -= '0';
		if (c > 9)
			c -= 7;
		i = (i << 4) + c;
	}
	return i;
}

//test function
int main(int argc, char* argv[]) {

    std::shared_ptr<cpu_bus_arm_if> intf_shared_ptr(new cpu_bus_arm_if( "arm", ""));
    cpu::access()->add_if("arm", intf_shared_ptr.get());
    cpu::access()->set_cur_if_name("arm");

	unsigned char addr, data;
	char option[20];
	strcpy(option, argv[1]);
	addr = xtoi(argv[2]);
	if(!strcmp("rd", option))
	{
		data = ssi_cpld_read(addr);
		printf("cpld reg 0x%x value 0x%x\n", addr, data);
	} else if(!strcmp("wr", option))
	{
		data = xtoi(argv[3]);
		ssi_cpld_write(addr, data);
	}

	return 0;
}

