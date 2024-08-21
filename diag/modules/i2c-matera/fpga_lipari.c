// SPDX-License-Identifier: GPL-2.0
/*
 * i2c-ocores.c: I2C bus driver for OpenCores I2C controller
 * (https://opencores.org/project/i2c/overview)
 *
 * Peter Korsgaard <peter@korsgaard.com>
 * David Wang <david.wang2@amd.com>
 *
 * Support for the GRLIB port of the controller by
 * Andreas Larsson <andreas@gaisler.com>
 */

#include <linux/delay.h>
#include <linux/err.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/errno.h>
#include <linux/platform_device.h>
#include <linux/pci.h>
#include <linux/i2c.h>
#include <linux/interrupt.h>
#include <linux/wait.h>
#include <linux/platform_data/i2c-ocores.h>
#include <linux/slab.h>
#include <linux/io.h>
#include <linux/log2.h>
#include <linux/spinlock.h>
#include <linux/jiffies.h>
#include "fpga_lipari.h"
#include "fpga_i2c_mux.h"

static void __iomem *fpga_membase;

uint32_t get_bits(uint32_t val, uint32_t start_bit, uint32_t end_bit)
{
    uint32_t ones = ~0;
    uint32_t l = ones << (end_bit + 1);
    uint32_t r = (1 << start_bit) - 1;
    uint32_t mask = ~(l | r);
    return ((val & mask) >> start_bit);
}

uint32_t update_bits(uint32_t reg_val, uint32_t val,
                     uint32_t start_bit, uint32_t end_bit)
{
    uint32_t ones = ~0;
    uint32_t l = ones << (end_bit + 1);
    uint32_t r = (1 << start_bit) - 1;
    uint32_t mask = (l | r);
    return ((reg_val & mask) | (val << start_bit)) ;
}

