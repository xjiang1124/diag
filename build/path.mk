SRC_DIR=				\
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

#C_SRC_DIR=i2c

C_SRC_DIR=		\
	i2c			\
	i2csim

GO_TEST_DIR=	\
	device/powermodule/tps53659		\
	device/powermodule/tps549a20	\
	device/tempsensor/tmp422		\
	device/rtc/pcf85263a			\
	common/dmutex					\
	util/periutil					
