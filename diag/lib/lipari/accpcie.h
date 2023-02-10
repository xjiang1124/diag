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
#include <sys/mman.h>
#include <fcntl.h>

typedef unsigned int            ULONG;
typedef ULONG                   *PULONG;
typedef unsigned long long int  ULONGLONG;

typedef ULONG   FT_HANDLE;
typedef ULONG   FT_STATUS;

//
// Device status
//
enum {
        FT_OK,
        FT_ERROR_OPEN_MEM,
        FT_ERROR_MAP_PCIE,
        FT_NO_HANDLE,
        FT_WRITE_FAILURE,
        FT_READ_FAILURE,
        FT_RESP_TIMEOUT,
        FT_INVALID_RESP,
        FT_ERROR_ID,
};

#define J2C_NOP_COMMAND    0x0
#define J2C_RESET_COMMAND  0x1
#define J2C_ENABLE_COMMAND 0x2
#define J2C_WRITE_COMMAND  0x3
#define J2C_READ_COMMAND   0x4
#define J2C_RESP_COMMAND   0x5

#define J2C_VALID_BIT   0x10000
#define J2C_ID_BIT      0x20000

#define J2C_0_CMD_REG    0xB00
#define J2C_0_STAT_REG   0xB04
#define J2C_0_ADDR0_REG  0xB08
#define J2C_0_ADDR1_REG  0xB0C
#define J2C_0_TXDATA_REG 0xB10
#define J2C_0_RXDATA_REG 0xB14
#define J2C_0_SEM_REG    0xB18
#define J2C_0_MAGIC_REG  0xB1C

#define UART_0_RXDATA_REG 0x1000
#define UART_0_TXDATA_REG 0x1004
#define UART_0_STAT_REG   0x1008
#define UART_0_CTRL_REG   0x100C

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

extern FT_HANDLE ftHandle;

extern BYTE 	OutputBuffer[512];
extern DWORD	dwNumBytesToSend;
extern DWORD	dwNumBytesSent;
extern DWORD 	dwNumBytesRead;

FT_STATUS jtag_init(DWORD portNum);
FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag);
void jtag_close();
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