GEN_SHOW(fpga_id,0,16,31)
GEN_SHOW(fpga_rev,0,0,15)
GEN_SHOW(board_rev,8,0,3)
GEN_SHOW(reset_cause_0,512,0,31)
GEN_SHOW(reset_cause_1,516,0,31)
GEN_SHOW(reset_cause_2,520,0,31)
GEN_SHOW(reset_cause_3,524,0,31)
GEN_SHOW(reset_cause_4,528,0,31)
GEN_SHOW(reset_cause_5,532,0,31)
GEN_SHOW(reset_cause_6,536,0,31)
GEN_SHOW(reset_cause_7,540,0,31)
GEN_STORE(soft_i2c_spi_reset,680,0,7)
GEN_SHOW(protect_golden_bios,684,0,0)
GEN_STORE(protect_golden_bios,684,0,0)
GEN_SHOW(protect_primary_bios,684,1,1)
GEN_STORE(protect_primary_bios,684,1,1)
GEN_SHOW(protect_nic_flash,684,2,2)
GEN_STORE(protect_nic_flash,684,2,2)
GEN_SHOW(protect_fru_eeprom,684,3,3)
GEN_STORE(protect_fru_eeprom,684,3,3)
GEN_SHOW(protect_fpga1_cfg_spi,684,4,4)
GEN_STORE(protect_fpga1_cfg_spi,684,4,4)
GEN_SHOW(protect_fpga0_cfg_spi,684,5,5)
GEN_STORE(protect_fpga0_cfg_spi,684,5,5)
GEN_SHOW(protect_th4_qspi,684,6,6)
GEN_STORE(protect_th4_qspi,684,6,6)
GEN_SHOW(protect_elba_qspi,684,7,7)
GEN_STORE(protect_elba_qspi,684,7,7)
GEN_SHOW(protect_ccpld_acc,684,8,8)
GEN_STORE(protect_ccpld_acc,684,8,8)
GEN_SHOW(led_brightness,688,0,3)
GEN_STORE(led_brightness,688,0,3)
GEN_SHOW(led_slow_blink_speed,688,8,12)
GEN_STORE(led_slow_blink_speed,688,8,12)
GEN_SHOW(led_fast_blink_speed,688,16,20)
GEN_STORE(led_fast_blink_speed,688,16,20)
GEN_SHOW(led_syshealth,692,0,7)
GEN_STORE(led_syshealth,692,0,7)
GEN_SHOW(led_chassis,692,8,15)
GEN_STORE(led_chassis,692,8,15)
GEN_SHOW(led_uid_blue,692,16,23)
GEN_STORE(led_uid_blue,692,16,23)
GEN_SHOW(led_fan0,696,0,7)
GEN_STORE(led_fan0,696,0,7)
GEN_SHOW(led_fan1,696,8,15)
GEN_STORE(led_fan1,696,8,15)
GEN_SHOW(led_fan2,696,16,23)
GEN_STORE(led_fan2,696,16,23)
GEN_SHOW(led_fan3,696,24,31)
GEN_STORE(led_fan3,696,24,31)
GEN_SHOW(led_chip_port0,700,0,7)
GEN_STORE(led_chip_port0,700,0,7)
GEN_SHOW(led_chip_port1,700,8,15)
GEN_STORE(led_chip_port1,700,8,15)
GEN_SHOW(led_chip_port2,700,16,23)
GEN_STORE(led_chip_port2,700,16,23)
GEN_SHOW(led_chip_port3,700,24,31)
GEN_STORE(led_chip_port3,700,24,31)
GEN_SHOW(led_chip_port4,704,0,7)
GEN_STORE(led_chip_port4,704,0,7)
GEN_SHOW(led_chip_port5,704,8,15)
GEN_STORE(led_chip_port5,704,8,15)
GEN_SHOW(led_chip_port6,704,16,23)
GEN_STORE(led_chip_port6,704,16,23)
GEN_SHOW(led_chip_port7,704,24,31)
GEN_STORE(led_chip_port7,704,24,31)
GEN_SHOW(led_chip_port8,708,0,7)
GEN_STORE(led_chip_port8,708,0,7)
GEN_SHOW(led_chip_port9,708,8,15)
GEN_STORE(led_chip_port9,708,8,15)
GEN_SHOW(led_chip_port10,708,16,23)
GEN_STORE(led_chip_port10,708,16,23)
GEN_SHOW(led_chip_port11,708,24,31)
GEN_STORE(led_chip_port11,708,24,31)
GEN_SHOW(led_chip_port12,712,0,7)
GEN_STORE(led_chip_port12,712,0,7)
GEN_SHOW(led_chip_port13,712,8,15)
GEN_STORE(led_chip_port13,712,8,15)
GEN_SHOW(led_chip_port14,712,16,23)
GEN_STORE(led_chip_port14,712,16,23)
GEN_SHOW(led_chip_port15,712,24,31)
GEN_STORE(led_chip_port15,712,24,31)
GEN_SHOW(led_chip_port16,716,0,7)
GEN_STORE(led_chip_port16,716,0,7)
GEN_SHOW(led_chip_port17,716,8,15)
GEN_STORE(led_chip_port17,716,8,15)
GEN_SHOW(led_chip_port18,716,16,23)
GEN_STORE(led_chip_port18,716,16,23)
GEN_SHOW(led_chip_port19,716,24,31)
GEN_STORE(led_chip_port19,716,24,31)
GEN_SHOW(led_chip_port20,720,0,7)
GEN_STORE(led_chip_port20,720,0,7)
GEN_SHOW(led_chip_port21,720,8,15)
GEN_STORE(led_chip_port21,720,8,15)
GEN_SHOW(led_chip_port22,720,16,23)
GEN_STORE(led_chip_port22,720,16,23)
GEN_SHOW(led_chip_port23,720,24,31)
GEN_STORE(led_chip_port23,720,24,31)
GEN_SHOW(led_chip_port24,724,0,7)
GEN_STORE(led_chip_port24,724,0,7)
GEN_SHOW(led_chip_port25,724,8,15)
GEN_STORE(led_chip_port25,724,8,15)
GEN_SHOW(led_chip_port26,724,16,23)
GEN_STORE(led_chip_port26,724,16,23)
GEN_SHOW(led_chip_port27,724,24,31)
GEN_STORE(led_chip_port27,724,24,31)
GEN_SHOW(qsfp0_absent,768,0,0)
GEN_SHOW(qsfp0_int_pending,768,1,1)
GEN_SHOW(qsfp1_absent,768,8,8)
GEN_SHOW(qsfp1_int_pending,768,9,9)
GEN_SHOW(qsfp2_absent,768,16,16)
GEN_SHOW(qsfp2_int_pending,768,17,17)
GEN_SHOW(qsfp3_absent,768,24,24)
GEN_SHOW(qsfp3_int_pending,768,25,25)
GEN_SHOW(qsfp4_absent,776,0,0)
GEN_SHOW(qsfp4_int_pending,776,1,1)
GEN_SHOW(qsfp5_absent,776,8,8)
GEN_SHOW(qsfp5_int_pending,776,9,9)
GEN_SHOW(qsfp6_absent,776,16,16)
GEN_SHOW(qsfp6_int_pending,776,17,17)
GEN_SHOW(qsfp7_absent,776,24,24)
GEN_SHOW(qsfp7_int_pending,776,25,25)
GEN_SHOW(qsfp8_absent,784,0,0)
GEN_SHOW(qsfp8_int_pending,784,1,1)
GEN_SHOW(qsfp9_absent,784,8,8)
GEN_SHOW(qsfp9_int_pending,784,9,9)
GEN_SHOW(qsfp10_absent,784,16,16)
GEN_SHOW(qsfp10_int_pending,784,17,17)
GEN_SHOW(qsfp11_absent,784,24,24)
GEN_SHOW(qsfp11_int_pending,784,25,25)
GEN_SHOW(qsfp12_absent,792,0,0)
GEN_SHOW(qsfp12_int_pending,792,1,1)
GEN_SHOW(qsfp13_absent,792,8,8)
GEN_SHOW(qsfp13_int_pending,792,9,9)
GEN_SHOW(qsfp14_absent,792,16,16)
GEN_SHOW(qsfp14_int_pending,792,17,17)
GEN_SHOW(qsfp15_absent,792,24,24)
GEN_SHOW(qsfp15_int_pending,792,25,25)
GEN_SHOW(qsfp16_absent,800,0,0)
GEN_SHOW(qsfp16_int_pending,800,1,1)
GEN_SHOW(qsfp17_absent,800,8,8)
GEN_SHOW(qsfp17_int_pending,800,9,9)
GEN_SHOW(qsfp18_absent,800,16,16)
GEN_SHOW(qsfp18_int_pending,800,17,17)
GEN_SHOW(qsfp19_absent,800,24,24)
GEN_SHOW(qsfp19_int_pending,800,25,25)
GEN_SHOW(qsfp20_absent,808,0,0)
GEN_SHOW(qsfp20_int_pending,808,1,1)
GEN_SHOW(qsfp21_absent,808,8,8)
GEN_SHOW(qsfp21_int_pending,808,9,9)
GEN_SHOW(qsfp22_absent,808,16,16)
GEN_SHOW(qsfp22_int_pending,808,17,17)
GEN_SHOW(qsfp23_absent,808,24,24)
GEN_SHOW(qsfp23_int_pending,808,25,25)
GEN_SHOW(qsfp24_absent,816,0,0)
GEN_SHOW(qsfp24_int_pending,816,1,1)
GEN_SHOW(qsfp25_absent,816,8,8)
GEN_SHOW(qsfp25_int_pending,816,9,9)
GEN_SHOW(qsfp26_absent,816,16,16)
GEN_SHOW(qsfp26_int_pending,816,17,17)
GEN_SHOW(qsfp27_absent,816,24,24)
GEN_SHOW(qsfp27_int_pending,816,25,25)
GEN_SHOW(qsfp0_reset,772,0,0)
GEN_STORE(qsfp0_reset,772,0,0)
GEN_SHOW(qsfp0_low_power_mode,772,1,1)
GEN_STORE(qsfp0_low_power_mode,772,1,1)
GEN_SHOW(qsfp1_reset,772,8,8)
GEN_STORE(qsfp1_reset,772,8,8)
GEN_SHOW(qsfp1_low_power_mode,772,9,9)
GEN_STORE(qsfp1_low_power_mode,772,9,9)
GEN_SHOW(qsfp2_reset,772,16,16)
GEN_STORE(qsfp2_reset,772,16,16)
GEN_SHOW(qsfp2_low_power_mode,772,17,17)
GEN_STORE(qsfp2_low_power_mode,772,17,17)
GEN_SHOW(qsfp3_reset,772,24,24)
GEN_STORE(qsfp3_reset,772,24,24)
GEN_SHOW(qsfp3_low_power_mode,772,25,25)
GEN_STORE(qsfp3_low_power_mode,772,25,25)
GEN_SHOW(qsfp4_reset,780,0,0)
GEN_STORE(qsfp4_reset,780,0,0)
GEN_SHOW(qsfp4_low_power_mode,780,1,1)
GEN_STORE(qsfp4_low_power_mode,780,1,1)
GEN_SHOW(qsfp5_reset,780,8,8)
GEN_STORE(qsfp5_reset,780,8,8)
GEN_SHOW(qsfp5_low_power_mode,780,9,9)
GEN_STORE(qsfp5_low_power_mode,780,9,9)
GEN_SHOW(qsfp6_reset,780,16,16)
GEN_STORE(qsfp6_reset,780,16,16)
GEN_SHOW(qsfp6_low_power_mode,780,17,17)
GEN_STORE(qsfp6_low_power_mode,780,17,17)
GEN_SHOW(qsfp7_reset,780,24,24)
GEN_STORE(qsfp7_reset,780,24,24)
GEN_SHOW(qsfp7_low_power_mode,780,25,25)
GEN_STORE(qsfp7_low_power_mode,780,25,25)
GEN_SHOW(qsfp8_reset,788,0,0)
GEN_STORE(qsfp8_reset,788,0,0)
GEN_SHOW(qsfp8_low_power_mode,788,1,1)
GEN_STORE(qsfp8_low_power_mode,788,1,1)
GEN_SHOW(qsfp9_reset,788,8,8)
GEN_STORE(qsfp9_reset,788,8,8)
GEN_SHOW(qsfp9_low_power_mode,788,9,9)
GEN_STORE(qsfp9_low_power_mode,788,9,9)
GEN_SHOW(qsfp10_reset,788,16,16)
GEN_STORE(qsfp10_reset,788,16,16)
GEN_SHOW(qsfp10_low_power_mode,788,17,17)
GEN_STORE(qsfp10_low_power_mode,788,17,17)
GEN_SHOW(qsfp11_reset,788,24,24)
GEN_STORE(qsfp11_reset,788,24,24)
GEN_SHOW(qsfp11_low_power_mode,788,25,25)
GEN_STORE(qsfp11_low_power_mode,788,25,25)
GEN_SHOW(qsfp12_reset,796,0,0)
GEN_STORE(qsfp12_reset,796,0,0)
GEN_SHOW(qsfp12_low_power_mode,796,1,1)
GEN_STORE(qsfp12_low_power_mode,796,1,1)
GEN_SHOW(qsfp13_reset,796,8,8)
GEN_STORE(qsfp13_reset,796,8,8)
GEN_SHOW(qsfp13_low_power_mode,796,9,9)
GEN_STORE(qsfp13_low_power_mode,796,9,9)
GEN_SHOW(qsfp14_reset,796,16,16)
GEN_STORE(qsfp14_reset,796,16,16)
GEN_SHOW(qsfp14_low_power_mode,796,17,17)
GEN_STORE(qsfp14_low_power_mode,796,17,17)
GEN_SHOW(qsfp15_reset,796,24,24)
GEN_STORE(qsfp15_reset,796,24,24)
GEN_SHOW(qsfp15_low_power_mode,796,25,25)
GEN_STORE(qsfp15_low_power_mode,796,25,25)
GEN_SHOW(qsfp16_reset,804,0,0)
GEN_STORE(qsfp16_reset,804,0,0)
GEN_SHOW(qsfp16_low_power_mode,804,1,1)
GEN_STORE(qsfp16_low_power_mode,804,1,1)
GEN_SHOW(qsfp17_reset,804,8,8)
GEN_STORE(qsfp17_reset,804,8,8)
GEN_SHOW(qsfp17_low_power_mode,804,9,9)
GEN_STORE(qsfp17_low_power_mode,804,9,9)
GEN_SHOW(qsfp18_reset,804,16,16)
GEN_STORE(qsfp18_reset,804,16,16)
GEN_SHOW(qsfp18_low_power_mode,804,17,17)
GEN_STORE(qsfp18_low_power_mode,804,17,17)
GEN_SHOW(qsfp19_reset,804,24,24)
GEN_STORE(qsfp19_reset,804,24,24)
GEN_SHOW(qsfp19_low_power_mode,804,25,25)
GEN_STORE(qsfp19_low_power_mode,804,25,25)
GEN_SHOW(qsfp20_reset,812,0,0)
GEN_STORE(qsfp20_reset,812,0,0)
GEN_SHOW(qsfp20_low_power_mode,812,1,1)
GEN_STORE(qsfp20_low_power_mode,812,1,1)
GEN_SHOW(qsfp21_reset,812,8,8)
GEN_STORE(qsfp21_reset,812,8,8)
GEN_SHOW(qsfp21_low_power_mode,812,9,9)
GEN_STORE(qsfp21_low_power_mode,812,9,9)
GEN_SHOW(qsfp22_reset,812,16,16)
GEN_STORE(qsfp22_reset,812,16,16)
GEN_SHOW(qsfp22_low_power_mode,812,17,17)
GEN_STORE(qsfp22_low_power_mode,812,17,17)
GEN_SHOW(qsfp23_reset,812,24,24)
GEN_STORE(qsfp23_reset,812,24,24)
GEN_SHOW(qsfp23_low_power_mode,812,25,25)
GEN_STORE(qsfp23_low_power_mode,812,25,25)
GEN_SHOW(qsfp24_reset,820,0,0)
GEN_STORE(qsfp24_reset,820,0,0)
GEN_SHOW(qsfp24_low_power_mode,820,1,1)
GEN_STORE(qsfp24_low_power_mode,820,1,1)
GEN_SHOW(qsfp25_reset,820,8,8)
GEN_STORE(qsfp25_reset,820,8,8)
GEN_SHOW(qsfp25_low_power_mode,820,9,9)
GEN_STORE(qsfp25_low_power_mode,820,9,9)
GEN_SHOW(qsfp26_reset,820,16,16)
GEN_STORE(qsfp26_reset,820,16,16)
GEN_SHOW(qsfp26_low_power_mode,820,17,17)
GEN_STORE(qsfp26_low_power_mode,820,17,17)
GEN_SHOW(qsfp27_reset,820,24,24)
GEN_STORE(qsfp27_reset,820,24,24)
GEN_SHOW(qsfp27_low_power_mode,820,25,25)
GEN_STORE(qsfp27_low_power_mode,820,25,25)
GEN_SHOW(psu1_ctrl,1280,0,7)
GEN_STORE(psu1_ctrl,1280,0,7)
GEN_SHOW(psu2_ctrl,1280,8,15)
GEN_STORE(psu2_ctrl,1280,8,15)
GEN_SHOW(psu1_present,1284,0,0)
GEN_SHOW(psu1_alert,1284,1,1)
GEN_SHOW(psu1_power_ok,1284,2,2)
GEN_SHOW(psu2_present,1284,8,8)
GEN_SHOW(psu2_alert,1284,9,9)
GEN_SHOW(psu2_power_ok,1284,10,10)
GEN_SHOW(fan0_power_enable,1288,0,0)
GEN_STORE(fan0_power_enable,1288,0,0)
GEN_SHOW(fan1_power_enable,1288,1,1)
GEN_STORE(fan1_power_enable,1288,1,1)
GEN_SHOW(fan2_power_enable,1288,2,2)
GEN_STORE(fan2_power_enable,1288,2,2)
GEN_SHOW(fan3_power_enable,1288,3,3)
GEN_STORE(fan3_power_enable,1288,3,3)
GEN_SHOW(fan0_pwn_ctrl,1292,0,7)
GEN_STORE(fan0_pwn_ctrl,1292,0,7)
GEN_SHOW(fan1_pwn_ctrl,1292,8,15)
GEN_STORE(fan1_pwn_ctrl,1292,8,15)
GEN_SHOW(fan2_pwn_ctrl,1292,16,23)
GEN_STORE(fan2_pwn_ctrl,1292,16,23)
GEN_SHOW(fan3_pwn_ctrl,1292,24,31)
GEN_STORE(fan3_pwn_ctrl,1292,24,31)
GEN_SHOW(fan0_present,1296,0,0)
GEN_SHOW(fan1_present,1296,1,1)
GEN_SHOW(fan2_present,1296,2,2)
GEN_SHOW(fan3_present,1296,3,3)
GEN_SHOW(fan0_direction,1296,4,4)
GEN_SHOW(fan1_direction,1296,5,5)
GEN_SHOW(fan2_direction,1296,6,6)
GEN_SHOW(fan3_direction,1296,7,7)
GEN_SHOW(fan0_hw_rev,1296,8,9)
GEN_SHOW(fan1_hw_rev,1296,10,11)
GEN_SHOW(fan2_hw_rev,1296,12,13)
GEN_SHOW(fan3_hw_rev,1296,14,15)
GEN_SHOW(fan0_alert,1296,16,16)
GEN_SHOW(fan1_alert,1296,17,17)
GEN_SHOW(fan2_alert,1296,18,18)
GEN_SHOW(fan3_alert,1296,19,19)
GEN_SHOW(fan0_error,1296,20,20)
GEN_SHOW(fan1_error,1296,21,21)
GEN_SHOW(fan2_error,1296,22,22)
GEN_SHOW(fan3_error,1296,23,23)
GEN_SHOW(fan0_inlet,1300,16,31)
GEN_SHOW(fan0_outlet,1300,0,15)
GEN_SHOW(fan1_inlet,1304,16,31)
GEN_SHOW(fan1_outlet,1304,0,15)
GEN_SHOW(fan2_inlet,1308,16,31)
GEN_SHOW(fan2_outlet,1308,0,15)
GEN_SHOW(fan3_inlet,1312,16,31)
GEN_SHOW(fan3_outlet,1312,0,15)
GEN_SHOW(elba0_power_ctrl,1344,0,7)
GEN_STORE(elba0_power_ctrl,1344,0,7)
GEN_SHOW(elba1_power_ctrl,1352,0,7)
GEN_STORE(elba1_power_ctrl,1352,0,7)
GEN_SHOW(elba2_power_ctrl,1360,0,7)
GEN_STORE(elba2_power_ctrl,1360,0,7)
GEN_SHOW(elba3_power_ctrl,1368,0,7)
GEN_STORE(elba3_power_ctrl,1368,0,7)
GEN_SHOW(elba4_power_ctrl,1376,0,7)
GEN_STORE(elba4_power_ctrl,1376,0,7)
GEN_SHOW(elba5_power_ctrl,1384,0,7)
GEN_STORE(elba5_power_ctrl,1384,0,7)
GEN_SHOW(elba6_power_ctrl,1392,0,7)
GEN_STORE(elba6_power_ctrl,1392,0,7)
GEN_SHOW(elba7_power_ctrl,1400,0,7)
GEN_STORE(elba7_power_ctrl,1400,0,7)
GEN_SHOW(elba0_power_stat,1348,0,3)
GEN_SHOW(elba1_power_stat,1356,0,3)
GEN_SHOW(elba2_power_stat,1364,0,3)
GEN_SHOW(elba3_power_stat,1372,0,3)
GEN_SHOW(elba4_power_stat,1380,0,3)
GEN_SHOW(elba5_power_stat,1388,0,3)
GEN_SHOW(elba6_power_stat,1396,0,3)
GEN_SHOW(elba7_power_stat,1404,0,3)
GEN_SHOW(th4_power_ctrl,1408,0,7)
GEN_STORE(th4_power_ctrl,1408,0,7)
GEN_SHOW(th4_power_stat,1412,0,2)
GEN_STORE(th4_power_stat,1412,0,2)
GEN_SHOW(th4_pci_reset,1416,0,0)
GEN_STORE(th4_pci_reset,1416,0,0)
GEN_SHOW(th4_sys_reset,1416,1,1)
GEN_STORE(th4_sys_reset,1416,1,1)
GEN_SHOW(wdog_ctrl_reg,1448,0,31)
GEN_STORE(wdog_ctrl_reg,1448,0,31)
GEN_SHOW(wdog_reset_reg,1452,0,7)
GEN_STORE(wdog_reset_reg,1452,0,7)
GEN_SHOW(th4_ctrl_reg,1416,0,1)
GEN_STORE(th4_ctrl_reg,1416,0,1)


