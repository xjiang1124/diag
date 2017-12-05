SRC_DIR=				\
	diagmgr 			\
	dsp/pmbus   		\
	dsp/qsfp    		\
	dsp/rtc     		\
	dsp/pcieh   		\
	dsp/tempsensor     	\
	util/sysmon			\
	util/periutil 		\
	util/pmutil

#C_SRC_DIR=i2c

C_SRC_DIR=		\
	i2c			\
	i2csim

GO_TEST_DIR=	\
	common/powermodule/tps53659		\
	common/powermodule/tps549a20	\
	common/tempsensor/tmp422		\
	common/rtc/pcf85263a			\
	common/pmbCmd					\
	common/dmutex					\
	util/periutil					\
	util/pmutil						
