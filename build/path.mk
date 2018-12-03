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
	util/cpldutil		\
	util/inventory		\
	util/mtptest		\
	util/pcieswutil

AMD64_C_SRC_DIR=		\
	lib/cpld			\
	util/jtag

ARM64_SRC_DIR=			\
	util/ledutil 		\
	dsp/cpld     		\
	dsp/i2c 			\
	dsp/intr    		\
	dsp/mvl    			\
	dsp/qsfp    		\
	dsp/rtc     		\
	dsp/spi    			\
	dsp/tempsensor

ARM64_C_SRC_DIR=		\
	lib/spi_userspace	\
	util/capricpld		\
	lib/capricpld