static DEVICE_ATTR(fpga_id,S_IRUGO,fpga_id_show,NULL);
static DEVICE_ATTR(fpga_rev,S_IRUGO,fpga_rev_show,NULL);
static DEVICE_ATTR(board_rev,S_IRUGO,board_rev_show,NULL);
static DEVICE_ATTR(reset_cause_0,S_IRUGO,reset_cause_0_show,NULL);
static DEVICE_ATTR(reset_cause_1,S_IRUGO,reset_cause_1_show,NULL);
static DEVICE_ATTR(reset_cause_2,S_IRUGO,reset_cause_2_show,NULL);
static DEVICE_ATTR(reset_cause_3,S_IRUGO,reset_cause_3_show,NULL);
static DEVICE_ATTR(reset_cause_4,S_IRUGO,reset_cause_4_show,NULL);
static DEVICE_ATTR(reset_cause_5,S_IRUGO,reset_cause_5_show,NULL);
static DEVICE_ATTR(reset_cause_6,S_IRUGO,reset_cause_6_show,NULL);
static DEVICE_ATTR(reset_cause_7,S_IRUGO,reset_cause_7_show,NULL);
static DEVICE_ATTR(qsfp0_absent,S_IRUGO,qsfp0_absent_show,NULL);
static DEVICE_ATTR(qsfp0_int_pending,S_IRUGO,qsfp0_int_pending_show,NULL);
static DEVICE_ATTR(qsfp1_absent,S_IRUGO,qsfp1_absent_show,NULL);
static DEVICE_ATTR(qsfp1_int_pending,S_IRUGO,qsfp1_int_pending_show,NULL);
static DEVICE_ATTR(qsfp2_absent,S_IRUGO,qsfp2_absent_show,NULL);
static DEVICE_ATTR(qsfp2_int_pending,S_IRUGO,qsfp2_int_pending_show,NULL);
static DEVICE_ATTR(qsfp3_absent,S_IRUGO,qsfp3_absent_show,NULL);
static DEVICE_ATTR(qsfp3_int_pending,S_IRUGO,qsfp3_int_pending_show,NULL);
static DEVICE_ATTR(qsfp4_absent,S_IRUGO,qsfp4_absent_show,NULL);
static DEVICE_ATTR(qsfp4_int_pending,S_IRUGO,qsfp4_int_pending_show,NULL);
static DEVICE_ATTR(qsfp5_absent,S_IRUGO,qsfp5_absent_show,NULL);
static DEVICE_ATTR(qsfp5_int_pending,S_IRUGO,qsfp5_int_pending_show,NULL);
static DEVICE_ATTR(qsfp6_absent,S_IRUGO,qsfp6_absent_show,NULL);
static DEVICE_ATTR(qsfp6_int_pending,S_IRUGO,qsfp6_int_pending_show,NULL);
static DEVICE_ATTR(qsfp7_absent,S_IRUGO,qsfp7_absent_show,NULL);
static DEVICE_ATTR(qsfp7_int_pending,S_IRUGO,qsfp7_int_pending_show,NULL);
static DEVICE_ATTR(qsfp8_absent,S_IRUGO,qsfp8_absent_show,NULL);
static DEVICE_ATTR(qsfp8_int_pending,S_IRUGO,qsfp8_int_pending_show,NULL);
static DEVICE_ATTR(qsfp9_absent,S_IRUGO,qsfp9_absent_show,NULL);
static DEVICE_ATTR(qsfp9_int_pending,S_IRUGO,qsfp9_int_pending_show,NULL);
static DEVICE_ATTR(qsfp10_absent,S_IRUGO,qsfp10_absent_show,NULL);
static DEVICE_ATTR(qsfp10_int_pending,S_IRUGO,qsfp10_int_pending_show,NULL);
static DEVICE_ATTR(qsfp11_absent,S_IRUGO,qsfp11_absent_show,NULL);
static DEVICE_ATTR(qsfp11_int_pending,S_IRUGO,qsfp11_int_pending_show,NULL);
static DEVICE_ATTR(qsfp12_absent,S_IRUGO,qsfp12_absent_show,NULL);
static DEVICE_ATTR(qsfp12_int_pending,S_IRUGO,qsfp12_int_pending_show,NULL);
static DEVICE_ATTR(qsfp13_absent,S_IRUGO,qsfp13_absent_show,NULL);
static DEVICE_ATTR(qsfp13_int_pending,S_IRUGO,qsfp13_int_pending_show,NULL);
static DEVICE_ATTR(qsfp14_absent,S_IRUGO,qsfp14_absent_show,NULL);
static DEVICE_ATTR(qsfp14_int_pending,S_IRUGO,qsfp14_int_pending_show,NULL);
static DEVICE_ATTR(qsfp15_absent,S_IRUGO,qsfp15_absent_show,NULL);
static DEVICE_ATTR(qsfp15_int_pending,S_IRUGO,qsfp15_int_pending_show,NULL);
static DEVICE_ATTR(qsfp16_absent,S_IRUGO,qsfp16_absent_show,NULL);
static DEVICE_ATTR(qsfp16_int_pending,S_IRUGO,qsfp16_int_pending_show,NULL);
static DEVICE_ATTR(qsfp17_absent,S_IRUGO,qsfp17_absent_show,NULL);
static DEVICE_ATTR(qsfp17_int_pending,S_IRUGO,qsfp17_int_pending_show,NULL);
static DEVICE_ATTR(qsfp18_absent,S_IRUGO,qsfp18_absent_show,NULL);
static DEVICE_ATTR(qsfp18_int_pending,S_IRUGO,qsfp18_int_pending_show,NULL);
static DEVICE_ATTR(qsfp19_absent,S_IRUGO,qsfp19_absent_show,NULL);
static DEVICE_ATTR(qsfp19_int_pending,S_IRUGO,qsfp19_int_pending_show,NULL);
static DEVICE_ATTR(qsfp20_absent,S_IRUGO,qsfp20_absent_show,NULL);
static DEVICE_ATTR(qsfp20_int_pending,S_IRUGO,qsfp20_int_pending_show,NULL);
static DEVICE_ATTR(qsfp21_absent,S_IRUGO,qsfp21_absent_show,NULL);
static DEVICE_ATTR(qsfp21_int_pending,S_IRUGO,qsfp21_int_pending_show,NULL);
static DEVICE_ATTR(qsfp22_absent,S_IRUGO,qsfp22_absent_show,NULL);
static DEVICE_ATTR(qsfp22_int_pending,S_IRUGO,qsfp22_int_pending_show,NULL);
static DEVICE_ATTR(qsfp23_absent,S_IRUGO,qsfp23_absent_show,NULL);
static DEVICE_ATTR(qsfp23_int_pending,S_IRUGO,qsfp23_int_pending_show,NULL);
static DEVICE_ATTR(qsfp24_absent,S_IRUGO,qsfp24_absent_show,NULL);
static DEVICE_ATTR(qsfp24_int_pending,S_IRUGO,qsfp24_int_pending_show,NULL);
static DEVICE_ATTR(qsfp25_absent,S_IRUGO,qsfp25_absent_show,NULL);
static DEVICE_ATTR(qsfp25_int_pending,S_IRUGO,qsfp25_int_pending_show,NULL);
static DEVICE_ATTR(qsfp26_absent,S_IRUGO,qsfp26_absent_show,NULL);
static DEVICE_ATTR(qsfp26_int_pending,S_IRUGO,qsfp26_int_pending_show,NULL);
static DEVICE_ATTR(qsfp27_absent,S_IRUGO,qsfp27_absent_show,NULL);
static DEVICE_ATTR(qsfp27_int_pending,S_IRUGO,qsfp27_int_pending_show,NULL);
static DEVICE_ATTR(psu1_present,S_IRUGO,psu1_present_show,NULL);
static DEVICE_ATTR(psu1_alert,S_IRUGO,psu1_alert_show,NULL);
static DEVICE_ATTR(psu1_power_ok,S_IRUGO,psu1_power_ok_show,NULL);
static DEVICE_ATTR(psu2_present,S_IRUGO,psu2_present_show,NULL);
static DEVICE_ATTR(psu2_alert,S_IRUGO,psu2_alert_show,NULL);
static DEVICE_ATTR(psu2_power_ok,S_IRUGO,psu2_power_ok_show,NULL);
static DEVICE_ATTR(fan0_present,S_IRUGO,fan0_present_show,NULL);
static DEVICE_ATTR(fan1_present,S_IRUGO,fan1_present_show,NULL);
static DEVICE_ATTR(fan2_present,S_IRUGO,fan2_present_show,NULL);
static DEVICE_ATTR(fan3_present,S_IRUGO,fan3_present_show,NULL);
static DEVICE_ATTR(fan0_direction,S_IRUGO,fan0_direction_show,NULL);
static DEVICE_ATTR(fan1_direction,S_IRUGO,fan1_direction_show,NULL);
static DEVICE_ATTR(fan2_direction,S_IRUGO,fan2_direction_show,NULL);
static DEVICE_ATTR(fan3_direction,S_IRUGO,fan3_direction_show,NULL);
static DEVICE_ATTR(fan0_hw_rev,S_IRUGO,fan0_hw_rev_show,NULL);
static DEVICE_ATTR(fan1_hw_rev,S_IRUGO,fan1_hw_rev_show,NULL);
static DEVICE_ATTR(fan2_hw_rev,S_IRUGO,fan2_hw_rev_show,NULL);
static DEVICE_ATTR(fan3_hw_rev,S_IRUGO,fan3_hw_rev_show,NULL);
static DEVICE_ATTR(fan0_alert,S_IRUGO,fan0_alert_show,NULL);
static DEVICE_ATTR(fan1_alert,S_IRUGO,fan1_alert_show,NULL);
static DEVICE_ATTR(fan2_alert,S_IRUGO,fan2_alert_show,NULL);
static DEVICE_ATTR(fan3_alert,S_IRUGO,fan3_alert_show,NULL);
static DEVICE_ATTR(fan0_error,S_IRUGO,fan0_error_show,NULL);
static DEVICE_ATTR(fan1_error,S_IRUGO,fan1_error_show,NULL);
static DEVICE_ATTR(fan2_error,S_IRUGO,fan2_error_show,NULL);
static DEVICE_ATTR(fan3_error,S_IRUGO,fan3_error_show,NULL);
static DEVICE_ATTR(fan0_inlet,S_IRUGO,fan0_inlet_show,NULL);
static DEVICE_ATTR(fan0_outlet,S_IRUGO,fan0_outlet_show,NULL);
static DEVICE_ATTR(fan1_inlet,S_IRUGO,fan1_inlet_show,NULL);
static DEVICE_ATTR(fan1_outlet,S_IRUGO,fan1_outlet_show,NULL);
static DEVICE_ATTR(fan2_inlet,S_IRUGO,fan2_inlet_show,NULL);
static DEVICE_ATTR(fan2_outlet,S_IRUGO,fan2_outlet_show,NULL);
static DEVICE_ATTR(fan3_inlet,S_IRUGO,fan3_inlet_show,NULL);
static DEVICE_ATTR(fan3_outlet,S_IRUGO,fan3_outlet_show,NULL);
static DEVICE_ATTR(elba0_power_stat,S_IRUGO,elba0_power_stat_show,NULL);
static DEVICE_ATTR(elba1_power_stat,S_IRUGO,elba1_power_stat_show,NULL);
static DEVICE_ATTR(elba2_power_stat,S_IRUGO,elba2_power_stat_show,NULL);
static DEVICE_ATTR(elba3_power_stat,S_IRUGO,elba3_power_stat_show,NULL);
static DEVICE_ATTR(elba4_power_stat,S_IRUGO,elba4_power_stat_show,NULL);
static DEVICE_ATTR(elba5_power_stat,S_IRUGO,elba5_power_stat_show,NULL);
static DEVICE_ATTR(elba6_power_stat,S_IRUGO,elba6_power_stat_show,NULL);
static DEVICE_ATTR(elba7_power_stat,S_IRUGO,elba7_power_stat_show,NULL);
static DEVICE_ATTR(soft_i2c_spi_reset,S_IWUSR,NULL,soft_i2c_spi_reset_store);
static DEVICE_ATTR(protect_golden_bios,S_IRUGO|S_IWUSR,protect_golden_bios_show,protect_golden_bios_store);
static DEVICE_ATTR(protect_primary_bios,S_IRUGO|S_IWUSR,protect_primary_bios_show,protect_primary_bios_store);
static DEVICE_ATTR(protect_nic_flash,S_IRUGO|S_IWUSR,protect_nic_flash_show,protect_nic_flash_store);
static DEVICE_ATTR(protect_fru_eeprom,S_IRUGO|S_IWUSR,protect_fru_eeprom_show,protect_fru_eeprom_store);
static DEVICE_ATTR(protect_fpga1_cfg_spi,S_IRUGO|S_IWUSR,protect_fpga1_cfg_spi_show,protect_fpga1_cfg_spi_store);
static DEVICE_ATTR(protect_fpga0_cfg_spi,S_IRUGO|S_IWUSR,protect_fpga0_cfg_spi_show,protect_fpga0_cfg_spi_store);
static DEVICE_ATTR(protect_th4_qspi,S_IRUGO|S_IWUSR,protect_th4_qspi_show,protect_th4_qspi_store);
static DEVICE_ATTR(protect_elba_qspi,S_IRUGO|S_IWUSR,protect_elba_qspi_show,protect_elba_qspi_store);
static DEVICE_ATTR(protect_ccpld_acc,S_IRUGO|S_IWUSR,protect_ccpld_acc_show,protect_ccpld_acc_store);
static DEVICE_ATTR(led_brightness,S_IRUGO|S_IWUSR,led_brightness_show,led_brightness_store);
static DEVICE_ATTR(led_slow_blink_speed,S_IRUGO|S_IWUSR,led_slow_blink_speed_show,led_slow_blink_speed_store);
static DEVICE_ATTR(led_fast_blink_speed,S_IRUGO|S_IWUSR,led_fast_blink_speed_show,led_fast_blink_speed_store);
static DEVICE_ATTR(led_syshealth,S_IRUGO|S_IWUSR,led_syshealth_show,led_syshealth_store);
static DEVICE_ATTR(led_chassis,S_IRUGO|S_IWUSR,led_chassis_show,led_chassis_store);
static DEVICE_ATTR(led_uid_blue,S_IRUGO|S_IWUSR,led_uid_blue_show,led_uid_blue_store);
static DEVICE_ATTR(led_fan0,S_IRUGO|S_IWUSR,led_fan0_show,led_fan0_store);
static DEVICE_ATTR(led_fan1,S_IRUGO|S_IWUSR,led_fan1_show,led_fan1_store);
static DEVICE_ATTR(led_fan2,S_IRUGO|S_IWUSR,led_fan2_show,led_fan2_store);
static DEVICE_ATTR(led_fan3,S_IRUGO|S_IWUSR,led_fan3_show,led_fan3_store);
static DEVICE_ATTR(led_chip_port0,S_IRUGO|S_IWUSR,led_chip_port0_show,led_chip_port0_store);
static DEVICE_ATTR(led_chip_port1,S_IRUGO|S_IWUSR,led_chip_port1_show,led_chip_port1_store);
static DEVICE_ATTR(led_chip_port2,S_IRUGO|S_IWUSR,led_chip_port2_show,led_chip_port2_store);
static DEVICE_ATTR(led_chip_port3,S_IRUGO|S_IWUSR,led_chip_port3_show,led_chip_port3_store);
static DEVICE_ATTR(led_chip_port4,S_IRUGO|S_IWUSR,led_chip_port4_show,led_chip_port4_store);
static DEVICE_ATTR(led_chip_port5,S_IRUGO|S_IWUSR,led_chip_port5_show,led_chip_port5_store);
static DEVICE_ATTR(led_chip_port6,S_IRUGO|S_IWUSR,led_chip_port6_show,led_chip_port6_store);
static DEVICE_ATTR(led_chip_port7,S_IRUGO|S_IWUSR,led_chip_port7_show,led_chip_port7_store);
static DEVICE_ATTR(led_chip_port8,S_IRUGO|S_IWUSR,led_chip_port8_show,led_chip_port8_store);
static DEVICE_ATTR(led_chip_port9,S_IRUGO|S_IWUSR,led_chip_port9_show,led_chip_port9_store);
static DEVICE_ATTR(led_chip_port10,S_IRUGO|S_IWUSR,led_chip_port10_show,led_chip_port10_store);
static DEVICE_ATTR(led_chip_port11,S_IRUGO|S_IWUSR,led_chip_port11_show,led_chip_port11_store);
static DEVICE_ATTR(led_chip_port12,S_IRUGO|S_IWUSR,led_chip_port12_show,led_chip_port12_store);
static DEVICE_ATTR(led_chip_port13,S_IRUGO|S_IWUSR,led_chip_port13_show,led_chip_port13_store);
static DEVICE_ATTR(led_chip_port14,S_IRUGO|S_IWUSR,led_chip_port14_show,led_chip_port14_store);
static DEVICE_ATTR(led_chip_port15,S_IRUGO|S_IWUSR,led_chip_port15_show,led_chip_port15_store);
static DEVICE_ATTR(led_chip_port16,S_IRUGO|S_IWUSR,led_chip_port16_show,led_chip_port16_store);
static DEVICE_ATTR(led_chip_port17,S_IRUGO|S_IWUSR,led_chip_port17_show,led_chip_port17_store);
static DEVICE_ATTR(led_chip_port18,S_IRUGO|S_IWUSR,led_chip_port18_show,led_chip_port18_store);
static DEVICE_ATTR(led_chip_port19,S_IRUGO|S_IWUSR,led_chip_port19_show,led_chip_port19_store);
static DEVICE_ATTR(led_chip_port20,S_IRUGO|S_IWUSR,led_chip_port20_show,led_chip_port20_store);
static DEVICE_ATTR(led_chip_port21,S_IRUGO|S_IWUSR,led_chip_port21_show,led_chip_port21_store);
static DEVICE_ATTR(led_chip_port22,S_IRUGO|S_IWUSR,led_chip_port22_show,led_chip_port22_store);
static DEVICE_ATTR(led_chip_port23,S_IRUGO|S_IWUSR,led_chip_port23_show,led_chip_port23_store);
static DEVICE_ATTR(led_chip_port24,S_IRUGO|S_IWUSR,led_chip_port24_show,led_chip_port24_store);
static DEVICE_ATTR(led_chip_port25,S_IRUGO|S_IWUSR,led_chip_port25_show,led_chip_port25_store);
static DEVICE_ATTR(led_chip_port26,S_IRUGO|S_IWUSR,led_chip_port26_show,led_chip_port26_store);
static DEVICE_ATTR(led_chip_port27,S_IRUGO|S_IWUSR,led_chip_port27_show,led_chip_port27_store);
static DEVICE_ATTR(qsfp0_reset,S_IRUGO|S_IWUSR,qsfp0_reset_show,qsfp0_reset_store);
static DEVICE_ATTR(qsfp0_low_power_mode,S_IRUGO|S_IWUSR,qsfp0_low_power_mode_show,qsfp0_low_power_mode_store);
static DEVICE_ATTR(qsfp1_reset,S_IRUGO|S_IWUSR,qsfp1_reset_show,qsfp1_reset_store);
static DEVICE_ATTR(qsfp1_low_power_mode,S_IRUGO|S_IWUSR,qsfp1_low_power_mode_show,qsfp1_low_power_mode_store);
static DEVICE_ATTR(qsfp2_reset,S_IRUGO|S_IWUSR,qsfp2_reset_show,qsfp2_reset_store);
static DEVICE_ATTR(qsfp2_low_power_mode,S_IRUGO|S_IWUSR,qsfp2_low_power_mode_show,qsfp2_low_power_mode_store);
static DEVICE_ATTR(qsfp3_reset,S_IRUGO|S_IWUSR,qsfp3_reset_show,qsfp3_reset_store);
static DEVICE_ATTR(qsfp3_low_power_mode,S_IRUGO|S_IWUSR,qsfp3_low_power_mode_show,qsfp3_low_power_mode_store);
static DEVICE_ATTR(qsfp4_reset,S_IRUGO|S_IWUSR,qsfp4_reset_show,qsfp4_reset_store);
static DEVICE_ATTR(qsfp4_low_power_mode,S_IRUGO|S_IWUSR,qsfp4_low_power_mode_show,qsfp4_low_power_mode_store);
static DEVICE_ATTR(qsfp5_reset,S_IRUGO|S_IWUSR,qsfp5_reset_show,qsfp5_reset_store);
static DEVICE_ATTR(qsfp5_low_power_mode,S_IRUGO|S_IWUSR,qsfp5_low_power_mode_show,qsfp5_low_power_mode_store);
static DEVICE_ATTR(qsfp6_reset,S_IRUGO|S_IWUSR,qsfp6_reset_show,qsfp6_reset_store);
static DEVICE_ATTR(qsfp6_low_power_mode,S_IRUGO|S_IWUSR,qsfp6_low_power_mode_show,qsfp6_low_power_mode_store);
static DEVICE_ATTR(qsfp7_reset,S_IRUGO|S_IWUSR,qsfp7_reset_show,qsfp7_reset_store);
static DEVICE_ATTR(qsfp7_low_power_mode,S_IRUGO|S_IWUSR,qsfp7_low_power_mode_show,qsfp7_low_power_mode_store);
static DEVICE_ATTR(qsfp8_reset,S_IRUGO|S_IWUSR,qsfp8_reset_show,qsfp8_reset_store);
static DEVICE_ATTR(qsfp8_low_power_mode,S_IRUGO|S_IWUSR,qsfp8_low_power_mode_show,qsfp8_low_power_mode_store);
static DEVICE_ATTR(qsfp9_reset,S_IRUGO|S_IWUSR,qsfp9_reset_show,qsfp9_reset_store);
static DEVICE_ATTR(qsfp9_low_power_mode,S_IRUGO|S_IWUSR,qsfp9_low_power_mode_show,qsfp9_low_power_mode_store);
static DEVICE_ATTR(qsfp10_reset,S_IRUGO|S_IWUSR,qsfp10_reset_show,qsfp10_reset_store);
static DEVICE_ATTR(qsfp10_low_power_mode,S_IRUGO|S_IWUSR,qsfp10_low_power_mode_show,qsfp10_low_power_mode_store);
static DEVICE_ATTR(qsfp11_reset,S_IRUGO|S_IWUSR,qsfp11_reset_show,qsfp11_reset_store);
static DEVICE_ATTR(qsfp11_low_power_mode,S_IRUGO|S_IWUSR,qsfp11_low_power_mode_show,qsfp11_low_power_mode_store);
static DEVICE_ATTR(qsfp12_reset,S_IRUGO|S_IWUSR,qsfp12_reset_show,qsfp12_reset_store);
static DEVICE_ATTR(qsfp12_low_power_mode,S_IRUGO|S_IWUSR,qsfp12_low_power_mode_show,qsfp12_low_power_mode_store);
static DEVICE_ATTR(qsfp13_reset,S_IRUGO|S_IWUSR,qsfp13_reset_show,qsfp13_reset_store);
static DEVICE_ATTR(qsfp13_low_power_mode,S_IRUGO|S_IWUSR,qsfp13_low_power_mode_show,qsfp13_low_power_mode_store);
static DEVICE_ATTR(qsfp14_reset,S_IRUGO|S_IWUSR,qsfp14_reset_show,qsfp14_reset_store);
static DEVICE_ATTR(qsfp14_low_power_mode,S_IRUGO|S_IWUSR,qsfp14_low_power_mode_show,qsfp14_low_power_mode_store);
static DEVICE_ATTR(qsfp15_reset,S_IRUGO|S_IWUSR,qsfp15_reset_show,qsfp15_reset_store);
static DEVICE_ATTR(qsfp15_low_power_mode,S_IRUGO|S_IWUSR,qsfp15_low_power_mode_show,qsfp15_low_power_mode_store);
static DEVICE_ATTR(qsfp16_reset,S_IRUGO|S_IWUSR,qsfp16_reset_show,qsfp16_reset_store);
static DEVICE_ATTR(qsfp16_low_power_mode,S_IRUGO|S_IWUSR,qsfp16_low_power_mode_show,qsfp16_low_power_mode_store);
static DEVICE_ATTR(qsfp17_reset,S_IRUGO|S_IWUSR,qsfp17_reset_show,qsfp17_reset_store);
static DEVICE_ATTR(qsfp17_low_power_mode,S_IRUGO|S_IWUSR,qsfp17_low_power_mode_show,qsfp17_low_power_mode_store);
static DEVICE_ATTR(qsfp18_reset,S_IRUGO|S_IWUSR,qsfp18_reset_show,qsfp18_reset_store);
static DEVICE_ATTR(qsfp18_low_power_mode,S_IRUGO|S_IWUSR,qsfp18_low_power_mode_show,qsfp18_low_power_mode_store);
static DEVICE_ATTR(qsfp19_reset,S_IRUGO|S_IWUSR,qsfp19_reset_show,qsfp19_reset_store);
static DEVICE_ATTR(qsfp19_low_power_mode,S_IRUGO|S_IWUSR,qsfp19_low_power_mode_show,qsfp19_low_power_mode_store);
static DEVICE_ATTR(qsfp20_reset,S_IRUGO|S_IWUSR,qsfp20_reset_show,qsfp20_reset_store);
static DEVICE_ATTR(qsfp20_low_power_mode,S_IRUGO|S_IWUSR,qsfp20_low_power_mode_show,qsfp20_low_power_mode_store);
static DEVICE_ATTR(qsfp21_reset,S_IRUGO|S_IWUSR,qsfp21_reset_show,qsfp21_reset_store);
static DEVICE_ATTR(qsfp21_low_power_mode,S_IRUGO|S_IWUSR,qsfp21_low_power_mode_show,qsfp21_low_power_mode_store);
static DEVICE_ATTR(qsfp22_reset,S_IRUGO|S_IWUSR,qsfp22_reset_show,qsfp22_reset_store);
static DEVICE_ATTR(qsfp22_low_power_mode,S_IRUGO|S_IWUSR,qsfp22_low_power_mode_show,qsfp22_low_power_mode_store);
static DEVICE_ATTR(qsfp23_reset,S_IRUGO|S_IWUSR,qsfp23_reset_show,qsfp23_reset_store);
static DEVICE_ATTR(qsfp23_low_power_mode,S_IRUGO|S_IWUSR,qsfp23_low_power_mode_show,qsfp23_low_power_mode_store);
static DEVICE_ATTR(qsfp24_reset,S_IRUGO|S_IWUSR,qsfp24_reset_show,qsfp24_reset_store);
static DEVICE_ATTR(qsfp24_low_power_mode,S_IRUGO|S_IWUSR,qsfp24_low_power_mode_show,qsfp24_low_power_mode_store);
static DEVICE_ATTR(qsfp25_reset,S_IRUGO|S_IWUSR,qsfp25_reset_show,qsfp25_reset_store);
static DEVICE_ATTR(qsfp25_low_power_mode,S_IRUGO|S_IWUSR,qsfp25_low_power_mode_show,qsfp25_low_power_mode_store);
static DEVICE_ATTR(qsfp26_reset,S_IRUGO|S_IWUSR,qsfp26_reset_show,qsfp26_reset_store);
static DEVICE_ATTR(qsfp26_low_power_mode,S_IRUGO|S_IWUSR,qsfp26_low_power_mode_show,qsfp26_low_power_mode_store);
static DEVICE_ATTR(qsfp27_reset,S_IRUGO|S_IWUSR,qsfp27_reset_show,qsfp27_reset_store);
static DEVICE_ATTR(qsfp27_low_power_mode,S_IRUGO|S_IWUSR,qsfp27_low_power_mode_show,qsfp27_low_power_mode_store);
static DEVICE_ATTR(psu1_ctrl,S_IRUGO|S_IWUSR,psu1_ctrl_show,psu1_ctrl_store);
static DEVICE_ATTR(psu2_ctrl,S_IRUGO|S_IWUSR,psu2_ctrl_show,psu2_ctrl_store);
static DEVICE_ATTR(fan0_power_enable,S_IRUGO|S_IWUSR,fan0_power_enable_show,fan0_power_enable_store);
static DEVICE_ATTR(fan1_power_enable,S_IRUGO|S_IWUSR,fan1_power_enable_show,fan1_power_enable_store);
static DEVICE_ATTR(fan2_power_enable,S_IRUGO|S_IWUSR,fan2_power_enable_show,fan2_power_enable_store);
static DEVICE_ATTR(fan3_power_enable,S_IRUGO|S_IWUSR,fan3_power_enable_show,fan3_power_enable_store);
static DEVICE_ATTR(fan0_pwn_ctrl,S_IRUGO|S_IWUSR,fan0_pwn_ctrl_show,fan0_pwn_ctrl_store);
static DEVICE_ATTR(fan1_pwn_ctrl,S_IRUGO|S_IWUSR,fan1_pwn_ctrl_show,fan1_pwn_ctrl_store);
static DEVICE_ATTR(fan2_pwn_ctrl,S_IRUGO|S_IWUSR,fan2_pwn_ctrl_show,fan2_pwn_ctrl_store);
static DEVICE_ATTR(fan3_pwn_ctrl,S_IRUGO|S_IWUSR,fan3_pwn_ctrl_show,fan3_pwn_ctrl_store);
static DEVICE_ATTR(elba0_power_ctrl,S_IRUGO|S_IWUSR,elba0_power_ctrl_show,elba0_power_ctrl_store);
static DEVICE_ATTR(elba1_power_ctrl,S_IRUGO|S_IWUSR,elba1_power_ctrl_show,elba1_power_ctrl_store);
static DEVICE_ATTR(elba2_power_ctrl,S_IRUGO|S_IWUSR,elba2_power_ctrl_show,elba2_power_ctrl_store);
static DEVICE_ATTR(elba3_power_ctrl,S_IRUGO|S_IWUSR,elba3_power_ctrl_show,elba3_power_ctrl_store);
static DEVICE_ATTR(elba4_power_ctrl,S_IRUGO|S_IWUSR,elba4_power_ctrl_show,elba4_power_ctrl_store);
static DEVICE_ATTR(elba5_power_ctrl,S_IRUGO|S_IWUSR,elba5_power_ctrl_show,elba5_power_ctrl_store);
static DEVICE_ATTR(elba6_power_ctrl,S_IRUGO|S_IWUSR,elba6_power_ctrl_show,elba6_power_ctrl_store);
static DEVICE_ATTR(elba7_power_ctrl,S_IRUGO|S_IWUSR,elba7_power_ctrl_show,elba7_power_ctrl_store);
static DEVICE_ATTR(th4_power_ctrl,S_IRUGO|S_IWUSR,th4_power_ctrl_show,th4_power_ctrl_store);
static DEVICE_ATTR(th4_power_stat,S_IRUGO|S_IWUSR,th4_power_stat_show,th4_power_stat_store);
static DEVICE_ATTR(th4_pci_reset,S_IRUGO|S_IWUSR,th4_pci_reset_show,th4_pci_reset_store);
static DEVICE_ATTR(th4_sys_reset,S_IRUGO|S_IWUSR,th4_sys_reset_show,th4_sys_reset_store);
static DEVICE_ATTR(wdog_ctrl_reg,S_IRUGO|S_IWUSR,wdog_ctrl_reg_show,wdog_ctrl_reg_store);
static DEVICE_ATTR(wdog_reset_reg,S_IRUGO|S_IWUSR,wdog_reset_reg_show,wdog_reset_reg_store);
static DEVICE_ATTR(th4_ctrl_reg,S_IRUGO|S_IWUSR,th4_ctrl_reg_show,th4_ctrl_reg_store);

