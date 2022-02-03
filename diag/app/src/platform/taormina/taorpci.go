/* Notes
 
SPI BUS HOOKUP 
SPI0 = CPU CPLD 
SPI1 = ELBA0 CPLD
SPI2 = ELBA1 CPLD
SPI3 = GPIO CPLD0
SPI4 = GPIO CPLD1
SPI5 = GPIO CPLD2
SPI6 = ELBA0 SERIAL FLASH
SPI7 = ELBA1 SERIAL FLASH 
 
 
*/ 
 
package taormina

import (
    "bufio"
    "common/cli"
    "common/errType"
    "fmt"
    "os"
    /*
    "bufio"
    "bytes"
    "crypto/md5"
    "fmt"
    "hash"
    "io"
    "regexp"
    "strconv"
    "strings"
    "common/cli"
    "common/dcli"
    "common/misc"
    "common/errType"
    "device/cpld/nicCpldCommon"
    "encoding/json"
    "hardware/i2cinfo"
    "hardware/hwdev"
    "hardware/hwinfo"
    "io/ioutil"
    "os"
    "os/exec"
    "time"

    "device/bcm/td3"
    "device/cpu/XeonD"
    "device/fpga/taorfpga"
    "device/powermodule/sn1701022"
    "device/powermodule/tps549a20"
    "device/powermodule/tps544c20"
    "device/powermodule/tps53681"
    "device/psu/dps800" 
    "device/fanctrl/adt7462"
    "device/tempsensor/tmp451"
    "device/tempsensor/lm75a"

    "device/sfp"
    "device/qsfp"
    */
)


/*
00:00.0 Host bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DMI2 (rev 05)
00:01.0 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 1 (rev 05)
00:01.1 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 1 (rev 05)
00:02.0 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 2 (rev 05)
00:02.2 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 2 (rev 05)
00:03.0 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 3 (rev 05)
00:03.1 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 3 (rev 05)
00:03.2 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 3 (rev 05)
00:03.3 PCI bridge: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D PCI Express Root Port 3 (rev 05)
00:04.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 0 (rev 05)
00:04.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 1 (rev 05)
00:04.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 2 (rev 05)
00:04.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 3 (rev 05)
00:04.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 4 (rev 05)
00:04.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 5 (rev 05)
00:04.6 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 6 (rev 05)
00:04.7 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Crystal Beach DMA Channel 7 (rev 05)
00:05.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Map/VTd_Misc/System Management (rev 05)
00:05.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D IIO Hot Plug (rev 05)
00:05.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D IIO RAS/Control Status/Global Errors (rev 05)
00:05.4 PIC: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D I/O APIC (rev 05)
00:14.0 USB controller: Intel Corporation 8 Series/C220 Series Chipset Family USB xHCI (rev 05)
00:1a.0 USB controller: Intel Corporation 8 Series/C220 Series Chipset Family USB EHCI #2 (rev 05)
00:1c.0 PCI bridge: Intel Corporation 8 Series/C220 Series Chipset Family PCI Express Root Port #1 (rev d5)
00:1c.1 PCI bridge: Intel Corporation 8 Series/C220 Series Chipset Family PCI Express Root Port #2 (rev d5)
00:1d.0 USB controller: Intel Corporation 8 Series/C220 Series Chipset Family USB EHCI #1 (rev 05)
00:1f.0 ISA bridge: Intel Corporation C224 Series Chipset Family Server Standard SKU LPC Controller (rev 05)
00:1f.2 SATA controller: Intel Corporation 8 Series/C220 Series Chipset Family 6-port SATA Controller 1 [AHCI mode] (rev 05)
00:1f.3 SMBus: Intel Corporation 8 Series/C220 Series Chipset Family SMBus Controller (rev 05)
01:00.0 Ethernet controller: Broadcom Inc. and subsidiaries Device b870 (rev 01)
04:00.0 Unassigned class [ff00]: Intel Corporation 82599EB 10-Gigabit Dummy Function
05:00.0 PCI bridge: Device 1dd8:0002   
06:00.0 PCI bridge: Device 1dd8:1001
07:00.0 Ethernet controller: Device 1dd8:1004
0b:00.0 PCI bridge: Device 1dd8:0002   
0c:00.0 PCI bridge: Device 1dd8:1001
0d:00.0 Ethernet controller: Device 1dd8:1004
11:00.0 Ethernet controller: Intel Corporation I210 Gigabit Network Connection (rev 03)
12:00.0 Non-VGA unclassified device: Device 1dd8:0003
12:00.1 Non-VGA unclassified device: Device 1dd8:0004
12:00.2 Non-VGA unclassified device: Device 1dd8:0005
12:00.3 Non-VGA unclassified device: Device 1dd8:0006
ff:0b.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R3 QPI Link 0/1 (rev 05)
ff:0b.1 Performance counters: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R3 QPI Link 0/1 (rev 05)
ff:0b.2 Performance counters: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R3 QPI Link 0/1 (rev 05)
ff:0b.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R3 QPI Link Debug (rev 05)
ff:0c.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0c.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0c.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0c.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0c.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0c.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0f.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0f.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0f.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:0f.6 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Caching Agent (rev 05)
ff:10.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R2PCIe Agent (rev 05)
ff:10.1 Performance counters: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D R2PCIe Agent (rev 05)
ff:10.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Ubox (rev 05)
ff:10.6 Performance counters: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Ubox (rev 05)
ff:10.7 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Ubox (rev 05)
ff:12.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Home Agent 0 (rev 05)
ff:12.1 Performance counters: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Home Agent 0 (rev 05)
ff:13.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Target Address/Thermal/RAS (rev 05)
ff:13.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Target Address/Thermal/RAS (rev 05)
ff:13.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel Target Address Decoder (rev 05)
ff:13.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel Target Address Decoder (rev 05)
ff:13.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel Target Address Decoder (rev 05)
ff:13.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel Target Address Decoder (rev 05)
ff:13.6 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Channel 0/1 Broadcast (rev 05)
ff:13.7 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Global Broadcast (rev 05)
ff:14.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 0 Thermal Control (rev 05)
ff:14.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 1 Thermal Control (rev 05)
ff:14.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 0 Error (rev 05)
ff:14.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 1 Error (rev 05)
ff:14.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Channel 0/1 Interface (rev 05)
ff:14.5 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Channel 0/1 Interface (rev 05)
ff:14.6 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Channel 0/1 Interface (rev 05)
ff:14.7 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D DDRIO Channel 0/1 Interface (rev 05)
ff:15.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 2 Thermal Control (rev 05)
ff:15.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 3 Thermal Control (rev 05)
ff:15.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 2 Error (rev 05)
ff:15.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Memory Controller 0 - Channel 3 Error (rev 05)
ff:1e.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1e.1 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1e.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1e.3 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1e.4 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1f.0 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
ff:1f.2 System peripheral: Intel Corporation Xeon E7 v4/Xeon E5 v4/Xeon E3 v4/Xeon D Power Control Unit (rev 05)
*/

