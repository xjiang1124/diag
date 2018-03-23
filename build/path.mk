COMMON_SRC_DIR=				\
	diagmgr 			\
	dsp/pmbus   		\
	dsp/qsfp    		\
	dsp/rtc     		\
	dsp/pcieh   		\
	dsp/tempsensor     	\
	util/sysmon			\
	util/periutil 		\
	util/smbutil 		\
	util/devmgr

COMMON_C_LIB_DIR=		\
	lib/i2c				\
	lib/i2csim			\
	lib/cpld

COMMON_C_SRC_DIR=

GO_TEST_DIR=						\
	device/powermodule/tps53659		\
	device/powermodule/tps549a20	\
	device/tempsensor/tmp422		\
	device/rtc/pcf85263a			\
	common/dmutex					\
	util/periutil					

AMD64_SRC_DIR=
AMD64_C_LIB_DIR=

AMD64_C_SRC_DIR=		\
	util/jtag			\
	util/cpld			\
	util/mdio			\
	util/spi

ARM64_SRC_DIR=
ARM64_C_LIB_DIR=
ARM64_C_SRC_DIR=