static struct attribute *fpga_attrs[] = {
    &dev_attr_fpga_id.attr,
    &dev_attr_fpga_rev.attr,
    &dev_attr_board_rev.attr,
    &dev_attr_reset_cause_0.attr,
    &dev_attr_reset_cause_1.attr,
    &dev_attr_reset_cause_2.attr,
    &dev_attr_reset_cause_3.attr,
    &dev_attr_reset_cause_4.attr,
    &dev_attr_reset_cause_5.attr,
    &dev_attr_reset_cause_6.attr,
    &dev_attr_reset_cause_7.attr,
    &dev_attr_soft_i2c_spi_reset.attr,
    &dev_attr_protect_golden_bios.attr,
    &dev_attr_protect_primary_bios.attr,
    &dev_attr_protect_nic_flash.attr,
    &dev_attr_protect_fru_eeprom.attr,
    &dev_attr_protect_fpga1_cfg_spi.attr,
    &dev_attr_protect_fpga0_cfg_spi.attr,
    &dev_attr_protect_th4_qspi.attr,
    &dev_attr_protect_elba_qspi.attr,
    &dev_attr_protect_ccpld_acc.attr,
    &dev_attr_led_brightness.attr,
    &dev_attr_led_slow_blink_speed.attr,
    &dev_attr_led_fast_blink_speed.attr,
    &dev_attr_led_syshealth.attr,
    &dev_attr_led_chassis.attr,
    &dev_attr_led_uid_blue.attr,
    &dev_attr_led_fan0.attr,
    &dev_attr_led_fan1.attr,
    &dev_attr_led_fan2.attr,
    &dev_attr_led_fan3.attr,
    &dev_attr_led_chip_port0.attr,
    &dev_attr_led_chip_port1.attr,
    &dev_attr_led_chip_port2.attr,
    &dev_attr_led_chip_port3.attr,
    &dev_attr_led_chip_port4.attr,
    &dev_attr_led_chip_port5.attr,
    &dev_attr_led_chip_port6.attr,
    &dev_attr_led_chip_port7.attr,
    &dev_attr_led_chip_port8.attr,
    &dev_attr_led_chip_port9.attr,
    &dev_attr_led_chip_port10.attr,
    &dev_attr_led_chip_port11.attr,
    &dev_attr_led_chip_port12.attr,
    &dev_attr_led_chip_port13.attr,
    &dev_attr_led_chip_port14.attr,
    &dev_attr_led_chip_port15.attr,
    &dev_attr_led_chip_port16.attr,
    &dev_attr_led_chip_port17.attr,
    &dev_attr_led_chip_port18.attr,
    &dev_attr_led_chip_port19.attr,
    &dev_attr_led_chip_port20.attr,
    &dev_attr_led_chip_port21.attr,
    &dev_attr_led_chip_port22.attr,
    &dev_attr_led_chip_port23.attr,
    &dev_attr_led_chip_port24.attr,
    &dev_attr_led_chip_port25.attr,
    &dev_attr_led_chip_port26.attr,
    &dev_attr_led_chip_port27.attr,
    &dev_attr_qsfp0_absent.attr,
    &dev_attr_qsfp0_int_pending.attr,
    &dev_attr_qsfp1_absent.attr,
    &dev_attr_qsfp1_int_pending.attr,
    &dev_attr_qsfp2_absent.attr,
    &dev_attr_qsfp2_int_pending.attr,
    &dev_attr_qsfp3_absent.attr,
    &dev_attr_qsfp3_int_pending.attr,
    &dev_attr_qsfp4_absent.attr,
    &dev_attr_qsfp4_int_pending.attr,
    &dev_attr_qsfp5_absent.attr,
    &dev_attr_qsfp5_int_pending.attr,
    &dev_attr_qsfp6_absent.attr,
    &dev_attr_qsfp6_int_pending.attr,
    &dev_attr_qsfp7_absent.attr,
    &dev_attr_qsfp7_int_pending.attr,
    &dev_attr_qsfp8_absent.attr,
    &dev_attr_qsfp8_int_pending.attr,
    &dev_attr_qsfp9_absent.attr,
    &dev_attr_qsfp9_int_pending.attr,
    &dev_attr_qsfp10_absent.attr,
    &dev_attr_qsfp10_int_pending.attr,
    &dev_attr_qsfp11_absent.attr,
    &dev_attr_qsfp11_int_pending.attr,
    &dev_attr_qsfp12_absent.attr,
    &dev_attr_qsfp12_int_pending.attr,
    &dev_attr_qsfp13_absent.attr,
    &dev_attr_qsfp13_int_pending.attr,
    &dev_attr_qsfp14_absent.attr,
    &dev_attr_qsfp14_int_pending.attr,
    &dev_attr_qsfp15_absent.attr,
    &dev_attr_qsfp15_int_pending.attr,
    &dev_attr_qsfp16_absent.attr,
    &dev_attr_qsfp16_int_pending.attr,
    &dev_attr_qsfp17_absent.attr,
    &dev_attr_qsfp17_int_pending.attr,
    &dev_attr_qsfp18_absent.attr,
    &dev_attr_qsfp18_int_pending.attr,
    &dev_attr_qsfp19_absent.attr,
    &dev_attr_qsfp19_int_pending.attr,
    &dev_attr_qsfp20_absent.attr,
    &dev_attr_qsfp20_int_pending.attr,
    &dev_attr_qsfp21_absent.attr,
    &dev_attr_qsfp21_int_pending.attr,
    &dev_attr_qsfp22_absent.attr,
    &dev_attr_qsfp22_int_pending.attr,
    &dev_attr_qsfp23_absent.attr,
    &dev_attr_qsfp23_int_pending.attr,
    &dev_attr_qsfp24_absent.attr,
    &dev_attr_qsfp24_int_pending.attr,
    &dev_attr_qsfp25_absent.attr,
    &dev_attr_qsfp25_int_pending.attr,
    &dev_attr_qsfp26_absent.attr,
    &dev_attr_qsfp26_int_pending.attr,
    &dev_attr_qsfp27_absent.attr,
    &dev_attr_qsfp27_int_pending.attr,
    &dev_attr_qsfp0_reset.attr,
    &dev_attr_qsfp0_low_power_mode.attr,
    &dev_attr_qsfp1_reset.attr,
    &dev_attr_qsfp1_low_power_mode.attr,
    &dev_attr_qsfp2_reset.attr,
    &dev_attr_qsfp2_low_power_mode.attr,
    &dev_attr_qsfp3_reset.attr,
    &dev_attr_qsfp3_low_power_mode.attr,
    &dev_attr_qsfp4_reset.attr,
    &dev_attr_qsfp4_low_power_mode.attr,
    &dev_attr_qsfp5_reset.attr,
    &dev_attr_qsfp5_low_power_mode.attr,
    &dev_attr_qsfp6_reset.attr,
    &dev_attr_qsfp6_low_power_mode.attr,
    &dev_attr_qsfp7_reset.attr,
    &dev_attr_qsfp7_low_power_mode.attr,
    &dev_attr_qsfp8_reset.attr,
    &dev_attr_qsfp8_low_power_mode.attr,
    &dev_attr_qsfp9_reset.attr,
    &dev_attr_qsfp9_low_power_mode.attr,
    &dev_attr_qsfp10_reset.attr,
    &dev_attr_qsfp10_low_power_mode.attr,
    &dev_attr_qsfp11_reset.attr,
    &dev_attr_qsfp11_low_power_mode.attr,
    &dev_attr_qsfp12_reset.attr,
    &dev_attr_qsfp12_low_power_mode.attr,
    &dev_attr_qsfp13_reset.attr,
    &dev_attr_qsfp13_low_power_mode.attr,
    &dev_attr_qsfp14_reset.attr,
    &dev_attr_qsfp14_low_power_mode.attr,
    &dev_attr_qsfp15_reset.attr,
    &dev_attr_qsfp15_low_power_mode.attr,
    &dev_attr_qsfp16_reset.attr,
    &dev_attr_qsfp16_low_power_mode.attr,
    &dev_attr_qsfp17_reset.attr,
    &dev_attr_qsfp17_low_power_mode.attr,
    &dev_attr_qsfp18_reset.attr,
    &dev_attr_qsfp18_low_power_mode.attr,
    &dev_attr_qsfp19_reset.attr,
    &dev_attr_qsfp19_low_power_mode.attr,
    &dev_attr_qsfp20_reset.attr,
    &dev_attr_qsfp20_low_power_mode.attr,
    &dev_attr_qsfp21_reset.attr,
    &dev_attr_qsfp21_low_power_mode.attr,
    &dev_attr_qsfp22_reset.attr,
    &dev_attr_qsfp22_low_power_mode.attr,
    &dev_attr_qsfp23_reset.attr,
    &dev_attr_qsfp23_low_power_mode.attr,
    &dev_attr_qsfp24_reset.attr,
    &dev_attr_qsfp24_low_power_mode.attr,
    &dev_attr_qsfp25_reset.attr,
    &dev_attr_qsfp25_low_power_mode.attr,
    &dev_attr_qsfp26_reset.attr,
    &dev_attr_qsfp26_low_power_mode.attr,
    &dev_attr_qsfp27_reset.attr,
    &dev_attr_qsfp27_low_power_mode.attr,
    &dev_attr_psu1_ctrl.attr,
    &dev_attr_psu2_ctrl.attr,
    &dev_attr_psu1_present.attr,
    &dev_attr_psu1_alert.attr,
    &dev_attr_psu1_power_ok.attr,
    &dev_attr_psu2_present.attr,
    &dev_attr_psu2_alert.attr,
    &dev_attr_psu2_power_ok.attr,
    &dev_attr_fan0_power_enable.attr,
    &dev_attr_fan1_power_enable.attr,
    &dev_attr_fan2_power_enable.attr,
    &dev_attr_fan3_power_enable.attr,
    &dev_attr_fan0_pwn_ctrl.attr,
    &dev_attr_fan1_pwn_ctrl.attr,
    &dev_attr_fan2_pwn_ctrl.attr,
    &dev_attr_fan3_pwn_ctrl.attr,
    &dev_attr_fan0_present.attr,
    &dev_attr_fan1_present.attr,
    &dev_attr_fan2_present.attr,
    &dev_attr_fan3_present.attr,
    &dev_attr_fan0_direction.attr,
    &dev_attr_fan1_direction.attr,
    &dev_attr_fan2_direction.attr,
    &dev_attr_fan3_direction.attr,
    &dev_attr_fan0_hw_rev.attr,
    &dev_attr_fan1_hw_rev.attr,
    &dev_attr_fan2_hw_rev.attr,
    &dev_attr_fan3_hw_rev.attr,
    &dev_attr_fan0_alert.attr,
    &dev_attr_fan1_alert.attr,
    &dev_attr_fan2_alert.attr,
    &dev_attr_fan3_alert.attr,
    &dev_attr_fan0_error.attr,
    &dev_attr_fan1_error.attr,
    &dev_attr_fan2_error.attr,
    &dev_attr_fan3_error.attr,
    &dev_attr_fan0_inlet.attr,
    &dev_attr_fan0_outlet.attr,
    &dev_attr_fan1_inlet.attr,
    &dev_attr_fan1_outlet.attr,
    &dev_attr_fan2_inlet.attr,
    &dev_attr_fan2_outlet.attr,
    &dev_attr_fan3_inlet.attr,
    &dev_attr_fan3_outlet.attr,
    &dev_attr_elba0_power_ctrl.attr,
    &dev_attr_elba1_power_ctrl.attr,
    &dev_attr_elba2_power_ctrl.attr,
    &dev_attr_elba3_power_ctrl.attr,
    &dev_attr_elba4_power_ctrl.attr,
    &dev_attr_elba5_power_ctrl.attr,
    &dev_attr_elba6_power_ctrl.attr,
    &dev_attr_elba7_power_ctrl.attr,
    &dev_attr_elba0_power_stat.attr,
    &dev_attr_elba1_power_stat.attr,
    &dev_attr_elba2_power_stat.attr,
    &dev_attr_elba3_power_stat.attr,
    &dev_attr_elba4_power_stat.attr,
    &dev_attr_elba5_power_stat.attr,
    &dev_attr_elba6_power_stat.attr,
    &dev_attr_elba7_power_stat.attr,
    &dev_attr_th4_power_ctrl.attr,
    &dev_attr_th4_power_stat.attr,
    &dev_attr_th4_pci_reset.attr,
    &dev_attr_th4_sys_reset.attr,
    &dev_attr_wdog_ctrl_reg.attr,
    &dev_attr_wdog_reset_reg.attr,
    &dev_attr_th4_ctrl_reg.attr,
    NULL,
};