type pci_id struct {
    bus uint16
    dev uint16
    funct uint16
    vendId uint32
    devId uint32   
    name string
    bar0 uint64
    bar1 uint64
    check_link uint32
    link_width uint32
    link_speed uint32
} 

type pci_id_skip_list struct {
    bus uint16
    dev uint16
} 

const (
    PCI_VENDOR_ID_INTEL	      = 0x8086
    PCI_VENDOR_ID_BROADCOM    = 0x14e4
    PCI_VENDOR_ID_PENSANDO    = 0x1dd8


    PCI_STATUS		      = 0x0006	// 16 bits 
        PCI_STATUS_INTERRUPT      = 0x08	// Interrupt status 
        PCI_STATUS_CAP_LIST       = 0x10	// Support Capability List 
        PCI_STATUS_66MHZ          = 0x20	// Support 66 MHz PCI 2.1 bus 
        PCI_STATUS_UDF            = 0x40	// Support User Definable Features [obsolete] 
        PCI_STATUS_FAST_BACK      = 0x80	// Accept fast-back to back 
        PCI_STATUS_PARITY         = 0x100	// Detected parity error 
        PCI_STATUS_DEVSEL_MASK    = 0x600	// DEVSEL timing 
        PCI_STATUS_DEVSEL_FAST    = 0x000
        PCI_STATUS_DEVSEL_MEDIUM  = 0x200
        PCI_STATUS_DEVSEL_SLOW    = 0x400
        PCI_STATUS_SIG_TARGET_ABORT = 0x800     // Set on target abort 
        PCI_STATUS_REC_TARGET_ABORT = 0x1000    //  Master ack of " 
        PCI_STATUS_REC_MASTER_ABORT = 0x2000    // Set on master abort 
        PCI_STATUS_SIG_SYSTEM_ERROR = 0x4000    // Set when we drive SERR 
        PCI_STATUS_DETECTED_PARITY  = 0x8000    // Set on parity error 

    PCI_CAPABILITY_LIST	      = 0x0034	// Offset of first capability list entry 

// Capability lists 

    PCI_CAP_LIST_ID         = 0	// Capability ID 
      PCI_CAP_ID_PM		= 0x01	// Power Management 
      PCI_CAP_ID_AGP		= 0x02	// Accelerated Graphics Port 
      PCI_CAP_ID_VPD		= 0x03	// Vital Product Data 
      PCI_CAP_ID_SLOTID	        = 0x04	// Slot Identification 
      PCI_CAP_ID_MSI		= 0x05	// Message Signalled Interrupts 
      PCI_CAP_ID_CHSWP	        = 0x06	// CompactPCI HotSwap 
      PCI_CAP_ID_PCIX	        = 0x07	// PCI-X 
      PCI_CAP_ID_HT		= 0x08	// HyperTransport 
      PCI_CAP_ID_VNDR	        = 0x09	// Vendor-Specific 
      PCI_CAP_ID_DBG		= 0x0A	// Debug port 
      PCI_CAP_ID_CCRC	        = 0x0B	// CompactPCI Central Resource Control 
      PCI_CAP_ID_SHPC	        = 0x0C	// PCI Standard Hot-Plug Controller 
      PCI_CAP_ID_SSVID	        = 0x0D	// Bridge subsystem vendor/device ID 
      PCI_CAP_ID_AGP3	        = 0x0E	// AGP Target PCI-PCI bridge 
      PCI_CAP_ID_SECDEV	        = 0x0F	// Secure Device 
      PCI_CAP_ID_EXP		= 0x10	// PCI Express 
      PCI_CAP_ID_MSIX	        = 0x11	// MSI-X 
      PCI_CAP_ID_SATA	        = 0x12	// SATA Data/Index Conf. 
      PCI_CAP_ID_AF		= 0x13	// PCI Advanced Features 
      PCI_CAP_ID_EA		= 0x14	// PCI Enhanced Allocation 
      PCI_CAP_ID_MAX		= PCI_CAP_ID_EA
    PCI_CAP_LIST_NEXT	    = 1	// Next capability in the list 
    PCI_CAP_FLAGS	    = 2	// Capability defined flags (16 bits) 
    PCI_CAP_SIZEOF	    = 4

    PCI_EXP_FLAGS	    = 2	// Capabilities register 
    PCI_EXP_FLAGS_VERS	    = 0x000f	// Capability version 
    PCI_EXP_FLAGS_TYPE	    = 0x00f0	// Device/Port type 

    PCI_EXP_LNKSTA	    = 18	// Link Status 
     PCI_EXP_LNKSTA_CLS	        = 0x000f	// Current Link Speed 
     PCI_EXP_LNKSTA_CLS_2_5GB   = 0x0001 // Current Link Speed 2.5GT/s 
     PCI_EXP_LNKSTA_CLS_5_0GB   = 0x0002 // Current Link Speed 5.0GT/s 
     PCI_EXP_LNKSTA_CLS_8_0GB   = 0x0003 // Current Link Speed 8.0GT/s 
     PCI_EXP_LNKSTA_NLW	        = 0x03f0 // Negotiated Link Width 
     PCI_EXP_LNKSTA_NLW_X1	= 0x0010 // Current Link Width x1 
     PCI_EXP_LNKSTA_NLW_X2	= 0x0020 // Current Link Width x2 
     PCI_EXP_LNKSTA_NLW_X4	= 0x0040 // Current Link Width x4 
     PCI_EXP_LNKSTA_NLW_X8	= 0x0080 // Current Link Width x8 
     PCI_EXP_LNKSTA_NLW_X16	= 0x0100 // Current Link Width x8 
     PCI_EXP_LNKSTA_NLW_SHIFT   = 4	// start of NLW mask in link status
)

