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
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
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
#define JTAG_TST_CMD	0x0

#define MDIO_INST0_CRTL_LO_REG		0x6
#define MDIO_INST0_CRTL_HI_REG		0x7
#define MDIO_INST0_DATA_LO_REG		0x8
#define MDIO_INST0_DATA_HI_REG		0x9
#define MDIO_INST1_CRTL_LO_REG		0xA
#define MDIO_INST1_CRTL_HI_REG		0xB
#define MDIO_INST1_DATA_LO_REG		0xC
#define MDIO_INST1_DATA_HI_REG		0xD
#define MDIO_ACC_ENA				0x1
#define MDIO_RD_ENA					0x2
#define MDIO_WR_ENA					0x4

#ifndef DWORD
#define DWORD unsigned int 
#endif

#ifndef ULONGLONG
#define ULONGLONG unsigned long long int
#endif

#ifndef ULONG
#define ULONG unsigned int
#endif

#ifndef BYTE
#define BYTE unsigned char
#endif

#define CFG_SIZE	(16*2175)

extern const BYTE SPIDATALENGTH;//3 digit command + 8 digit address
extern const BYTE READ;//110xxxxx
extern const BYTE WRITE;//101xxxxx
extern const BYTE WREN;//10011xxx
extern const BYTE ERAL;//10010xxx
//declare for BAD command
extern const BYTE AA_ECHO_CMD_1;
extern const BYTE AB_ECHO_CMD_2;
extern const BYTE BAD_COMMAND_RESPONSE;
//declare for MPSSE command
extern const BYTE MSB_RISING_EDGE_CLOCK_BYTE_OUT;
extern const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_OUT;
extern const BYTE MSB_RISING_EDGE_CLOCK_BIT_OUT;
extern const BYTE MSB_FALLING_EDGE_CLOCK_BIT_OUT;
extern const BYTE MSB_RISING_EDGE_CLOCK_BYTE_IN;
extern const BYTE MSB_RISING_EDGE_CLOCK_BIT_IN;
extern const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_IN;
extern const BYTE MSB_FALLING_EDGE_CLOCK_BIT_IN;

extern FT_HANDLE ftHandle_a;
extern FT_HANDLE ftHandle;
extern unsigned char lsc_idcode_cmd[4];
extern unsigned char lsc_enable_cmd[4];
extern unsigned char lsc_erase_cmd[4];
extern unsigned char lsc_init_cmd[4];
extern unsigned char lsc_disable_cmd[3];
extern unsigned char lsc_prog_done_cmd[4];
extern unsigned char lsc_cfg_add_cmd[4];
extern unsigned char lsc_read_cmd[4];
extern unsigned char lsc_acc_mode_cmd[3];
extern unsigned char lsc_refresh_cmd[3];
extern unsigned char lsc_no_op_cmd[4];

extern BYTE 	OutputBuffer[512];
extern DWORD	dwNumBytesToSend;
extern DWORD	dwNumBytesSent;
extern DWORD 	dwNumBytesRead;

extern BYTE	is_spi_flash;
extern BYTE	is_jtag_flash;
extern BYTE	is_mdio;
extern BYTE	is_jtag;
extern BYTE   setup_reg[3];
extern BYTE   setup_spi[3];
extern BYTE   ena_lpbk[1];
extern BYTE   dis_lpbk[1];
extern BYTE   setClock[3];
extern BYTE   transceive[3];
extern BYTE   rst_irscan[3];
extern BYTE   mod_sel[5];
extern BYTE   oneclock_high[3];
extern BYTE   oneclock_low[3];
extern BYTE   updateir_shiftdr[3];
extern BYTE   shiftdr[2];
extern BYTE   updatedr_reset[3];
extern BYTE   tms_low[3];
extern BYTE   tms_high[3];
extern BYTE   test1[6];
extern BYTE   test2[7];
extern BYTE   cpu_wr[15];
extern BYTE   cpu_rd[11];
extern BYTE   cpu_res[13];
extern BYTE   con_red[5];

FT_STATUS jtag_init(int portNum);
FT_STATUS jtag_id(DWORD inst, DWORD* data);
FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag);
FT_STATUS jtag_write(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_tst(DWORD inst, BYTE enable);
void jtag_close();
void jtag_recover();
DWORD jtag_read(DWORD inst, ULONGLONG address, DWORD flag);
FT_STATUS jtag_reset(DWORD inst);
FT_STATUS jtag_enable(DWORD inst);
ULONGLONG xtoi(char *hexstring);
void queue_clear(FT_HANDLE ftHandle);
int queue_read(FT_HANDLE ftHandle, DWORD* data);
FT_STATUS sendJtagCommand(FT_HANDLE ftHandle, BYTE *sequence, const size_t length);
void spi_csena();
void spi_csdis();
FT_STATUS spi_reg_init();
FT_STATUS spi_mdio_init();
FT_STATUS spi_flash_init();
FT_STATUS jtag_flash_init();
FT_STATUS spi_init();
FT_STATUS spi_wr(BYTE address, BYTE data);
FT_STATUS spi_rd(BYTE address, BYTE* data);
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
int flash_program(BYTE* buf, int size);
int flash_erase();
int flash_read(BYTE* buf, DWORD size);
int flash_program_done();
int flash_refresh();
FT_STATUS mdio_wr(DWORD instance, DWORD dev_addr, DWORD offset, DWORD data);
FT_STATUS mdio_rd(DWORD instance, DWORD dev_addr, DWORD offset, DWORD* data);
unsigned int cpld_program(char* file_name);
unsigned int cpld_read(char* file_name);
void ftHandle_close();

extern char*	lock_file;
extern int		lock_fd;
extern struct stat st0;
extern struct stat st1;

#endif /* RELEASE_EXAMPLES_LOOPBACK_ACC_H_ */