static struct attribute_group fpga_attr_group = {
   .attrs  = fpga_attrs,
};


/*
 * 'process_lock' exists because ocores_process() and ocores_process_timeout()
 * can't run in parallel.
 */
struct ocores_i2c {
    void __iomem *base;
    unsigned long flags;
    wait_queue_head_t wait;
    struct i2c_adapter adap;
    struct i2c_msg *msg;
    int pos;
    int nmsgs;
    int state; /* see STATE_ */
    spinlock_t process_lock;
    void (*setreg)(struct ocores_i2c *i2c, int reg, u8 value);
    u8 (*getreg)(struct ocores_i2c *i2c, int reg);
};

/* registers */
#define OCI2C_PRELOW        0
#define OCI2C_PREHIGH       1
#define OCI2C_CONTROL       2
#define OCI2C_DATA          3
#define OCI2C_CMD           4 /* write only */
#define OCI2C_STATUS        4 /* read only, same address as OCI2C_CMD */

#define OCI2C_CTRL_IEN      0x40
#define OCI2C_CTRL_EN       0x80

#define OCI2C_CMD_START     0x91
#define OCI2C_CMD_STOP      0x41
#define OCI2C_CMD_READ      0x21
#define OCI2C_CMD_WRITE     0x11
#define OCI2C_CMD_READ_ACK  0x21
#define OCI2C_CMD_READ_NACK 0x29
#define OCI2C_CMD_IACK      0x01

