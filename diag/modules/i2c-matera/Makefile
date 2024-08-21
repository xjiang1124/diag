# SPDX-License-Identifier: GPL-2.0
#
# Makefile for the i2c core.
#

obj	+= fpga_i2c_mux.o
obj	+= fpga_lipari.o
obj	+= fpga1_lipari.o

ccflags-$(CONFIG_I2C_DEBUG_CORE) := -DDEBUG
CFLAGS_i2c-core-base.o := -Wno-deprecated-declarations
obj-m += fpga_i2c_mux.o
obj-m += fpga_lipari.o
obj-m += fpga1_lipari.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
