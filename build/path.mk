COMMON_SRC_DIR=			\
	diagmgr 			\
	dsp/asic			\
	dsp/pcie_h   		\
	util/devmgr			\
	util/devmgr_v2			\
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
	dsp/cpu 			\
	dsp/i2cspi 			\
	dsp/i2c 			\
	dsp/sfp 			\
	dsp/switch 			\
	dsp/qsfp 			\
	dsp/bcm 			\
	util/bcmutil        \
	util/cpldutil		\
	util/mctputil		\
	util/fanutil        \
	util/fpgautil       \
	util/inventory		\
	util/mtptest		\
	util/swmadaputil	\
	util/switch			\
	util/pcieswutil     \
	util/bcmutil        \
	util/sucutil

AMD64_C_SRC_DIR=		\
	lib/cpld			\
	lib/fpga_util		\
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
	dsp/mem				\
	dsp/sys

ARM64_C_SRC_DIR=		\
	lib/spi_userspace	\
	util/capricpld		\
	util/xo3dcpld		\
	util/artix7fpgaNew	\
	lib/capricpld		\
	lib/xo3dcpld

ARM_SRC_DIR=            \
    util/asicutil       \
    util/ledutil        \
    util/emmcutil       \
    dsp/i2c             \
    dsp/emmc            \
    dsp/led             \
    dsp/mvl             \
    dsp/nic_asic        \
    dsp/qsfp            \
    dsp/rtc             \
    dsp/sfp             \
    dsp/mem             \
    dsp/sys

ARM_C_SRC_DIR=          \
    lib/spi_userspace   \
    util/capricpld      \
    util/xo3dcpld       \
    util/artix7fpgaNew  \
    lib/capricpld       \
    lib/xo3dcpld