#define OCI2C_STAT_IF       0x01
#define OCI2C_STAT_TIP      0x02
#define OCI2C_STAT_ARBLOST  0x20
#define OCI2C_STAT_BUSY     0x40
#define OCI2C_STAT_NACK     0x80

#define STATE_DONE      0
#define STATE_START     1
#define STATE_WRITE     2
#define STATE_READ      3
#define STATE_ERROR     4

#define OCORES_FLAG_BROKEN_IRQ BIT(1) /* Broken IRQ for FU540-C000 SoC */

static struct ocores_i2c ocores_i2c_list[NUM_I2C_CONTROLLERS];

static struct fpga_i2c_mux_plat_data i2c_mux_plat_data[] = {
   [0] = {
       .mux_reg_addr   = 0,
       .dev_id     = 0,
   },
   [1] = {
       .mux_reg_addr   = 0,
       .dev_id     = 1,
   },
   [2] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [3] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [4] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [5] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [6] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [7] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [8] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [9] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [10] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [11] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [12] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [13] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [14] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [15] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [16] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [17] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
   [18] = {
       .mux_reg_addr   = 0,
       .dev_id     = 2,
   },
};

struct i2c_board_info  board_info [] = {
   [0] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x01),
   },
   [1] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x02),
   },
   [2] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [3] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [4] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [5] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [6] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [7] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [8] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [9] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [10] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [11] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [12] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [13] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [14] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [15] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [16] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [17] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
   [18] = {
       I2C_BOARD_INFO("pen_fpga_i2c_mux", 0x03),
   },
};

