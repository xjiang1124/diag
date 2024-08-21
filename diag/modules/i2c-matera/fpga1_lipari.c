// SPDX-License-Identifier: GPL-2.0
/*
 * Support for FPGA-1 on lipari. Registers I2C controllers
 * on FPGA and creates SYSFS entries for different registers
 * on FPGA, FPGA1 has ELBA related.
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
GEN_SHOW(board_rev,0xC,0,3)
GEN_SHOW(led_debug_0_reg, 0x40, 0, 31)
GEN_SHOW(led_debug_1_reg, 0x44, 0, 31)
GEN_SHOW(led_debug_2_reg, 0x48, 0, 31)
GEN_SHOW(led_debug_3_reg, 0x4C, 0, 31)
GEN_STORE(led_debug_0_reg, 0x40, 0, 31)
GEN_STORE(led_debug_1_reg, 0x44, 0, 31)
GEN_STORE(led_debug_2_reg, 0x48, 0, 31)
GEN_STORE(led_debug_3_reg, 0x4C, 0, 31)
GEN_SHOW(debug_0_reg, 0x50, 0, 31)
GEN_SHOW(debug_1_reg, 0x54, 0, 31)
GEN_SHOW(debug_2_reg, 0x58, 0, 31)
GEN_SHOW(debug_3_reg, 0x5C, 0, 31)
GEN_STORE(debug_0_reg, 0x50, 0, 31)
GEN_STORE(debug_1_reg, 0x54, 0, 31)
GEN_STORE(debug_2_reg, 0x58, 0, 31)
GEN_STORE(debug_3_reg, 0x5C, 0, 31)
GEN_SHOW(elba_reset_cause_0_reg, 0x200, 0, 23)
GEN_SHOW(elba_reset_cause_1_reg, 0x204, 0, 23)
GEN_SHOW(elba_reset_cause_2_reg, 0x208, 0, 23)
GEN_SHOW(elba_reset_cause_3_reg, 0x20C, 0, 23)
GEN_SHOW(elba_reset_cause_4_reg, 0x210, 0, 23)
GEN_SHOW(elba_reset_cause_5_reg, 0x214, 0, 23)
GEN_SHOW(elba_reset_cause_6_reg, 0x218, 0, 23)
GEN_SHOW(elba_reset_cause_7_reg, 0x21C, 0, 23)
GEN_STORE(elba_reset_cause_0_reg, 0x200, 0, 23)
GEN_STORE(elba_reset_cause_1_reg, 0x204, 0, 23)
GEN_STORE(elba_reset_cause_2_reg, 0x208, 0, 23)
GEN_STORE(elba_reset_cause_3_reg, 0x20C, 0, 23)
GEN_STORE(elba_reset_cause_4_reg, 0x210, 0, 23)
GEN_STORE(elba_reset_cause_5_reg, 0x214, 0, 23)
GEN_STORE(elba_reset_cause_6_reg, 0x218, 0, 23)
GEN_STORE(elba_reset_cause_7_reg, 0x21C, 0, 23)
GEN_STORE(soft_reset_reg, 0x2A8, 0,7)
GEN_SHOW(misc_ctrl_reg, 0x2Ac, 0, 2)
GEN_STORE(misc_ctrl_reg, 0x2Ac, 0, 2)
GEN_SHOW(flsh_ctrl_reg, 0x2B4, 0, 2)
GEN_STORE(flsh_ctrl_reg, 0x2B4, 0, 2)
GEN_SHOW(e0_ctrl_reg, 0x300, 0, 8)
GEN_SHOW(e0_wdog_ctrl_reg, 0x308, 0, 31)
GEN_SHOW(e0_wdog_stat_reg, 0x30C, 0, 7)
GEN_STORE(e0_ctrl_reg, 0x300, 0, 8)
GEN_STORE(e0_wdog_ctrl_reg, 0x308, 0, 31)
GEN_STORE(e0_wdog_stat_reg, 0x30C, 0, 7)
GEN_SHOW(e1_ctrl_reg, 0x320, 0, 8)
GEN_SHOW(e1_wdog_ctrl_reg, 0x328, 0, 31)
GEN_SHOW(e1_wdog_stat_reg, 0x32C, 0, 7)
GEN_STORE(e1_ctrl_reg, 0x320, 0, 8)
GEN_STORE(e1_wdog_ctrl_reg, 0x328, 0, 31)
GEN_STORE(e1_wdog_stat_reg, 0x32C, 0, 7)
GEN_SHOW(e2_ctrl_reg, 0x340, 0, 8)
GEN_SHOW(e2_wdog_ctrl_reg, 0x348, 0, 31)
GEN_SHOW(e2_wdog_stat_reg, 0x34C, 0, 7)
GEN_STORE(e2_ctrl_reg, 0x340, 0, 8)
GEN_STORE(e2_wdog_ctrl_reg, 0x348, 0, 31)
GEN_STORE(e2_wdog_stat_reg, 0x34C, 0, 7)
GEN_SHOW(e3_ctrl_reg, 0x360, 0, 8)
GEN_SHOW(e3_wdog_ctrl_reg, 0x368, 0, 31)
GEN_SHOW(e3_wdog_stat_reg, 0x36C, 0, 7)
GEN_STORE(e3_ctrl_reg, 0x360, 0, 8)
GEN_STORE(e3_wdog_ctrl_reg, 0x368, 0, 31)
GEN_STORE(e3_wdog_stat_reg, 0x36C, 0, 7)
GEN_SHOW(e4_ctrl_reg, 0x380, 0, 8)
GEN_SHOW(e4_wdog_ctrl_reg, 0x388, 0, 31)
GEN_SHOW(e4_wdog_stat_reg, 0x38C, 0, 7)
GEN_STORE(e4_ctrl_reg, 0x380, 0, 8)
GEN_STORE(e4_wdog_ctrl_reg, 0x388, 0, 31)
GEN_STORE(e4_wdog_stat_reg, 0x38C, 0, 7)
GEN_SHOW(e5_ctrl_reg, 0x3A0, 0, 8)
GEN_SHOW(e5_wdog_ctrl_reg, 0x3A8, 0, 31)
GEN_SHOW(e5_wdog_stat_reg, 0x3AC, 0, 7)
GEN_STORE(e5_ctrl_reg, 0x3A0, 0, 8)
GEN_STORE(e5_wdog_ctrl_reg, 0x3A8, 0, 31)
GEN_STORE(e5_wdog_stat_reg, 0x3AC, 0, 7)
GEN_SHOW(e6_ctrl_reg, 0x3C0, 0, 8)
GEN_SHOW(e6_wdog_ctrl_reg, 0x3C8, 0, 31)
GEN_SHOW(e6_wdog_stat_reg, 0x3CC, 0, 7)
GEN_STORE(e6_ctrl_reg, 0x3C0, 0, 8)
GEN_STORE(e6_wdog_ctrl_reg, 0x3C8, 0, 31)
GEN_STORE(e6_wdog_stat_reg, 0x3CC, 0, 7)
GEN_SHOW(e7_ctrl_reg, 0x3E0, 0, 8)
GEN_SHOW(e7_wdog_ctrl_reg, 0x3E8, 0, 31)
GEN_SHOW(e7_wdog_stat_reg, 0x3EC, 0, 7)
GEN_STORE(e7_ctrl_reg, 0x3E0, 0, 8)
GEN_STORE(e7_wdog_ctrl_reg, 0x3E8, 0, 31)
GEN_STORE(e7_wdog_stat_reg, 0x3EC, 0, 7)
GEN_SHOW(e0cfg_spi_muxsel_reg, 0x464, 0, 0)
GEN_SHOW(e1cfg_spi_muxsel_reg, 0x4A4, 0, 0)
GEN_SHOW(e2cfg_spi_muxsel_reg, 0x4E4, 0, 0)
GEN_SHOW(e3cfg_spi_muxsel_reg, 0x524, 0, 0)
GEN_SHOW(e4cfg_spi_muxsel_reg, 0x564, 0, 0)
GEN_SHOW(e5cfg_spi_muxsel_reg, 0x5A4, 0, 0)
GEN_SHOW(e6cfg_spi_muxsel_reg, 0x5E4, 0, 0)
GEN_SHOW(e7cfg_spi_muxsel_reg, 0x624, 0, 0)
GEN_STORE(e0cfg_spi_muxsel_reg, 0x464, 0, 0)
GEN_STORE(e1cfg_spi_muxsel_reg, 0x4A4, 0, 0)
GEN_STORE(e2cfg_spi_muxsel_reg, 0x4E4, 0, 0)
GEN_STORE(e3cfg_spi_muxsel_reg, 0x524, 0, 0)
GEN_STORE(e4cfg_spi_muxsel_reg, 0x564, 0, 0)
GEN_STORE(e5cfg_spi_muxsel_reg, 0x5A4, 0, 0)
GEN_STORE(e6cfg_spi_muxsel_reg, 0x5E4, 0, 0)
GEN_STORE(e7cfg_spi_muxsel_reg, 0x624, 0, 0)
GEN_SHOW(e0spi_muxsel_reg, 0x824, 0, 0)
GEN_SHOW(e1spi_muxsel_reg, 0x864, 0, 0)
GEN_SHOW(e2spi_muxsel_reg, 0x8A4, 0, 0)
GEN_SHOW(e3spi_muxsel_reg, 0x8E4, 0, 0)
GEN_SHOW(e4spi_muxsel_reg, 0x924, 0, 0)
GEN_SHOW(e5spi_muxsel_reg, 0x964, 0, 0)
GEN_SHOW(e6spi_muxsel_reg, 0x9A4, 0, 0)
GEN_SHOW(e7spi_muxsel_reg, 0x9E4, 0, 0)
GEN_STORE(e0spi_muxsel_reg, 0x824, 0, 0)
GEN_STORE(e1spi_muxsel_reg, 0x864, 0, 0)
GEN_STORE(e2spi_muxsel_reg, 0x8A4, 0, 0)
GEN_STORE(e3spi_muxsel_reg, 0x8E4, 0, 0)
GEN_STORE(e4spi_muxsel_reg, 0x924, 0, 0)
GEN_STORE(e5spi_muxsel_reg, 0x964, 0, 0)
GEN_STORE(e6spi_muxsel_reg, 0x9A4, 0, 0)
GEN_STORE(e7spi_muxsel_reg, 0x9E4, 0, 0)
GEN_SHOW(e0_uart_rxdata_reg, 0x1000, 0, 7)
GEN_SHOW(e0_uart_txdata_reg, 0x1004, 0, 7)
GEN_SHOW(e0_uart_stat_reg, 0x1008, 0, 7)
GEN_SHOW(e0_uart_ctrl_reg, 0x100C, 0, 4)
GEN_SHOW(e1_uart_rxdata_reg, 0x1100, 0, 7)
GEN_SHOW(e1_uart_txdata_reg, 0x1104, 0, 7)
GEN_SHOW(e1_uart_stat_reg, 0x1108, 0, 7)
GEN_SHOW(e1_uart_ctrl_reg, 0x110C, 0, 4)
GEN_SHOW(e2_uart_rxdata_reg, 0x1200, 0, 7)
GEN_SHOW(e2_uart_txdata_reg, 0x1204, 0, 7)
GEN_SHOW(e2_uart_stat_reg, 0x1208, 0, 7)
GEN_SHOW(e2_uart_ctrl_reg, 0x120C, 0, 4)
GEN_SHOW(e3_uart_rxdata_reg, 0x1300, 0, 7)
GEN_SHOW(e3_uart_txdata_reg, 0x1304, 0, 7)
GEN_SHOW(e3_uart_stat_reg, 0x1308, 0, 7)
GEN_SHOW(e3_uart_ctrl_reg, 0x130C, 0, 4)
GEN_SHOW(e4_uart_rxdata_reg, 0x1400, 0, 7)
GEN_SHOW(e4_uart_txdata_reg, 0x1404, 0, 7)
GEN_SHOW(e4_uart_stat_reg, 0x1408, 0, 7)
GEN_SHOW(e4_uart_ctrl_reg, 0x140C, 0, 4)
GEN_SHOW(e5_uart_rxdata_reg, 0x1500, 0, 7)
GEN_SHOW(e5_uart_txdata_reg, 0x1504, 0, 7)
GEN_SHOW(e5_uart_stat_reg, 0x1508, 0, 7)
GEN_SHOW(e5_uart_ctrl_reg, 0x150C, 0, 4)
GEN_SHOW(e6_uart_rxdata_reg, 0x1600, 0, 7)
GEN_SHOW(e6_uart_txdata_reg, 0x1604, 0, 7)
GEN_SHOW(e6_uart_stat_reg, 0x1608, 0, 7)
GEN_SHOW(e6_uart_ctrl_reg, 0x160C, 0, 4)
GEN_SHOW(e7_uart_rxdata_reg, 0x1700, 0, 7)
GEN_SHOW(e7_uart_txdata_reg, 0x1704, 0, 7)
GEN_SHOW(e7_uart_stat_reg, 0x1708, 0, 7)
GEN_SHOW(e7_uart_ctrl_reg, 0x170C, 0, 4)
GEN_SHOW(int0_en_reg, 0x60, 0, 0)
GEN_SHOW(int1_en_reg, 0x64, 0, 0)
GEN_SHOW(int2_en_reg, 0x68, 0, 0)
GEN_SHOW(int3_en_reg, 0x6C, 0, 0)
GEN_SHOW(int4_en_reg, 0x70, 0, 0)
GEN_SHOW(int5_en_reg, 0x74, 0, 0)
GEN_SHOW(int6_en_reg, 0x78, 0, 0)
GEN_SHOW(int7_en_reg, 0x7C, 0, 0)
GEN_SHOW(int8_en_reg, 0x80, 0, 0)
GEN_SHOW(int9_en_reg, 0x84, 0, 0)
GEN_SHOW(int10_en_reg, 0x88, 0, 0)
GEN_SHOW(int11_en_reg, 0x8C, 0, 0)
GEN_SHOW(int12_en_reg, 0x90, 0, 0)
GEN_SHOW(int13_en_reg, 0x94, 0, 0)
GEN_SHOW(int14_en_reg, 0x98, 0, 0)
GEN_SHOW(int15_en_reg, 0x9C, 0, 0)
GEN_SHOW(int0_pend_reg, 0xA0, 0, 0)
GEN_SHOW(int1_pend_reg, 0xA4, 0, 0)
GEN_SHOW(int2_pend_reg, 0xA8, 0, 0)
GEN_SHOW(int3_pend_reg, 0xAC, 0, 0)
GEN_SHOW(int4_pend_reg, 0xB0, 0, 0)
GEN_SHOW(int5_pend_reg, 0xB4, 0, 0)
GEN_SHOW(int6_pend_reg, 0xB8, 0, 0)
GEN_SHOW(int7_pend_reg, 0xBC, 0, 0)
GEN_SHOW(int8_pend_reg, 0xC0, 0, 0)
GEN_SHOW(int9_pend_reg, 0xC4, 0, 0)
GEN_SHOW(int10_pend_reg, 0xC8, 0, 0)
GEN_SHOW(int11_pend_reg, 0xCC, 0, 0)
GEN_SHOW(int12_pend_reg, 0xD0, 0, 0)
GEN_SHOW(int13_pend_reg, 0xD4, 0, 0)
GEN_SHOW(int14_pend_reg, 0xD8, 0, 0)
GEN_SHOW(int15_pend_reg, 0xDC, 0, 0)
GEN_SHOW(bmc_int0_en_reg, 0xE0, 0, 0)
GEN_SHOW(bmc_int1_en_reg, 0xE4, 0, 0)
GEN_SHOW(bmc_int2_en_reg, 0xE8, 0, 0)
GEN_SHOW(bmc_int3_en_reg, 0xEC, 0, 0)
GEN_SHOW(bmc_int4_en_reg, 0xF0, 0, 0)
GEN_SHOW(bmc_int5_en_reg, 0xF4, 0, 0)
GEN_SHOW(bmc_int6_en_reg, 0xF8, 0, 0)
GEN_SHOW(bmc_int7_en_reg, 0xFC, 0, 0)
GEN_SHOW(bmc_int8_en_reg, 0x100, 0, 0)
GEN_SHOW(bmc_int9_en_reg, 0x104, 0, 0)
GEN_SHOW(bmc_int10_en_reg, 0x108, 0, 0)
GEN_SHOW(bmc_int11_en_reg, 0x10C, 0, 0)
GEN_SHOW(bmc_int12_en_reg, 0x110, 0, 0)
GEN_SHOW(bmc_int13_en_reg, 0x114, 0, 0)
GEN_SHOW(bmc_int14_en_reg, 0x118, 0, 0)
GEN_SHOW(bmc_int15_en_reg, 0x11C, 0, 0)
GEN_SHOW(bmc_int0_pend_reg, 0x120, 0, 0)
GEN_SHOW(bmc_int1_pend_reg, 0x124, 0, 0)
GEN_SHOW(bmc_int2_pend_reg, 0x128, 0, 0)
GEN_SHOW(bmc_int3_pend_reg, 0x12C, 0, 0)
GEN_SHOW(bmc_int4_pend_reg, 0x130, 0, 0)
GEN_SHOW(bmc_int5_pend_reg, 0x134, 0, 0)
GEN_SHOW(bmc_int6_pend_reg, 0x138, 0, 0)
GEN_SHOW(bmc_int7_pend_reg, 0x13C, 0, 0)
GEN_SHOW(bmc_int8_pend_reg, 0x140, 0, 0)
GEN_SHOW(bmc_int9_pend_reg, 0x144, 0, 0)
GEN_SHOW(bmc_int10_pend_reg, 0x148, 0, 0)
GEN_SHOW(bmc_int11_pend_reg, 0x14C, 0, 0)
GEN_SHOW(bmc_int12_pend_reg, 0x150, 0, 0)
GEN_SHOW(bmc_int13_pend_reg, 0x154, 0, 0)
GEN_SHOW(bmc_int14_pend_reg, 0x158, 0, 0)
GEN_SHOW(bmc_int15_pend_reg, 0x15C, 0, 0)
GEN_STORE(int0_en_reg, 0x60, 0, 0)
GEN_STORE(int1_en_reg, 0x64, 0, 0)
GEN_STORE(int2_en_reg, 0x68, 0, 0)
GEN_STORE(int3_en_reg, 0x6C, 0, 0)
GEN_STORE(int4_en_reg, 0x70, 0, 0)
GEN_STORE(int5_en_reg, 0x74, 0, 0)
GEN_STORE(int6_en_reg, 0x78, 0, 0)
GEN_STORE(int7_en_reg, 0x7C, 0, 0)
GEN_STORE(int8_en_reg, 0x80, 0, 0)
GEN_STORE(int9_en_reg, 0x84, 0, 0)
GEN_STORE(int10_en_reg, 0x88, 0, 0)
GEN_STORE(int11_en_reg, 0x8C, 0, 0)
GEN_STORE(int12_en_reg, 0x90, 0, 0)
GEN_STORE(int13_en_reg, 0x94, 0, 0)
GEN_STORE(int14_en_reg, 0x98, 0, 0)
GEN_STORE(int15_en_reg, 0x9C, 0, 0)
GEN_STORE(int0_pend_reg, 0xA0, 0, 0)
GEN_STORE(int1_pend_reg, 0xA4, 0, 0)
GEN_STORE(int2_pend_reg, 0xA8, 0, 0)
GEN_STORE(int3_pend_reg, 0xAC, 0, 0)
GEN_STORE(int4_pend_reg, 0xB0, 0, 0)
GEN_STORE(int5_pend_reg, 0xB4, 0, 0)
GEN_STORE(int6_pend_reg, 0xB8, 0, 0)
GEN_STORE(int7_pend_reg, 0xBC, 0, 0)
GEN_STORE(int8_pend_reg, 0xC0, 0, 0)
GEN_STORE(int9_pend_reg, 0xC4, 0, 0)
GEN_STORE(int10_pend_reg, 0xC8, 0, 0)
GEN_STORE(int11_pend_reg, 0xCC, 0, 0)
GEN_STORE(int12_pend_reg, 0xD0, 0, 0)
GEN_STORE(int13_pend_reg, 0xD4, 0, 0)
GEN_STORE(int14_pend_reg, 0xD8, 0, 0)
GEN_STORE(int15_pend_reg, 0xDC, 0, 0)
GEN_STORE(bmc_int0_en_reg, 0xE0, 0, 0)
GEN_STORE(bmc_int1_en_reg, 0xE4, 0, 0)
GEN_STORE(bmc_int2_en_reg, 0xE8, 0, 0)
GEN_STORE(bmc_int3_en_reg, 0xEC, 0, 0)
GEN_STORE(bmc_int4_en_reg, 0xF0, 0, 0)
GEN_STORE(bmc_int5_en_reg, 0xF4, 0, 0)
GEN_STORE(bmc_int6_en_reg, 0xF8, 0, 0)
GEN_STORE(bmc_int7_en_reg, 0xFC, 0, 0)
GEN_STORE(bmc_int8_en_reg, 0x100, 0, 0)
GEN_STORE(bmc_int9_en_reg, 0x104, 0, 0)
GEN_STORE(bmc_int10_en_reg, 0x108, 0, 0)
GEN_STORE(bmc_int11_en_reg, 0x10C, 0, 0)
GEN_STORE(bmc_int12_en_reg, 0x110, 0, 0)
GEN_STORE(bmc_int13_en_reg, 0x114, 0, 0)
GEN_STORE(bmc_int14_en_reg, 0x118, 0, 0)
GEN_STORE(bmc_int15_en_reg, 0x11C, 0, 0)
GEN_STORE(bmc_int0_pend_reg, 0x120, 0, 0)
GEN_STORE(bmc_int1_pend_reg, 0x124, 0, 0)
GEN_STORE(bmc_int2_pend_reg, 0x128, 0, 0)
GEN_STORE(bmc_int3_pend_reg, 0x12C, 0, 0)
GEN_STORE(bmc_int4_pend_reg, 0x130, 0, 0)
GEN_STORE(bmc_int5_pend_reg, 0x134, 0, 0)
GEN_STORE(bmc_int6_pend_reg, 0x138, 0, 0)
GEN_STORE(bmc_int7_pend_reg, 0x13C, 0, 0)
GEN_STORE(bmc_int8_pend_reg, 0x140, 0, 0)
GEN_STORE(bmc_int9_pend_reg, 0x144, 0, 0)
GEN_STORE(bmc_int10_pend_reg, 0x148, 0, 0)
GEN_STORE(bmc_int11_pend_reg, 0x14C, 0, 0)
GEN_STORE(bmc_int12_pend_reg, 0x150, 0, 0)
GEN_STORE(bmc_int13_pend_reg, 0x154, 0, 0)
GEN_STORE(bmc_int14_pend_reg, 0x158, 0, 0)
GEN_STORE(bmc_int15_pend_reg, 0x15C, 0, 0)
GEN_SHOW(rtc_clock, 0xC00, 0, 22)
GEN_STORE(rtc_clock, 0xC00, 0, 22)
GEN_SHOW(rtc_ckspeed_reg, 0xC10, 0, 31)
GEN_STORE(rtc_ckspeed_reg, 0xC10, 0, 31)
GEN_SHOW(rtc_hacktime_hh, 0xC14, 24, 31)
GEN_SHOW(rtc_hacktime_mm, 0xC14, 16, 23)
GEN_SHOW(rtc_hacktime_ss, 0xC14, 8, 15)
GEN_STORE(rtc_hacktime_hh, 0xC14, 24, 31)
GEN_STORE(rtc_hacktime_mm, 0xC14, 16, 23)
GEN_STORE(rtc_hacktime_ss, 0xC14, 8, 15)
GEN_SHOW(rtc_hackcnthi_32, 0xC18, 0, 31)
GEN_SHOW(rtc_hackcntlo_8, 0xC1C, 24, 31)
GEN_SHOW(rtc_date, 0xC20, 0, 31)
GEN_STORE(rtc_date, 0xC20, 0, 31)

static DEVICE_ATTR(fpga_id,S_IRUGO,fpga_id_show,NULL);
static DEVICE_ATTR(fpga_rev,S_IRUGO,fpga_rev_show,NULL);
static DEVICE_ATTR(board_rev,S_IRUGO,board_rev_show,NULL);
static DEVICE_ATTR(led_debug_0_reg, S_IRUGO|S_IWUSR, led_debug_0_reg_show, led_debug_0_reg_store);
static DEVICE_ATTR(led_debug_1_reg, S_IRUGO|S_IWUSR, led_debug_1_reg_show, led_debug_1_reg_store);
static DEVICE_ATTR(led_debug_2_reg, S_IRUGO|S_IWUSR, led_debug_2_reg_show, led_debug_2_reg_store);
static DEVICE_ATTR(led_debug_3_reg, S_IRUGO|S_IWUSR, led_debug_3_reg_show, led_debug_3_reg_store);
static DEVICE_ATTR(debug_0_reg, S_IRUGO|S_IWUSR, debug_0_reg_show, debug_0_reg_store);
static DEVICE_ATTR(debug_1_reg, S_IRUGO|S_IWUSR, debug_1_reg_show, debug_1_reg_store);
static DEVICE_ATTR(debug_2_reg, S_IRUGO|S_IWUSR, debug_2_reg_show, debug_2_reg_store);
static DEVICE_ATTR(debug_3_reg, S_IRUGO|S_IWUSR, debug_3_reg_show, debug_3_reg_store);
static DEVICE_ATTR(elba_reset_cause_0_reg, S_IRUGO|S_IWUSR, elba_reset_cause_0_reg_show, elba_reset_cause_0_reg_store);
static DEVICE_ATTR(elba_reset_cause_1_reg, S_IRUGO|S_IWUSR, elba_reset_cause_1_reg_show, elba_reset_cause_1_reg_store);
static DEVICE_ATTR(elba_reset_cause_2_reg, S_IRUGO|S_IWUSR, elba_reset_cause_2_reg_show, elba_reset_cause_2_reg_store);
static DEVICE_ATTR(elba_reset_cause_3_reg, S_IRUGO|S_IWUSR, elba_reset_cause_3_reg_show, elba_reset_cause_3_reg_store);
static DEVICE_ATTR(elba_reset_cause_4_reg, S_IRUGO|S_IWUSR, elba_reset_cause_4_reg_show, elba_reset_cause_4_reg_store);
static DEVICE_ATTR(elba_reset_cause_5_reg, S_IRUGO|S_IWUSR, elba_reset_cause_5_reg_show, elba_reset_cause_5_reg_store);
static DEVICE_ATTR(elba_reset_cause_6_reg, S_IRUGO|S_IWUSR, elba_reset_cause_6_reg_show, elba_reset_cause_6_reg_store);
static DEVICE_ATTR(elba_reset_cause_7_reg, S_IRUGO|S_IWUSR, elba_reset_cause_7_reg_show, elba_reset_cause_7_reg_store);
static DEVICE_ATTR(soft_reset_reg, S_IWUSR, NULL, soft_reset_reg_store);
static DEVICE_ATTR(misc_ctrl_reg, S_IRUGO|S_IWUSR, misc_ctrl_reg_show, misc_ctrl_reg_store);
static DEVICE_ATTR(flsh_ctrl_reg, S_IRUGO|S_IWUSR, flsh_ctrl_reg_show, flsh_ctrl_reg_store);
static DEVICE_ATTR(e0_ctrl_reg, S_IRUGO|S_IWUSR, e0_ctrl_reg_show, e0_ctrl_reg_store);
static DEVICE_ATTR(e0_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e0_wdog_ctrl_reg_show, e0_wdog_ctrl_reg_store);
static DEVICE_ATTR(e0_wdog_stat_reg, S_IRUGO|S_IWUSR, e0_wdog_stat_reg_show, e0_wdog_stat_reg_store);
static DEVICE_ATTR(e1_ctrl_reg, S_IRUGO|S_IWUSR, e1_ctrl_reg_show, e1_ctrl_reg_store);
static DEVICE_ATTR(e1_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e1_wdog_ctrl_reg_show, e1_wdog_ctrl_reg_store);
static DEVICE_ATTR(e1_wdog_stat_reg, S_IRUGO|S_IWUSR, e1_wdog_stat_reg_show, e1_wdog_stat_reg_store);
static DEVICE_ATTR(e2_ctrl_reg, S_IRUGO|S_IWUSR, e2_ctrl_reg_show, e2_ctrl_reg_store);
static DEVICE_ATTR(e2_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e2_wdog_ctrl_reg_show, e2_wdog_ctrl_reg_store);
static DEVICE_ATTR(e2_wdog_stat_reg, S_IRUGO|S_IWUSR, e2_wdog_stat_reg_show, e2_wdog_stat_reg_store);
static DEVICE_ATTR(e3_ctrl_reg, S_IRUGO|S_IWUSR, e3_ctrl_reg_show, e3_ctrl_reg_store);
static DEVICE_ATTR(e3_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e3_wdog_ctrl_reg_show, e3_wdog_ctrl_reg_store);
static DEVICE_ATTR(e3_wdog_stat_reg, S_IRUGO|S_IWUSR, e3_wdog_stat_reg_show, e3_wdog_stat_reg_store);
static DEVICE_ATTR(e4_ctrl_reg, S_IRUGO|S_IWUSR, e4_ctrl_reg_show, e4_ctrl_reg_store);
static DEVICE_ATTR(e4_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e4_wdog_ctrl_reg_show, e4_wdog_ctrl_reg_store);
static DEVICE_ATTR(e4_wdog_stat_reg, S_IRUGO|S_IWUSR, e4_wdog_stat_reg_show, e4_wdog_stat_reg_store);
static DEVICE_ATTR(e5_ctrl_reg, S_IRUGO|S_IWUSR, e5_ctrl_reg_show, e5_ctrl_reg_store);
static DEVICE_ATTR(e5_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e5_wdog_ctrl_reg_show, e5_wdog_ctrl_reg_store);
static DEVICE_ATTR(e5_wdog_stat_reg, S_IRUGO|S_IWUSR, e5_wdog_stat_reg_show, e5_wdog_stat_reg_store);
static DEVICE_ATTR(e6_ctrl_reg, S_IRUGO|S_IWUSR, e6_ctrl_reg_show, e6_ctrl_reg_store);
static DEVICE_ATTR(e6_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e6_wdog_ctrl_reg_show, e6_wdog_ctrl_reg_store);
static DEVICE_ATTR(e6_wdog_stat_reg, S_IRUGO|S_IWUSR, e6_wdog_stat_reg_show, e6_wdog_stat_reg_store);
static DEVICE_ATTR(e7_ctrl_reg, S_IRUGO|S_IWUSR, e7_ctrl_reg_show, e7_ctrl_reg_store);
static DEVICE_ATTR(e7_wdog_ctrl_reg, S_IRUGO|S_IWUSR, e7_wdog_ctrl_reg_show, e7_wdog_ctrl_reg_store);
static DEVICE_ATTR(e7_wdog_stat_reg, S_IRUGO|S_IWUSR, e7_wdog_stat_reg_show, e7_wdog_stat_reg_store);
static DEVICE_ATTR(e0cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e0cfg_spi_muxsel_reg_show, e0cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e1cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e1cfg_spi_muxsel_reg_show, e1cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e2cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e2cfg_spi_muxsel_reg_show, e2cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e3cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e3cfg_spi_muxsel_reg_show, e3cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e4cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e4cfg_spi_muxsel_reg_show, e4cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e5cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e5cfg_spi_muxsel_reg_show, e5cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e6cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e6cfg_spi_muxsel_reg_show, e6cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e7cfg_spi_muxsel_reg, S_IRUGO|S_IWUSR, e7cfg_spi_muxsel_reg_show, e7cfg_spi_muxsel_reg_store);
static DEVICE_ATTR(e0spi_muxsel_reg, S_IRUGO|S_IWUSR, e0spi_muxsel_reg_show, e0spi_muxsel_reg_store);
static DEVICE_ATTR(e1spi_muxsel_reg, S_IRUGO|S_IWUSR, e1spi_muxsel_reg_show, e1spi_muxsel_reg_store);
static DEVICE_ATTR(e2spi_muxsel_reg, S_IRUGO|S_IWUSR, e2spi_muxsel_reg_show, e2spi_muxsel_reg_store);
static DEVICE_ATTR(e3spi_muxsel_reg, S_IRUGO|S_IWUSR, e3spi_muxsel_reg_show, e3spi_muxsel_reg_store);
static DEVICE_ATTR(e4spi_muxsel_reg, S_IRUGO|S_IWUSR, e4spi_muxsel_reg_show, e4spi_muxsel_reg_store);
static DEVICE_ATTR(e5spi_muxsel_reg, S_IRUGO|S_IWUSR, e5spi_muxsel_reg_show, e5spi_muxsel_reg_store);
static DEVICE_ATTR(e6spi_muxsel_reg, S_IRUGO|S_IWUSR, e6spi_muxsel_reg_show, e6spi_muxsel_reg_store);
static DEVICE_ATTR(e7spi_muxsel_reg, S_IRUGO|S_IWUSR, e7spi_muxsel_reg_show, e7spi_muxsel_reg_store);
static DEVICE_ATTR(e0_uart_rxdata_reg, S_IRUGO, e0_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e0_uart_txdata_reg, S_IRUGO, e0_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e0_uart_stat_reg, S_IRUGO, e0_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e0_uart_ctrl_reg, S_IRUGO, e0_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e1_uart_rxdata_reg, S_IRUGO, e1_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e1_uart_txdata_reg, S_IRUGO, e1_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e1_uart_stat_reg, S_IRUGO, e1_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e1_uart_ctrl_reg, S_IRUGO, e1_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e2_uart_rxdata_reg, S_IRUGO, e2_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e2_uart_txdata_reg, S_IRUGO, e2_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e2_uart_stat_reg, S_IRUGO, e2_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e2_uart_ctrl_reg, S_IRUGO, e2_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e3_uart_rxdata_reg, S_IRUGO, e3_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e3_uart_txdata_reg, S_IRUGO, e3_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e3_uart_stat_reg, S_IRUGO, e3_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e3_uart_ctrl_reg, S_IRUGO, e3_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e4_uart_rxdata_reg, S_IRUGO, e4_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e4_uart_txdata_reg, S_IRUGO, e4_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e4_uart_stat_reg, S_IRUGO, e4_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e4_uart_ctrl_reg, S_IRUGO, e4_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e5_uart_rxdata_reg, S_IRUGO, e5_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e5_uart_txdata_reg, S_IRUGO, e5_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e5_uart_stat_reg, S_IRUGO, e5_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e5_uart_ctrl_reg, S_IRUGO, e5_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e6_uart_rxdata_reg, S_IRUGO, e6_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e6_uart_txdata_reg, S_IRUGO, e6_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e6_uart_stat_reg, S_IRUGO, e6_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e6_uart_ctrl_reg, S_IRUGO, e6_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(e7_uart_rxdata_reg, S_IRUGO, e7_uart_rxdata_reg_show, NULL);
static DEVICE_ATTR(e7_uart_txdata_reg, S_IRUGO, e7_uart_txdata_reg_show, NULL);
static DEVICE_ATTR(e7_uart_stat_reg, S_IRUGO, e7_uart_stat_reg_show, NULL);
static DEVICE_ATTR(e7_uart_ctrl_reg, S_IRUGO, e7_uart_ctrl_reg_show, NULL);
static DEVICE_ATTR(int0_en_reg, S_IRUGO|S_IWUSR, int0_en_reg_show, int0_en_reg_store);
static DEVICE_ATTR(int1_en_reg, S_IRUGO|S_IWUSR, int1_en_reg_show, int1_en_reg_store);
static DEVICE_ATTR(int2_en_reg, S_IRUGO|S_IWUSR, int2_en_reg_show, int2_en_reg_store);
static DEVICE_ATTR(int3_en_reg, S_IRUGO|S_IWUSR, int3_en_reg_show, int3_en_reg_store);
static DEVICE_ATTR(int4_en_reg, S_IRUGO|S_IWUSR, int4_en_reg_show, int4_en_reg_store);
static DEVICE_ATTR(int5_en_reg, S_IRUGO|S_IWUSR, int5_en_reg_show, int5_en_reg_store);
static DEVICE_ATTR(int6_en_reg, S_IRUGO|S_IWUSR, int6_en_reg_show, int6_en_reg_store);
static DEVICE_ATTR(int7_en_reg, S_IRUGO|S_IWUSR, int7_en_reg_show, int7_en_reg_store);
static DEVICE_ATTR(int8_en_reg, S_IRUGO|S_IWUSR, int8_en_reg_show, int8_en_reg_store);
static DEVICE_ATTR(int9_en_reg, S_IRUGO|S_IWUSR, int9_en_reg_show, int9_en_reg_store);
static DEVICE_ATTR(int10_en_reg, S_IRUGO|S_IWUSR, int10_en_reg_show, int10_en_reg_store);
static DEVICE_ATTR(int11_en_reg, S_IRUGO|S_IWUSR, int11_en_reg_show, int11_en_reg_store);
static DEVICE_ATTR(int12_en_reg, S_IRUGO|S_IWUSR, int12_en_reg_show, int12_en_reg_store);
static DEVICE_ATTR(int13_en_reg, S_IRUGO|S_IWUSR, int13_en_reg_show, int13_en_reg_store);
static DEVICE_ATTR(int14_en_reg, S_IRUGO|S_IWUSR, int14_en_reg_show, int14_en_reg_store);
static DEVICE_ATTR(int15_en_reg, S_IRUGO|S_IWUSR, int15_en_reg_show, int15_en_reg_store);
static DEVICE_ATTR(int0_pend_reg, S_IRUGO|S_IWUSR, int0_pend_reg_show, int0_pend_reg_store);
static DEVICE_ATTR(int1_pend_reg, S_IRUGO|S_IWUSR, int1_pend_reg_show, int1_pend_reg_store);
static DEVICE_ATTR(int2_pend_reg, S_IRUGO|S_IWUSR, int2_pend_reg_show, int2_pend_reg_store);
static DEVICE_ATTR(int3_pend_reg, S_IRUGO|S_IWUSR, int3_pend_reg_show, int3_pend_reg_store);
static DEVICE_ATTR(int4_pend_reg, S_IRUGO|S_IWUSR, int4_pend_reg_show, int4_pend_reg_store);
static DEVICE_ATTR(int5_pend_reg, S_IRUGO|S_IWUSR, int5_pend_reg_show, int5_pend_reg_store);
static DEVICE_ATTR(int6_pend_reg, S_IRUGO|S_IWUSR, int6_pend_reg_show, int6_pend_reg_store);
static DEVICE_ATTR(int7_pend_reg, S_IRUGO|S_IWUSR, int7_pend_reg_show, int7_pend_reg_store);
static DEVICE_ATTR(int8_pend_reg, S_IRUGO|S_IWUSR, int8_pend_reg_show, int8_pend_reg_store);
static DEVICE_ATTR(int9_pend_reg, S_IRUGO|S_IWUSR, int9_pend_reg_show, int9_pend_reg_store);
static DEVICE_ATTR(int10_pend_reg, S_IRUGO|S_IWUSR, int10_pend_reg_show, int10_pend_reg_store);
static DEVICE_ATTR(int11_pend_reg, S_IRUGO|S_IWUSR, int11_pend_reg_show, int11_pend_reg_store);
static DEVICE_ATTR(int12_pend_reg, S_IRUGO|S_IWUSR, int12_pend_reg_show, int12_pend_reg_store);
static DEVICE_ATTR(int13_pend_reg, S_IRUGO|S_IWUSR, int13_pend_reg_show, int13_pend_reg_store);
static DEVICE_ATTR(int14_pend_reg, S_IRUGO|S_IWUSR, int14_pend_reg_show, int14_pend_reg_store);
static DEVICE_ATTR(int15_pend_reg, S_IRUGO|S_IWUSR, int15_pend_reg_show, int15_pend_reg_store);
static DEVICE_ATTR(bmc_int0_en_reg, S_IRUGO|S_IWUSR, bmc_int0_en_reg_show, bmc_int0_en_reg_store);
static DEVICE_ATTR(bmc_int1_en_reg, S_IRUGO|S_IWUSR, bmc_int1_en_reg_show, bmc_int1_en_reg_store);
static DEVICE_ATTR(bmc_int2_en_reg, S_IRUGO|S_IWUSR, bmc_int2_en_reg_show, bmc_int2_en_reg_store);
static DEVICE_ATTR(bmc_int3_en_reg, S_IRUGO|S_IWUSR, bmc_int3_en_reg_show, bmc_int3_en_reg_store);
static DEVICE_ATTR(bmc_int4_en_reg, S_IRUGO|S_IWUSR, bmc_int4_en_reg_show, bmc_int4_en_reg_store);
static DEVICE_ATTR(bmc_int5_en_reg, S_IRUGO|S_IWUSR, bmc_int5_en_reg_show, bmc_int5_en_reg_store);
static DEVICE_ATTR(bmc_int6_en_reg, S_IRUGO|S_IWUSR, bmc_int6_en_reg_show, bmc_int6_en_reg_store);
static DEVICE_ATTR(bmc_int7_en_reg, S_IRUGO|S_IWUSR, bmc_int7_en_reg_show, bmc_int7_en_reg_store);
static DEVICE_ATTR(bmc_int8_en_reg, S_IRUGO|S_IWUSR, bmc_int8_en_reg_show, bmc_int8_en_reg_store);
static DEVICE_ATTR(bmc_int9_en_reg, S_IRUGO|S_IWUSR, bmc_int9_en_reg_show, bmc_int9_en_reg_store);
static DEVICE_ATTR(bmc_int10_en_reg, S_IRUGO|S_IWUSR, bmc_int10_en_reg_show, bmc_int10_en_reg_store);
static DEVICE_ATTR(bmc_int11_en_reg, S_IRUGO|S_IWUSR, bmc_int11_en_reg_show, bmc_int11_en_reg_store);
static DEVICE_ATTR(bmc_int12_en_reg, S_IRUGO|S_IWUSR, bmc_int12_en_reg_show, bmc_int12_en_reg_store);
static DEVICE_ATTR(bmc_int13_en_reg, S_IRUGO|S_IWUSR, bmc_int13_en_reg_show, bmc_int13_en_reg_store);
static DEVICE_ATTR(bmc_int14_en_reg, S_IRUGO|S_IWUSR, bmc_int14_en_reg_show, bmc_int14_en_reg_store);
static DEVICE_ATTR(bmc_int15_en_reg, S_IRUGO|S_IWUSR, bmc_int15_en_reg_show, bmc_int15_en_reg_store);
static DEVICE_ATTR(bmc_int0_pend_reg, S_IRUGO|S_IWUSR, bmc_int0_pend_reg_show, bmc_int0_pend_reg_store);
static DEVICE_ATTR(bmc_int1_pend_reg, S_IRUGO|S_IWUSR, bmc_int1_pend_reg_show, bmc_int1_pend_reg_store);
static DEVICE_ATTR(bmc_int2_pend_reg, S_IRUGO|S_IWUSR, bmc_int2_pend_reg_show, bmc_int2_pend_reg_store);
static DEVICE_ATTR(bmc_int3_pend_reg, S_IRUGO|S_IWUSR, bmc_int3_pend_reg_show, bmc_int3_pend_reg_store);
static DEVICE_ATTR(bmc_int4_pend_reg, S_IRUGO|S_IWUSR, bmc_int4_pend_reg_show, bmc_int4_pend_reg_store);
static DEVICE_ATTR(bmc_int5_pend_reg, S_IRUGO|S_IWUSR, bmc_int5_pend_reg_show, bmc_int5_pend_reg_store);
static DEVICE_ATTR(bmc_int6_pend_reg, S_IRUGO|S_IWUSR, bmc_int6_pend_reg_show, bmc_int6_pend_reg_store);
static DEVICE_ATTR(bmc_int7_pend_reg, S_IRUGO|S_IWUSR, bmc_int7_pend_reg_show, bmc_int7_pend_reg_store);
static DEVICE_ATTR(bmc_int8_pend_reg, S_IRUGO|S_IWUSR, bmc_int8_pend_reg_show, bmc_int8_pend_reg_store);
static DEVICE_ATTR(bmc_int9_pend_reg, S_IRUGO|S_IWUSR, bmc_int9_pend_reg_show, bmc_int9_pend_reg_store);
static DEVICE_ATTR(bmc_int10_pend_reg, S_IRUGO|S_IWUSR, bmc_int10_pend_reg_show, bmc_int10_pend_reg_store);
static DEVICE_ATTR(bmc_int11_pend_reg, S_IRUGO|S_IWUSR, bmc_int11_pend_reg_show, bmc_int11_pend_reg_store);
static DEVICE_ATTR(bmc_int12_pend_reg, S_IRUGO|S_IWUSR, bmc_int12_pend_reg_show, bmc_int12_pend_reg_store);
static DEVICE_ATTR(bmc_int13_pend_reg, S_IRUGO|S_IWUSR, bmc_int13_pend_reg_show, bmc_int13_pend_reg_store);
static DEVICE_ATTR(bmc_int14_pend_reg, S_IRUGO|S_IWUSR, bmc_int14_pend_reg_show, bmc_int14_pend_reg_store);
static DEVICE_ATTR(bmc_int15_pend_reg, S_IRUGO|S_IWUSR, bmc_int15_pend_reg_show, bmc_int15_pend_reg_store);
static DEVICE_ATTR(rtc_clock, S_IRUGO|S_IWUSR, rtc_clock_show, rtc_clock_store);
static DEVICE_ATTR(rtc_ckspeed_reg, S_IRUGO, rtc_ckspeed_reg_show, rtc_ckspeed_reg_store);
static DEVICE_ATTR(rtc_hacktime_hh, S_IRUGO|S_IWUSR, rtc_hacktime_hh_show, rtc_hacktime_hh_store);
static DEVICE_ATTR(rtc_hacktime_mm, S_IRUGO|S_IWUSR, rtc_hacktime_mm_show, rtc_hacktime_mm_store);
static DEVICE_ATTR(rtc_hacktime_ss, S_IRUGO|S_IWUSR, rtc_hacktime_ss_show, rtc_hacktime_ss_store);
static DEVICE_ATTR(rtc_hackcnthi_32, S_IRUGO, rtc_hackcnthi_32_show, NULL);
static DEVICE_ATTR(rtc_hackcntlo_8, S_IRUGO, rtc_hackcntlo_8_show, NULL);
static DEVICE_ATTR(rtc_date, S_IRUGO|S_IWUSR, rtc_date_show, rtc_date_store);

static struct attribute *fpga1_attrs[] = {
    &dev_attr_fpga_id.attr,
    &dev_attr_fpga_rev.attr,
    &dev_attr_board_rev.attr,
    &dev_attr_led_debug_0_reg.attr,
    &dev_attr_led_debug_1_reg.attr,
    &dev_attr_led_debug_2_reg.attr,
    &dev_attr_led_debug_3_reg.attr,
    &dev_attr_debug_0_reg.attr,
    &dev_attr_debug_1_reg.attr,
    &dev_attr_debug_2_reg.attr,
    &dev_attr_debug_3_reg.attr,
    &dev_attr_elba_reset_cause_0_reg.attr,
    &dev_attr_elba_reset_cause_1_reg.attr,
    &dev_attr_elba_reset_cause_2_reg.attr,
    &dev_attr_elba_reset_cause_3_reg.attr,
    &dev_attr_elba_reset_cause_4_reg.attr,
    &dev_attr_elba_reset_cause_5_reg.attr,
    &dev_attr_elba_reset_cause_6_reg.attr,
    &dev_attr_elba_reset_cause_7_reg.attr,
    &dev_attr_misc_ctrl_reg.attr,
    &dev_attr_flsh_ctrl_reg.attr,
    &dev_attr_e0_ctrl_reg.attr,
    &dev_attr_e0_wdog_ctrl_reg.attr,
    &dev_attr_e0_wdog_stat_reg.attr,
    &dev_attr_e1_ctrl_reg.attr,
    &dev_attr_e1_wdog_ctrl_reg.attr,
    &dev_attr_e1_wdog_stat_reg.attr,
    &dev_attr_e2_ctrl_reg.attr,
    &dev_attr_e2_wdog_ctrl_reg.attr,
    &dev_attr_e2_wdog_stat_reg.attr,
    &dev_attr_e3_ctrl_reg.attr,
    &dev_attr_e3_wdog_ctrl_reg.attr,
    &dev_attr_e3_wdog_stat_reg.attr,
    &dev_attr_e4_ctrl_reg.attr,
    &dev_attr_e4_wdog_ctrl_reg.attr,
    &dev_attr_e4_wdog_stat_reg.attr,
    &dev_attr_e5_ctrl_reg.attr,
    &dev_attr_e5_wdog_ctrl_reg.attr,
    &dev_attr_e5_wdog_stat_reg.attr,
    &dev_attr_e6_ctrl_reg.attr,
    &dev_attr_e6_wdog_ctrl_reg.attr,
    &dev_attr_e6_wdog_stat_reg.attr,
    &dev_attr_e7_ctrl_reg.attr,
    &dev_attr_e7_wdog_ctrl_reg.attr,
    &dev_attr_e7_wdog_stat_reg.attr,
    &dev_attr_e0_uart_rxdata_reg.attr,
    &dev_attr_e0_uart_txdata_reg.attr,
    &dev_attr_e0_uart_stat_reg.attr,
    &dev_attr_e0_uart_ctrl_reg.attr,
    &dev_attr_e1_uart_rxdata_reg.attr,
    &dev_attr_e1_uart_txdata_reg.attr,
    &dev_attr_e1_uart_stat_reg.attr,
    &dev_attr_e1_uart_ctrl_reg.attr,
    &dev_attr_e2_uart_rxdata_reg.attr,
    &dev_attr_e2_uart_txdata_reg.attr,
    &dev_attr_e2_uart_stat_reg.attr,
    &dev_attr_e2_uart_ctrl_reg.attr,
    &dev_attr_e3_uart_rxdata_reg.attr,
    &dev_attr_e3_uart_txdata_reg.attr,
    &dev_attr_e3_uart_stat_reg.attr,
    &dev_attr_e3_uart_ctrl_reg.attr,
    &dev_attr_e4_uart_rxdata_reg.attr,
    &dev_attr_e4_uart_txdata_reg.attr,
    &dev_attr_e4_uart_stat_reg.attr,
    &dev_attr_e4_uart_ctrl_reg.attr,
    &dev_attr_e5_uart_rxdata_reg.attr,
    &dev_attr_e5_uart_txdata_reg.attr,
    &dev_attr_e5_uart_stat_reg.attr,
    &dev_attr_e5_uart_ctrl_reg.attr,
    &dev_attr_e6_uart_rxdata_reg.attr,
    &dev_attr_e6_uart_txdata_reg.attr,
    &dev_attr_e6_uart_stat_reg.attr,
    &dev_attr_e6_uart_ctrl_reg.attr,
    &dev_attr_e7_uart_rxdata_reg.attr,
    &dev_attr_e7_uart_txdata_reg.attr,
    &dev_attr_e7_uart_stat_reg.attr,
    &dev_attr_e7_uart_ctrl_reg.attr,
    &dev_attr_soft_reset_reg.attr,
    &dev_attr_e7cfg_spi_muxsel_reg.attr,
    &dev_attr_e6cfg_spi_muxsel_reg.attr,
    &dev_attr_e5cfg_spi_muxsel_reg.attr,
    &dev_attr_e4cfg_spi_muxsel_reg.attr,
    &dev_attr_e3cfg_spi_muxsel_reg.attr,
    &dev_attr_e2cfg_spi_muxsel_reg.attr,
    &dev_attr_e1cfg_spi_muxsel_reg.attr,
    &dev_attr_e0cfg_spi_muxsel_reg.attr,
    &dev_attr_e0spi_muxsel_reg.attr,
    &dev_attr_e1spi_muxsel_reg.attr,
    &dev_attr_e2spi_muxsel_reg.attr,
    &dev_attr_e3spi_muxsel_reg.attr,
    &dev_attr_e4spi_muxsel_reg.attr,
    &dev_attr_e5spi_muxsel_reg.attr,
    &dev_attr_e6spi_muxsel_reg.attr,
    &dev_attr_e7spi_muxsel_reg.attr,
    &dev_attr_int0_en_reg.attr,
    &dev_attr_int1_en_reg.attr,
    &dev_attr_int2_en_reg.attr,
    &dev_attr_int3_en_reg.attr,
    &dev_attr_int4_en_reg.attr,
    &dev_attr_int5_en_reg.attr,
    &dev_attr_int6_en_reg.attr,
    &dev_attr_int7_en_reg.attr,
    &dev_attr_int8_en_reg.attr,
    &dev_attr_int9_en_reg.attr,
    &dev_attr_int10_en_reg.attr,
    &dev_attr_int11_en_reg.attr,
    &dev_attr_int12_en_reg.attr,
    &dev_attr_int13_en_reg.attr,
    &dev_attr_int14_en_reg.attr,
    &dev_attr_int15_en_reg.attr,
    &dev_attr_int0_pend_reg.attr,
    &dev_attr_int1_pend_reg.attr,
    &dev_attr_int2_pend_reg.attr,
    &dev_attr_int3_pend_reg.attr,
    &dev_attr_int4_pend_reg.attr,
    &dev_attr_int5_pend_reg.attr,
    &dev_attr_int6_pend_reg.attr,
    &dev_attr_int7_pend_reg.attr,
    &dev_attr_int8_pend_reg.attr,
    &dev_attr_int9_pend_reg.attr,
    &dev_attr_int10_pend_reg.attr,
    &dev_attr_int11_pend_reg.attr,
    &dev_attr_int12_pend_reg.attr,
    &dev_attr_int13_pend_reg.attr,
    &dev_attr_int14_pend_reg.attr,
    &dev_attr_int15_pend_reg.attr,
    &dev_attr_bmc_int0_en_reg.attr,
    &dev_attr_bmc_int1_en_reg.attr,
    &dev_attr_bmc_int2_en_reg.attr,
    &dev_attr_bmc_int3_en_reg.attr,
    &dev_attr_bmc_int4_en_reg.attr,
    &dev_attr_bmc_int5_en_reg.attr,
    &dev_attr_bmc_int6_en_reg.attr,
    &dev_attr_bmc_int7_en_reg.attr,
    &dev_attr_bmc_int8_en_reg.attr,
    &dev_attr_bmc_int9_en_reg.attr,
    &dev_attr_bmc_int10_en_reg.attr,
    &dev_attr_bmc_int11_en_reg.attr,
    &dev_attr_bmc_int12_en_reg.attr,
    &dev_attr_bmc_int13_en_reg.attr,
    &dev_attr_bmc_int14_en_reg.attr,
    &dev_attr_bmc_int15_en_reg.attr,
    &dev_attr_bmc_int0_pend_reg.attr,
    &dev_attr_bmc_int1_pend_reg.attr,
    &dev_attr_bmc_int2_pend_reg.attr,
    &dev_attr_bmc_int3_pend_reg.attr,
    &dev_attr_bmc_int4_pend_reg.attr,
    &dev_attr_bmc_int5_pend_reg.attr,
    &dev_attr_bmc_int6_pend_reg.attr,
    &dev_attr_bmc_int7_pend_reg.attr,
    &dev_attr_bmc_int8_pend_reg.attr,
    &dev_attr_bmc_int9_pend_reg.attr,
    &dev_attr_bmc_int10_pend_reg.attr,
    &dev_attr_bmc_int11_pend_reg.attr,
    &dev_attr_bmc_int12_pend_reg.attr,
    &dev_attr_bmc_int13_pend_reg.attr,
    &dev_attr_bmc_int14_pend_reg.attr,
    &dev_attr_bmc_int15_pend_reg.attr,
    &dev_attr_rtc_clock.attr,
    &dev_attr_rtc_ckspeed_reg.attr,
    &dev_attr_rtc_hacktime_hh.attr,
    &dev_attr_rtc_hacktime_mm.attr,
    &dev_attr_rtc_hacktime_ss.attr,
    &dev_attr_rtc_hackcnthi_32.attr,
    &dev_attr_rtc_hackcntlo_8.attr,
    &dev_attr_rtc_date.attr,
    NULL,
};

static struct attribute_group fpga1_attr_group = {
   .attrs  = fpga1_attrs,
};

static int
amd_fpga_elba_probe(struct pci_dev *pdev,
                     const struct pci_device_id *id) {
    void __iomem *const *pci_tbl;
    char 	 *i2c_base_addr;
    int   	 i,ret;

    ret = pcim_enable_device(pdev);
    if (ret) {
        dev_err(&pdev->dev, "Failed to enable FPGA I2C PCI device ret=%d\n",
                ret);
        return ret;
    }
    if (!pdev->is_busmaster) {
        pci_set_master(pdev);
    }

    ret = pcim_iomap_regions(pdev, 1, AMD_FPGA_ELBA);
    if (ret) {
        dev_err(&pdev->dev, "Failed to ioremap rc=%d\n",
                ret);
        pci_disable_device(pdev);
	return ret;
    }

    pci_tbl       = pcim_iomap_table(pdev);
    fpga_membase  = pci_tbl[0];

    i2c_base_addr = (char*)fpga_membase;
    i2c_base_addr += FPGA1_I2C_ADDRESS_START;

    for (i = 0; i < FPGA1_NUM_I2C_CONTROLLERS; i++) {
        ocores_i2c_probe(pdev, i2c_base_addr, i,
			(i + FPGA0_NUM_I2C_CONTROLLERS),
			FPGA1_I2C_ADDRESS_START,
			FPGA1_I2C_REGISTERS_ADDRESS_SIZE);
        i2c_base_addr += FPGA1_I2C_REGISTERS_ADDRESS_SIZE;
    }

    ret = sysfs_create_group(&pdev->dev.kobj, &fpga1_attr_group);
    if (ret) {
        sysfs_remove_group(&pdev->dev.kobj, &fpga1_attr_group);
        dev_err(&pdev->dev, "Failed to create attr group\n");
    }

    return ret;
}

static void
amd_fpga_elba_remove(struct pci_dev *pdev) {
    int i;

    for (i = FPGA0_NUM_I2C_CONTROLLERS; i < NUM_I2C_CONTROLLERS; i++) {
		ocores_i2c_remove(pdev, i);
    }

    pcim_iounmap_regions(pdev, 1);
    pci_disable_device(pdev);
}

static const struct pci_device_id amd_fpga_elba_ids[] = {
    {PCI_DEVICE(PCI_VENDOR_ID_AMD_FPGA, PCI_DEVICE_ID_AMD_FPGA_ELBA)},
    {0}
};


static struct pci_driver amd_fpga_elba_driver = {
    .name        = "amd-lipari-fpga-elba",
    .id_table    = amd_fpga_elba_ids,
    .probe       = amd_fpga_elba_probe,
    .remove      = amd_fpga_elba_remove,
};

static int __init amd_fpga_elba_init(void) {
    return pci_register_driver(&amd_fpga_elba_driver);
}

static void __exit amd_fpga_elba_exit(void) {
    pci_unregister_driver(&amd_fpga_elba_driver);
}

module_init(amd_fpga_elba_init);
module_exit(amd_fpga_elba_exit);

MODULE_DESCRIPTION("AMD FPGA I2C and Elba Registers");
MODULE_LICENSE("GPL");

MODULE_AUTHOR("Mushtaq Khan <Mushtaq.khan@amd.com>");
