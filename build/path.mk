COMMON_SRC_DIR=			\
	diagmgr 			\
	dsp/asic			\
	dsp/pcie_h   		\
	util/devmgr			\
	util/eeutil			\
	util/i2cutil 		\
	util/rtcutil 		\
	util/smbutil 		\
	util/sysmon

COMMON_C_SRC_DIR=		\
	lib/i2c				\
	lib/i2csim

GO_TEST_DIR=						\
	device/powermodule/tps53659		\
	device/powermodule/tps549a20	\
	device/rtc/pcf85263a			\
	device/tempsensor/tmp422		\
	common/dmutex

AMD64_SRC_DIR=			\
	dsp/i2cspi 			\
	dsp/i2c 			\
	dsp/sfp 			\
	dsp/switch 			\
	dsp/qsfp 			\
	dsp/bcm 			\
	util/cpldutil		\
	util/mctputil		\
	util/fanutil        \
	util/fpgautil       \
	util/inventory		\
	util/mtptest		\
	util/swmadaputil	\
	util/switch			\
	util/pcieswutil

AMD64_C_SRC_DIR=		\
	lib/cpld			\
	util/jtag

ARM64_SRC_DIR=			\
	util/asicutil 		\
	util/ledutil 		\
	util/emmcutil		\
	dsp/i2c 			\
	dsp/emmc 			\
	dsp/led  			\
	dsp/mvl    			\
	dsp/nic_asic		\
	dsp/qsfp    		\
	dsp/rtc				\
	dsp/sfp				\
	dsp/ddr_stress

ARM64_C_SRC_DIR=		\
	lib/spi_userspace	\
	util/capricpld		\
	util/xo3dcpld		\
	util/artix7fpgaNew	\
	util/ddrstress  	\
	lib/capricpld		\
	lib/xo3dcpld



