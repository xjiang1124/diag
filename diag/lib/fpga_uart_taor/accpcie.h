/*
 * accpcie.h
 *
 *  Created on: Feb 13, 2023
 *      Author: David Wang 
 */

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
#include <pthread.h>

typedef unsigned int            ULONG;
typedef ULONG                   *PULONG;
typedef unsigned long long int  ULONGLONG;

typedef ULONGLONG   FT_HANDLE;
typedef ULONG       FT_STATUS;

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
        FT_PORT_TAKEN,
        FT_ERROR_LOCKPORT,
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
#define J2C_SEM_BIT     0x00001

#define J2C_0_OFFSET     0xB00
#define J2C_0_CMD_REG    0x000
#define J2C_0_STAT_REG   0x004
#define J2C_0_ADDR0_REG  0x008
#define J2C_0_ADDR1_REG  0x00C
#define J2C_0_TXDATA_REG 0x010
#define J2C_0_RXDATA_REG 0x014
#define J2C_0_SEM_REG    0x018
#define J2C_0_MAGIC_REG  0x01C

//CSCO 0x10020, 0x11020, 0x12020, 0x13020
#define MTFUJI_JTAG0_BASE       0x10020
#define MTFUJI_JTAG_STRIDE       0x1000

//Taormina register offset
#define UART_0_OFFSET     0x7000
#define UART_1_OFFSET     0x7010
#define UART_INST_OFFSET  0x0010
#define UART_0_RXFIFO_REG 0x0000
#define UART_0_TXFIFO_REG 0x0004
#define UART_0_STAT_REG   0x0008
#define UART_0_CTRL_REG   0x000C
#define UART_0_TX_MUX_REG   0x0020
#define UART_1_TX_MUX_REG   0x0024

//Taormina FIFO COMMAND
#define UART_TXMUX_SET   0x80000000
#define UART_TXMUX_UNSET 0x00000000
#define UART_RESET_TXFIFO 0x00000001
#define UART_RESET_RXFIFO 0x00000002
#define UART_RESET_TXRXFIFO 0x00000003
#define UART_EN_INTERRUPT 0x00000010

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

#ifndef uint32_t
#define uint32_t unsigned int
#endif

extern FT_HANDLE ftHandle;

ULONGLONG xtoi(char *hexstring);
int FindPlatform(ULONGLONG * bar, uint32_t * entry);
ULONGLONG show_bar(void);
FT_STATUS jtag_init(DWORD portNum);
FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag);
FT_STATUS jtag_wg(ULONGLONG address, DWORD data);
FT_STATUS jtag_rg(ULONGLONG address, DWORD* data);
FT_STATUS jtag_reset(DWORD inst);
FT_STATUS jtag_enable(DWORD inst);
void set_verbosity(int);
void set_bar(ULONGLONG);
void jtag_close();
FT_STATUS spi_reg_init();
FT_STATUS spi_wr(BYTE address, BYTE data);
FT_STATUS spi_rd(BYTE address, BYTE* data);
void ftHandle_close();