static void oc_setreg_32(struct ocores_i2c *i2c, int reg, u8 value)
{
    iowrite32(value, i2c->base + (reg * 4));
}

static inline u8 oc_getreg_32(struct ocores_i2c *i2c, int reg)
{
    return ioread32(i2c->base + (reg * 4));
}

static inline void oc_setreg(struct ocores_i2c *i2c, int reg, u8 value)
{
    i2c->setreg(i2c, reg, value);
}

static inline u8 oc_getreg(struct ocores_i2c *i2c, int reg)
{
    return i2c->getreg(i2c, reg);
}

static void ocores_process(struct ocores_i2c *i2c, u8 stat)
{
    struct i2c_msg *msg = i2c->msg;
    unsigned long flags;

    /*
     * If we spin here is because we are in timeout, so we are going
     * to be in STATE_ERROR. See ocores_process_timeout()
     */
    spin_lock_irqsave(&i2c->process_lock, flags);

    if ((i2c->state == STATE_DONE) || (i2c->state == STATE_ERROR)) {
        /* stop has been sent */
        oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_IACK);
        wake_up(&i2c->wait);
        goto out;
    }

    /* error? */
    if (stat & OCI2C_STAT_ARBLOST) {
        i2c->state = STATE_ERROR;
        oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_STOP);
        goto out;
    }

    if ((i2c->state == STATE_START) || (i2c->state == STATE_WRITE)) {
        i2c->state =
            (msg->flags & I2C_M_RD) ? STATE_READ : STATE_WRITE;

        if (stat & OCI2C_STAT_NACK) {
            i2c->state = STATE_ERROR;
            oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_STOP);
            goto out;
        }
    } else {
        msg->buf[i2c->pos++] = oc_getreg(i2c, OCI2C_DATA);
    }

    /* end of msg? */
    if (i2c->pos == msg->len) {
        i2c->nmsgs--;
        i2c->msg++;
        i2c->pos = 0;
        msg = i2c->msg;

        if (i2c->nmsgs) {   /* end? */
            /* send start? */
            if (!(msg->flags & I2C_M_NOSTART)) {
                u8 addr = i2c_8bit_addr_from_msg(msg);

                i2c->state = STATE_START;

                oc_setreg(i2c, OCI2C_DATA, addr);
                oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_START);
                goto out;
            }
            i2c->state = (msg->flags & I2C_M_RD)
                ? STATE_READ : STATE_WRITE;
        } else {
            i2c->state = STATE_DONE;
            oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_STOP);
            goto out;
        }
    }

    if (i2c->state == STATE_READ) {
        oc_setreg(i2c, OCI2C_CMD, i2c->pos == (msg->len-1) ?
              OCI2C_CMD_READ_NACK : OCI2C_CMD_READ_ACK);
    } else {
        oc_setreg(i2c, OCI2C_DATA, msg->buf[i2c->pos++]);
        oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_WRITE);
    }

out:
    spin_unlock_irqrestore(&i2c->process_lock, flags);
}

static irqreturn_t ocores_isr(int irq, void *dev_id)
{
    struct ocores_i2c *i2c = dev_id;
    u8 stat = oc_getreg(i2c, OCI2C_STATUS);

    if (i2c->flags & OCORES_FLAG_BROKEN_IRQ) {
        if ((stat & OCI2C_STAT_IF) && !(stat & OCI2C_STAT_BUSY))
            return IRQ_NONE;
    } else if (!(stat & OCI2C_STAT_IF)) {
        return IRQ_NONE;
    }
    ocores_process(i2c, stat);

    return IRQ_HANDLED;
}

/**
 * Process timeout event
 * @i2c: ocores I2C device instance
 */
static void ocores_process_timeout(struct ocores_i2c *i2c)
{
    unsigned long flags;

    spin_lock_irqsave(&i2c->process_lock, flags);
    i2c->state = STATE_ERROR;
    oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_STOP);
    spin_unlock_irqrestore(&i2c->process_lock, flags);
}

/**
 * Wait until something change in a given register
 * @i2c: ocores I2C device instance
 * @reg: register to query
 * @mask: bitmask to apply on register value
 * @val: expected result
 * @timeout: timeout in jiffies
 *
 * Timeout is necessary to avoid to stay here forever when the chip
 * does not answer correctly.
 *
 * Return: 0 on success, -ETIMEDOUT on timeout
 */
