/*
 * acclib.h
 *
 *  Created on: Jan 9, 2018
 *      Author: xiaodhu
 */

#ifndef RELEASE_EXAMPLES_LOOPBACK_ACC_H_
#define RELEASE_EXAMPLES_LOOPBACK_ACC_H_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>
#include <sys/time.h>
#include <ctype.h>
#include "ftd2xx.h"


#define UNUSED_PARAMETER(x) (void)(x)

#define ARRAY_SIZE(x) (sizeof((x))/sizeof((x)[0]))

#define JTAG_WR_CMD	0x04
#define	JTAG_WR_OP	0x02
#define JTAG_RD_CMD	0x08
#define JTAG_RD_OP	0x01
#define JTAG_RES_CMD	0x10
#define JTAG_RES_OP		0x0
#define JTAG_RST_CMD	0x01
#define JTAG_ENA_CMD	0x02

const BYTE SPIDATALENGTH;//3 digit command + 8 digit address
const BYTE READ;//110xxxxx
const BYTE WRITE;//101xxxxx
const BYTE WREN;//10011xxx
const BYTE ERAL;//10010xxx
//declare for BAD command
const BYTE AA_ECHO_CMD_1;
const BYTE AB_ECHO_CMD_2;
const BYTE BAD_COMMAND_RESPONSE;
//declare for MPSSE command
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_OUT;
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_OUT;
const BYTE MSB_RISING_EDGE_CLOCK_BIT_OUT;
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_OUT;
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_IN;
const BYTE MSB_RISING_EDGE_CLOCK_BIT_IN;
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_IN;
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_IN;

extern FT_HANDLE ftHandle_a;
extern FT_HANDLE ftHandle;
extern unsigned char lsc_idcode_cmd[4];
extern unsigned char lsc_enable_cmd[4];
extern unsigned char lsc_earse_cmd[4];
extern unsigned char lsc_init_cmd[4];
extern unsigned char lsc_disable_cmd[3];
extern unsigned char lsc_prog_done_cmd[4];
extern unsigned char lsc_cfg_add_cmd[4];
extern unsigned char lsc_read_cmd[4];
extern unsigned char lsc_acc_mode_cmd[3];
extern unsigned char lsc_refresh_cmd[3];
extern unsigned char lsc_no_op_cmd[4];

BYTE 	OutputBuffer[512];
DWORD	dwNumBytesToSend;
DWORD	dwNumBytesSent;
DWORD 	dwNumBytesRead;

BYTE	is_spi_flash;

BYTE	is_mdio;

BYTE	is_jtag;

BYTE   setup_reg[3];

BYTE   setup_spi[3];

BYTE   ena_lpbk[1];

BYTE   dis_lpbk[1];

BYTE   setClock[3];

BYTE   transceive[3];

BYTE   rst_irscan[3];

BYTE   mod_sel[5];

BYTE   oneclock_high[3];

BYTE   oneclock_low[3];

BYTE   updateir_shiftdr[3];

BYTE   shiftdr[2];

BYTE   updatedr_reset[3];

BYTE   tms_low[3];

BYTE   tms_high[3];

BYTE   test1[6];

BYTE   test2[7];

BYTE   cpu_wr[15];

BYTE   cpu_rd[11];

BYTE   cpu_res[13];

BYTE   con_red[5];

FT_STATUS jtag_init();
FT_STATUS jtag_id(DWORD inst, DWORD* data);
FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag);
FT_STATUS jtag_reset(DWORD inst);
FT_STATUS jtag_enable(DWORD inst);
int xtoi(char *hexstring);
void queue_clear(FT_HANDLE ftHandle);
int queue_read(FT_HANDLE ftHandle, DWORD* data);
FT_STATUS sendJtagCommand(FT_HANDLE ftHandle, BYTE *sequence, const size_t length);
void spi_csena();
void spi_csdis();
FT_STATUS spi_init();
FT_STATUS spi_wr(FT_HANDLE ftHandle, BYTE address, BYTE data);
FT_STATUS spi_rd(FT_HANDLE ftHandle, BYTE address, BYTE* data);
FT_STATUS cpld_csena();
FT_STATUS cpld_csdis();
FT_STATUS flash_id_check();
FT_STATUS cpld_flash_wr(BYTE* data, int size);
FT_STATUS cpld_flash_wr_clear(BYTE* data, int size);
FT_STATUS cpld_flash_rd(BYTE* data, int size);
int flash_enable();
int flash_init();
int flash_disable();
int flash_check_status();
int flash_program();
int flash_read(BYTE* buf, DWORD size);
int flash_program_done();
int flash_refresh();
int flash_erase();

#endif /* RELEASE_EXAMPLES_LOOPBACK_ACC_H_ */