var g_pci_tbl = []pci_id{}

var pci_table = []pci_id{
      {
      bus  : 0x00, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f00,
      name   : "Xeon D DMI2",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_5_0GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x01, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f02,
      name   : "Xeon D PCI Express Root Port 1",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x01, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f03,
      name   : "Xeon D PCI Express Root Port 1",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x02, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f04,
      name   : "Xeon D PCI Express Root Port 2",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x02, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f06,
      name   : "Xeon D PCI Express Root Port 2",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x03, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f08,
      name   : "Xeon D PCI Express Root Port 3",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x03, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f09,
      name   : "Xeon D PCI Express Root Port 3",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x03, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f0A,
      name   : "Xeon D PCI Express Root Port 3",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x03, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f0B,
      name   : "Xeon D PCI Express Root Port 3",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f20,
      name   : "Xeon D Crystal Beach DMA Channel 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f21,
      name   : "Xeon D Crystal Beach DMA Channel 1",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f22,
      name   : "Xeon D Crystal Beach DMA Channel 2",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f23,
      name   : "Xeon D Crystal Beach DMA Channel 3",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f24,
      name   : "Xeon D Crystal Beach DMA Channel 4",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f25,
      name   : "Xeon D Crystal Beach DMA Channel 5",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x06,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f26,
      name   : "Xeon D Crystal Beach DMA Channel 6",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x04, 
      funct : 0x07,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f27,
      name   : "Xeon D Crystal Beach DMA Channel 7",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x05, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f28,
      name   : "Xeon D Map/VTd_Misc/System Managemen",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x05, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f29,
      name   : "Xeon D IIO Hot Plug",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x05, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f2A,
      name   : "Xeon D IIO RAS/Control Status/Global",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x05, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f2C,
      name   : "Xeon D I/O APIC",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x14, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c31,
      name   : "C220 Series Chipset Family USB",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x1A, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c2d,
      name   : "C220 Series Chipset Family USB EHCI #2",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x1C, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c10,
      name   : "C220 Series Chipset Family PCI Express Root Port #1",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x1C, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c12,
      name   : "C220 Series Chipset Family PCI Express Root Port #2",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x00, 
      dev  : 0x1D, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c26,
      name   : "C220 Series Chipset Family USB EHCI #2",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x1F, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c54,
      name   : "SKU LPC Controller",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x1F, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c02,
      name   : "6-port SATA Controller 1 [AHCI mode]",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x00, 
      dev  : 0x1F, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x8c22,
      name   : "SMBus Controller",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0x01, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_BROADCOM,
      devId  : 0xb870,
      name   : "Broadcom Inc. and subsidiaries Device b870",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x04, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x10a6,
      name   : "Intel Corporation 82599EB 10-Gigabit Dummy Function",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x05, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0002,
      name   : "PCI bridge: Device 1dd8:0002",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x06, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x1001,
      name   : "PCI bridge: Device 1dd8:1001",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x07, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x1004,
      name   : "PCI bridge: Device 1dd8:1004",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x0b, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0002,
      name   : "PCI bridge: Device 1dd8:0002",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x0c, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x1001,
      name   : "PCI bridge: Device 1dd8:1001",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x0d, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x1004,
      name   : "PCI bridge: Device 1dd8:1004",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X4,
      link_speed : PCI_EXP_LNKSTA_CLS_8_0GB,
      },
      {
      bus  : 0x11, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x1533,
      name   : "I210 Gigabit Network Connectionn",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x12, 
      dev  : 0x00, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0003,
      name   : "Non-VGA unclassified device: Device 1dd8:0003",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x12, 
      dev  : 0x00, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0004,
      name   : "Non-VGA unclassified device: Device 1dd8:0004",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x12, 
      dev  : 0x00, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0005,
      name   : "Non-VGA unclassified device: Device 1dd8:0005",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0x12, 
      dev  : 0x00, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_PENSANDO,
      devId  : 0x0006,
      name   : "Non-VGA unclassified device: Device 1dd8:0006",
      bar0 : 0,
      bar1 : 0,
      check_link : 1,
      link_width : PCI_EXP_LNKSTA_NLW_X1,
      link_speed : PCI_EXP_LNKSTA_CLS_2_5GB,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0b, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f81,
      name   : "Xeon D R3 QPI Link 0/1",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0b, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f36,
      name   : "Xeon D R3 QPI Link 0/1",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0b, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f37,
      name   : "Xeon D R3 QPI Link 0/1",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0b, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f76,
      name   : "Xeon D R3 QPI Link Debug",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe0,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe1,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe2,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe3,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe4,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0C, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fe5,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0f, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6ff8,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0f, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6ffc,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0f, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6ffd,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x0f, 
      funct : 0x06,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6ffe,
      name   : "Xeon E3 v4/Xeon D Caching Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x10, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f1d,
      name   : "Xeon D R2PCIe Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x10, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f34,
      name   : "Xeon D R2PCIe Agent",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x10, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f1e,
      name   : "Xeon D Ubox",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x10, 
      funct : 0x06,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f7d,
      name   : "Xeon D Ubox",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x10, 
      funct : 0x07,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f1f,
      name   : "Xeon D Ubox",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x12, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fa0,
      name   : "Xeon D Home Agent 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x12, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f30,
      name   : "Xeon D Home Agent 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fa8,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f71,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6faa,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fab,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fac,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fad,
      name   : "Xeon D Memory Controller 0",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x06,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fae,
      name   : "Xeon D DDRIO Channel 0/1 Broadcast",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x13, 
      funct : 0x07,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6faf,
      name   : "Xeon D DDRIO Global Broadcast",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb0,
      name   : "Xeon D Memory Controller 0 - Channel 0 Thermal Control",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb1,
      name   : "Xeon D Memory Controller 0 - Channel 1 Thermal Control",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb2,
      name   : "Xeon D Memory Controller 0 - Channel 0 Error",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb3,
      name   : "Xeon D Memory Controller 0 - Channel 1 Error",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fbc,
      name   : "Xeon D DDRIO Channel 0/1 Interface",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x05,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fbd,
      name   : "Xeon D DDRIO Channel 0/1 Interface",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x06,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fbe,
      name   : "Xeon D DDRIO Channel 0/1 Interface",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x14, 
      funct : 0x07,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fbf,
      name   : "Xeon D DDRIO Channel 0/1 Interface",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x15, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb4,
      name   : "Xeon D Memory Controller 0 - Channel 2 Thermal Control",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x15, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb5,
      name   : "Xeon D Memory Controller 0 - Channel 3 Thermal Control",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x15, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb6,
      name   : "Xeon D Memory Controller 0 - Channel 2 Error",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x15, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fb7,
      name   : "Xeon D Memory Controller 0 - Channel 3 Error",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1E, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f98,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1E, 
      funct : 0x01,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f99,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1E, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f9a,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1E, 
      funct : 0x03,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6fc0,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1E, 
      funct : 0x04,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f9c,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1F, 
      funct : 0x00,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f88,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
      {
      bus  : 0xFF, 
      dev  : 0x1F, 
      funct : 0x02,
      vendId : PCI_VENDOR_ID_INTEL,
      devId  : 0x6f8a,
      name   : "Xeon D Power Control Unit",
      bar0 : 0,
      bar1 : 0,
      check_link : 0,
      link_width : 0,
      link_speed : 0,
      },
}



var pci_id_skip_list_t = []pci_id_skip_list{
    {
        bus: 0x05,
        dev: 0x00, 
    },
    {
        bus: 0x06,
        dev: 0x00, 
    },
    {
        bus: 0x07,
        dev: 0x00, 
    },
    {
        bus: 0x0B,
        dev: 0x00, 
    },
    {
        bus: 0x0C,
        dev: 0x00, 
    },
    {
        bus: 0x0D,
        dev: 0x00, 
    },
}

func get_conf_byte(d []byte, pos uint32) (ret_byte byte) {
  return d[pos]
}

func get_conf_word(d []byte, pos uint32) (conf_word uint16) {
    conf_word = uint16(d[pos]) | (uint16(d[pos+1]) << 8);
    return
}

func cap_express_link( pci_id_t pci_id, config_space []byte, where uint8, type_t uint16) (err int) {
    var w uint16
    //for {
        cli.Printf("i", "      --> Checking link speed and lane width of device %.02x:%.02x:%.02x\n", pci_id_t.bus, pci_id_t.dev, pci_id_t.funct)
        w = get_conf_word(config_space, uint32(where) + PCI_EXP_LNKSTA);
        if ((w & PCI_EXP_LNKSTA_CLS) != uint16(pci_id_t.link_speed)) {
            cli.Printf ("e", "  ERROR: Unexpected Link Speed (%.02x).  Epxect %.02x\n", w & PCI_EXP_LNKSTA_CLS,  pci_id_t.link_speed);
            return ( -1 );
        }
     
        if ( (w & PCI_EXP_LNKSTA_NLW) != uint16(pci_id_t.link_width)) {
            
            cli.Printf ("e", "  ERROR: Unexpected Link Width 0x%x.  Epxect 0x%x\n", w & PCI_EXP_LNKSTA_NLW, pci_id_t.link_width );
            return ( -1 );
        } 
    //}
    return
}

func cap_express( pci_id_t pci_id, config_space []byte, where uint8, cap uint16) (err int) {
    var typet uint16 = (cap & PCI_EXP_FLAGS_TYPE) >> 4;
    err = cap_express_link(pci_id_t, config_space, where, typet)
    return
}

func pci_check_links(pci_id_t pci_id) (err int) {
    config_space  := []byte{}
    var filename string

    filename = fmt.Sprintf("/sys/bus/pci/devices/0000:%.02x:%.02x.%.01x/config",
      pci_id_t.bus, pci_id_t.dev, pci_id_t.funct );


    f, errGo := os.Open(filename)
    if errGo != nil {
        cli.Printf("e", " Failed to open filename=%s.   ERR=%v\n", filename, errGo)
        return
    }
    defer func() { 
        f.Close()
    } ()

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    for scanner.Scan() {
        b := scanner.Bytes()
        config_space = append(config_space, b[0])
    }
    if errGo = scanner.Err(); errGo != nil {
        cli.Printf("e", " Scanner Failed.  ERR=%v\n", errGo)
        return
    }

    conf_word := get_conf_word(config_space,  PCI_STATUS)
    if  (conf_word & PCI_STATUS_CAP_LIST) == PCI_STATUS_CAP_LIST {
        var been_there [256]uint8
        var where byte = get_conf_byte ( config_space, PCI_CAPABILITY_LIST ) 
        where &^=3;     //capability pointer
        for {
            var id, next byte
            var cap uint16
            if where == 0 {
                break
            }
            id = get_conf_byte(config_space, uint32(where) + PCI_CAP_LIST_ID);
            next = get_conf_byte(config_space, uint32(where) + PCI_CAP_LIST_NEXT);
            next &^=3; 
            cap = get_conf_word(config_space, uint32(where) + PCI_CAP_FLAGS);
            if ( been_there[where] > 0 ) {
                cli.Printf("e", " PCI CHAIN LOOPED\n")
                err = errType.FAIL
                return
            }
            been_there[where]++
            if id == 0xff {
                cli.Printf("e", " PCI CHAIN BROKEN\n")
                err = errType.FAIL
                return
            }
            if id == PCI_CAP_ID_EXP {
                err = cap_express(pci_id_t, config_space, where, cap)
                return
            }
            where = next;
        }
    }

    return
}

func pci_sort_struct() ( err int) {
    var n int = len(g_pci_tbl)
    var temppci_s pci_id;
    fmt.Printf(" Sorting  list length=%d\n", n)
    for i:=0; i<(n - 1); i++  {
        for j:=0; j<(n-i-1); j++ {
        
           if  uint16( (g_pci_tbl[j].bus << 8) | (g_pci_tbl[j].dev << 3) | g_pci_tbl[j].funct ) > 
               uint16( (g_pci_tbl[j+1].bus << 8) | (g_pci_tbl[j+1].dev << 3) | g_pci_tbl[j+1].funct ) {
                 temppci_s = g_pci_tbl[j+1]
                 g_pci_tbl[j+1] = g_pci_tbl[j]
                 g_pci_tbl[j] = temppci_s
            }
        }
    }
    return
}

func pci_scan_devices(skipelba uint32) (err int) {
    var devfn uint32
    var irq uint32
    var pci_tbl_tmp pci_id
    //var g_pci_tbl = []pci_id{}


    var filename string = "/proc/bus/pci/devices"
    f, errGo := os.Open(filename)
    if errGo != nil {
        cli.Printf("e", " Failed to open filename=%s.   ERR=%v\n", filename, errGo)
        err = errType.FAIL
        return
    }
    defer func() { 
        f.Close()
    } ()

    scanner := bufio.NewScanner(f)
    if errGo = scanner.Err(); errGo != nil {
        cli.Printf("e", " Scanner Error = %v", errGo)
        err = errType.FAIL
        return
    }

    for scanner.Scan() {
        fmt.Sscanf(scanner.Text(), "%4x %4x%4x %x %x %x ",&devfn, &pci_tbl_tmp.vendId, &pci_tbl_tmp.devId, &irq, &pci_tbl_tmp.bar0, &pci_tbl_tmp.bar1)
        pci_tbl_tmp.bus = uint16(devfn >> 8)
        pci_tbl_tmp.dev = uint16((devfn >> 3) & 0x1F)
        pci_tbl_tmp.funct = uint16(devfn & 0x7)
        g_pci_tbl = append(g_pci_tbl, pci_tbl_tmp)
    }
    pci_sort_struct()
    for i:=0; i<len(g_pci_tbl);i++ {
        fmt.Printf("%x:%x:%x %x %x %x %x\n", g_pci_tbl[i].bus, g_pci_tbl[i].dev, g_pci_tbl[i].funct, g_pci_tbl[i].vendId, g_pci_tbl[i].devId,g_pci_tbl[i].bar0,g_pci_tbl[i].bar1 )
    }

    return
}

func Print_List(ListName string, pci_table []pci_id ) {
    cli.Printf("i", "LIST=%s\n", ListName)
    for i:=0;i<len(pci_table);i++ {
        cli.Printf("i", "%.02x:%.02x:%.02x %.04x:%.04x %s\n", pci_table[i].bus, 
                                           pci_table[i].dev, 
                                           pci_table[i].funct,
                                           pci_table[i].vendId,
                                           pci_table[i].devId,
                                           pci_table[i].name);
    }
    return
}

func Check_Skip_List(bus uint16, dev uint16) (skip int) {
    //for i:=0; i < len(pci_id_skip_list_t); i++ {
    for _, pci_skip := range(pci_id_skip_list_t) {
        //if pci_id_skip_list_t[i].dev == dev && pci_id_skip_list_t[i].bus == bus {
        if pci_skip.dev == dev && pci_skip.bus == bus {
            return 1
        }
    }
    return 0
}

//Check for PSU and FAN MODULE PRESENCE
func Pci_scan(skipelba uint32)(err int) {
    var rc int 

    g_pci_tbl = nil

    
    //cli.Printf("i", "%d\n", pci_table[0].bus)
    cli.Printf("i", "Scanning PCI Devices\n")
    if err = pci_scan_devices(skipelba); err != errType.SUCCESS {
        cli.Printf("e", "Failed to Scan PCI Devices\n")
        err = errType.FAIL
        return
    }
    cli.Printf("i", " Checking PCI Devices Against Expected List\n");
    for i:=0; i < len(pci_table); i++ {

        if skipelba > 0 {
            skip:=Check_Skip_List(pci_table[i].bus, pci_table[i].dev)
            if skip > 0 {
                continue
            }
        }
    
        //see if the entry is there to start with based on bus:dev:func
        if (pci_table[i].bus != g_pci_tbl[i].bus || pci_table[i].dev != g_pci_tbl[i].dev || pci_table[i].funct != g_pci_tbl[i].funct ) {
            cli.Printf("e","ERROR: PCI DEVICE %.02x:%.02x:%.02x %.04x:%.04x %s NOT FOUND\n", g_pci_tbl[i].bus, 
                                                       g_pci_tbl[i].dev, 
                                                       g_pci_tbl[i].funct,
                                                       g_pci_tbl[i].vendId,
                                                       g_pci_tbl[i].devId,
                                                       g_pci_tbl[i].name);
            cli.Printf("e", " MATCH=  %.02x:%.02x:%.02x %.04x:%.04x %s\n", pci_table[i].bus, 
                                                       pci_table[i].dev, 
                                                       pci_table[i].funct,
                                                       pci_table[i].vendId,
                                                       pci_table[i].devId,
                                                       pci_table[i].name);
            err = errType.FAIL
            Print_List("Expected Table", pci_table ) 
            Print_List("Read Table from PCI", g_pci_tbl) 
            return
        } else {
            cli.Printf("i", "  %.02x:%.02x:%.02x %.04x:%.04x %s\n", pci_table[i].bus, 
                                                       pci_table[i].dev, 
                                                       pci_table[i].funct,
                                                       pci_table[i].vendId,
                                                       pci_table[i].devId,
                                                       pci_table[i].name);
        }          
        
        if pci_table[i].check_link > 0 {
            rc = pci_check_links(pci_table[i])
            if rc != errType.SUCCESS {
                err = errType.FAIL
            }
        }

    }
    return
}