static int ocores_wait(struct ocores_i2c *i2c,
               int reg, u8 mask, u8 val,
               const unsigned long timeout)
{
    unsigned long j;

    j = jiffies + timeout;
    while (1) {
        u8 status = oc_getreg(i2c, reg);

        if ((status & mask) == val)
            break;

        udelay(8 * 10);

        if (time_after(jiffies, j))
            return -ETIMEDOUT;
    }
    return 0;
}

/**
 * Wait until is possible to process some data
 * @i2c: ocores I2C device instance
 *
 * Used when the device is in polling mode (interrupts disabled).
 *
 * Return: 0 on success, -ETIMEDOUT on timeout
 */
static int ocores_poll_wait(struct ocores_i2c *i2c)
{
    u8 mask;
    int err;

    if (i2c->state == STATE_DONE || i2c->state == STATE_ERROR) {
        /* transfer is over */
        mask = OCI2C_STAT_BUSY;
    } else {
        /* on going transfer */
        mask = OCI2C_STAT_TIP;
    }

    /*
     * once we are here we expect to get the expected result immediately
     * so if after 1ms we timeout then something is broken.
     */
    err = ocores_wait(i2c, OCI2C_STATUS, mask, 0, msecs_to_jiffies(1));
    if (err)
        dev_warn(i2c->adap.dev.parent,
             "%s: STATUS timeout, bit 0x%x did not clear in 1ms\n",
             __func__, mask);
    return err;
}

/**
 * It handles an IRQ-less transfer
 * @i2c: ocores I2C device instance
 *
 * Even if IRQ are disabled, the I2C OpenCore IP behavior is exactly the same
 * (only that IRQ are not produced). This means that we can re-use entirely
 * ocores_isr(), we just add our polling code around it.
 *
 * It can run in atomic context
 */
static void ocores_process_polling(struct ocores_i2c *i2c)
{
    while (1) {
        irqreturn_t ret;
        int err;

        err = ocores_poll_wait(i2c);
        if (err) {
            i2c->state = STATE_ERROR;
            break; /* timeout */
        }

        ret = ocores_isr(-1, i2c);
        if (ret == IRQ_NONE)
            break; /* all messages have been transferred */
        else {
            if (i2c->flags & OCORES_FLAG_BROKEN_IRQ)
                if (i2c->state == STATE_DONE)
                    break;
        }
    }
}

static int ocores_xfer_core(struct ocores_i2c *i2c,
                struct i2c_msg *msgs, int num,
                bool polling)
{
    int ret;
    u8 ctrl;

    ctrl = oc_getreg(i2c, OCI2C_CONTROL);
    if (polling)
        oc_setreg(i2c, OCI2C_CONTROL, ctrl & ~OCI2C_CTRL_IEN);
    else
        oc_setreg(i2c, OCI2C_CONTROL, ctrl | OCI2C_CTRL_IEN);

    i2c->msg = msgs;
    i2c->pos = 0;
    i2c->nmsgs = num;
    i2c->state = STATE_START;

    oc_setreg(i2c, OCI2C_DATA, i2c_8bit_addr_from_msg(i2c->msg));
    oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_START);

    if (polling) {
        ocores_process_polling(i2c);
    } else {
        ret = wait_event_timeout(i2c->wait,
                     (i2c->state == STATE_ERROR) ||
                     (i2c->state == STATE_DONE), HZ);
        if (ret == 0) {
            ocores_process_timeout(i2c);
            return -ETIMEDOUT;
        }
    }

    return (i2c->state == STATE_DONE) ? num : -EIO;
}

static int ocores_xfer_polling(struct i2c_adapter *adap,
                   struct i2c_msg *msgs, int num)
{
    return ocores_xfer_core(i2c_get_adapdata(adap), msgs, num, true);
}

static int ocores_xfer(struct i2c_adapter *adap,
               struct i2c_msg *msgs, int num)
{
    return ocores_xfer_core(i2c_get_adapdata(adap), msgs, num, false);
}

static int ocores_init(struct ocores_i2c *i2c)
{
    u8 ctrl = oc_getreg(i2c, OCI2C_CONTROL);

    /* make sure the device is disabled */
    ctrl &= ~(OCI2C_CTRL_EN | OCI2C_CTRL_IEN);
    oc_setreg(i2c, OCI2C_CONTROL, ctrl);

    oc_setreg(i2c, OCI2C_PRELOW, I2C_PRESCALE_LOW_VAL);
    oc_setreg(i2c, OCI2C_PREHIGH, I2C_PRESCALE_HIGH_VAL);

    /* Init the device */
    oc_setreg(i2c, OCI2C_CMD, OCI2C_CMD_IACK);
    oc_setreg(i2c, OCI2C_CONTROL, ctrl | OCI2C_CTRL_EN);

    return 0;
}

static u32 ocores_func(struct i2c_adapter *adap)
{
    return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
}

static struct i2c_algorithm ocores_algorithm = {
    .master_xfer = ocores_xfer,
    .master_xfer_atomic = ocores_xfer_polling,
    .functionality = ocores_func,
};

static const struct i2c_adapter ocores_adapter = {
    .owner = THIS_MODULE,
    .name = "i2c-ocores",
    .class = I2C_CLASS_DEPRECATED,
    .algo = &ocores_algorithm,
};

int ocores_i2c_probe(struct pci_dev *pdev, void* base, int instance,
                            int controller_id, uint32_t i2c_start_addr,
                            uint32_t i2c_register_range)
{
    struct ocores_i2c *i2c;
    int ret;
    int i = controller_id;

    i2c = &ocores_i2c_list[controller_id];
    i2c->base = base;

    spin_lock_init(&i2c->process_lock);

    if (!i2c->setreg || !i2c->getreg) {
        i2c->setreg = oc_setreg_32;
        i2c->getreg = oc_getreg_32;
    }

    init_waitqueue_head(&i2c->wait);

    ocores_algorithm.master_xfer = ocores_xfer_polling;

    ret = ocores_init(i2c);
    if (ret)
        goto err_ret;

    /* hook up driver to tree */
    i2c->adap = ocores_adapter;
    i2c_set_adapdata(&i2c->adap, i2c);
    i2c->adap.dev.parent = &pdev->dev;
    i2c->adap.dev.of_node = pdev->dev.of_node;

    /* add i2c adapter to i2c tree */
    ret = i2c_add_adapter(&i2c->adap);
    if (ret)
        goto err_ret;

    //Instantiate mux device.
    i2c_mux_plat_data[i].mux_reg_addr = pdev->resource[0].start +
            i2c_start_addr + (instance * i2c_register_range) + I2C_MUX_OFFSET;
    i2c_mux_plat_data[i].dev_id = controller_id;
    board_info[i].platform_data = (void *) &i2c_mux_plat_data[i];
    i2c_new_client_device(&i2c->adap, &board_info[i]);

    return 0;

err_ret:
    return ret;
}

int ocores_i2c_remove(struct pci_dev *pdev,
                             int controller_id)
{
    struct ocores_i2c *i2c;

    if (controller_id >= NUM_I2C_CONTROLLERS) {
            dev_err(&pdev->dev, "remove: controller_id:%d is invalid",
                    controller_id);
            return -ENOENT;
    }

    i2c = &ocores_i2c_list[controller_id];

    /* disable i2c logic */
    oc_setreg(i2c, OCI2C_CONTROL, oc_getreg(i2c, OCI2C_CONTROL)
          & ~(OCI2C_CTRL_EN|OCI2C_CTRL_IEN));

    /* remove adapter & data */
    i2c_del_adapter(&i2c->adap);

    return 0;
}

EXPORT_SYMBOL(ocores_i2c_probe);
EXPORT_SYMBOL(ocores_i2c_remove);
static int
amd_fpga_oci2c_probe(struct pci_dev *pdev,
                     const struct pci_device_id *id) {
    void __iomem *const *pci_tbl;
    char     *i2c_base_addr;
    int      i;
    int      ret;

    ret = pcim_enable_device(pdev);
    if (ret) {
        dev_err(&pdev->dev, "Failed to enable FPGA I2C PCI device ret=%d\n",
                ret);
        return ret;
    }

    if (!pdev->is_busmaster) {
        pci_set_master(pdev);
    }

    ret = pcim_iomap_regions(pdev, 1, AMD_FPGA_I2C);
    if (ret) {
        dev_err(&pdev->dev, "Failed to ioremap rc=%d\n",
                ret);
        pci_disable_device(pdev);
    return ret;
    }

    pci_tbl       = pcim_iomap_table(pdev);
    fpga_membase  = pci_tbl[0];;

    i2c_base_addr = (char*)fpga_membase;
    i2c_base_addr += FPGA0_I2C_ADDRESS_START;

    for (i = 0; i < FPGA0_NUM_I2C_CONTROLLERS; i++) {
        ocores_i2c_probe(pdev, i2c_base_addr, i, i,
                         FPGA0_I2C_ADDRESS_START, FPGA0_I2C_REGISTERS_ADDRESS_SIZE);
        i2c_base_addr += FPGA0_I2C_REGISTERS_ADDRESS_SIZE;
    }

    /*
    ret = sysfs_create_group(&pdev->dev.kobj, &fpga_attr_group);
    if (ret) {
        sysfs_remove_group(&pdev->dev.kobj, &fpga_attr_group);
        dev_err(&pdev->dev, "Failed to create attr group\n");
    }
    */
    return ret;

}

static void amd_fpga_oci2c_remove (struct pci_dev *pdev) {
    int i;

    for (i = 0; i < FPGA0_NUM_I2C_CONTROLLERS; i++) {
        ocores_i2c_remove(pdev, i);
    }

    pcim_iounmap_regions(pdev, 1);
    pci_disable_device(pdev);
}

static const struct pci_device_id amd_fpga_oci2c_ids[] = {
    {PCI_DEVICE(PCI_VENDOR_ID_AMD_FPGA, PCI_DEVICE_ID_AMD_FPGA_I2C)},
    {0}
};


static struct pci_driver amd_fpga_oci2c_driver = {
    .name        = "amd-fpga-ocores-i2c",
    .id_table    = amd_fpga_oci2c_ids,
    .probe       = amd_fpga_oci2c_probe,
    .remove      = amd_fpga_oci2c_remove,
};

static int __init amd_fpga_oci2c_init(void) {
    return pci_register_driver(&amd_fpga_oci2c_driver);
}

static void __exit amd_fpga_oci2c_exit(void) {
    pci_unregister_driver(&amd_fpga_oci2c_driver);
}

module_init(amd_fpga_oci2c_init);
module_exit(amd_fpga_oci2c_exit);

MODULE_DESCRIPTION("AMD FPGA OpenCores I2C bus driver");
MODULE_LICENSE("GPL");

MODULE_AUTHOR("Peter Korsgaard <peter@korsgaard.com>");
MODULE_AUTHOR("Ashwin H <Ashwin.H@amd.com>");
MODULE_AUTHOR("Ganesan Ramalingam <ganesan.ramalingam@amd.com>");
