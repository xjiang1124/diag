COMMON_SRC_DIR=				\
	diagmgr 			\
	dsp/pcieh   		\
	dsp/pmbus   		\
	dsp/qsfp    		\
	dsp/rtc     		\
	dsp/tempsensor     	\
	util/devmgr			\
	util/smbutil 		\
	util/i2cutil 		\
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
	util/pcieswutil		\
	util/mtptest

AMD64_C_SRC_DIR=		\
	lib/cpld		\
	util/jtag

ARM64_SRC_DIR=
ARM64_C_SRC_DIR=



