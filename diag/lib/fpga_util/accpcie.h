/*
 * accpcie.h
 *
 *  Created on: Feb 13, 2023
 *      Author: David Wang 
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
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
#include "ftd2xx.h"

typedef unsigned int            ULONG;
typedef ULONG                   *PULONG;
typedef unsigned long long int  ULONGLONG;

/* typedef ULONGLONG   FT_HANDLE; */
typedef ULONG       FT_STATUS;

//
// Device status
//
/*
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
*/
#define J2C_NOP_COMMAND    0x0
#define J2C_RESET_COMMAND  0x1
#define J2C_ENABLE_COMMAND 0x2
#define J2C_WRITE_COMMAND  0x3
#define J2C_READ_COMMAND   0x4
#define J2C_RESP_COMMAND   0x5
#define J2C_WR_IR_COMMAND  0x6
#define J2C_WR_DR_COMMAND  0x7
#define J2C_WR_CONFIG_CMD  0x1000000
#define J2C_RESET_CMD      0x2000000

#define J2C_ASIC_TYPE_MASK   0x00000F00
#define J2C_PRESCALE_MASK    0x00FF0000
#define J2C_PRESCALE_CONF    0x00190000

#define J2C_RESP_BIT         0x00180000
#define J2C_RLAST_ERR_BIT    0x00040000
#define J2C_ID_BIT           0x00020000
#define J2C_VALID_BIT        0x00010000
#define J2C_RXFIFO_EMPTY     0x00000010
#define J2C_RXFIFO_HFULL     0x00000008
#define J2C_TXFIFO_FULL      0x00000004
#define J2C_TXFIFO_HEMPTY    0x00000002
#define J2C_SEM_BIT          0x00000001

#define J2C_OW_READ_CMD      0x00000000
#define J2C_OW_WRITE_CMD     0x00000010
#define J2C_OW_CMD_PENDING   0x00000020
#define J2C_OW_RESP_ERROR    0x00000007
#define J2C_OW_VALID         0x00000080
#define J2C_OW_INIT          0x00000100

#define J2C_OW_SECURE_MASK   0x00000004
#define J2C_OW_SECURE_SHIFT  2

#define J2C_0_OFFSET      0xA00
#define J2C_0_CMD_REG     0x000
#define J2C_0_STAT_REG    0x004
#define J2C_0_ADDR0_REG   0x008
#define J2C_0_ADDR1_REG   0x00C
#define J2C_0_TXDATA_REG  0x010
#define J2C_0_RXDATA_REG  0x014
#define J2C_0_SEM_REG     0x018
#define J2C_0_MAGIC_REG   0x01C
#define J2C_0_TXFIFO_REG  0x020
#define J2C_0_RXFIFO_REG  0x024
#define J2C_0_SIZE_REG    0x028
#define OW_0_INIT_REG     0x040
#define OW_0_CMD_REG      0x044
#define OW_0_STAT_REG     0x048
#define OW_0_DATA_REG     0x04C
#define OW_0_ADDR0_REG    0x050
#define OW_0_ADDR1_REG    0x054
#define OW_0_EOM_W_REG    0x058

#define UART_0_OFFSET     0x10000
#define UART_INST_OFFSET  0x0100
#define UART_0_RXDATA_REG 0x0000
#define UART_0_TXDATA_REG 0x0004
#define UART_0_STAT_REG   0x0008
#define UART_0_CTRL_REG   0x000C

#define UART_RESET_TXFIFO 0x0001
#define UART_RESET_RXFIFO 0x0002
#define UART_EN_INTERRUPT 0x0010

#define TRUE 1
#define FALSE 0

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

ULONGLONG xtoi(char *hexstring);
ULONGLONG show_bar(void);
FT_STATUS jtag_init(DWORD portNum);
FT_STATUS jtag_ow_init(void);
FT_STATUS jtag_ow_read(DWORD mode, DWORD size, ULONGLONG address, DWORD* data, DWORD flag);
FT_STATUS jtag_ow_write(DWORD mode, DWORD size, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS fpga_j2c_init(DWORD portNum);
FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag);
FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag);
FT_STATUS jtag_wr_dr(DWORD* tx_data, DWORD *rx_data, DWORD num_bits);
FT_STATUS jtag_wr_ir(DWORD* tx_data, DWORD num_bits);
FT_STATUS jtag_wg(ULONGLONG address, DWORD data);
FT_STATUS jtag_rg(ULONGLONG address, DWORD* data);
FT_STATUS jtag_reset(DWORD inst);
FT_STATUS jtag_enable(DWORD inst);
FT_STATUS sendJtagCommand(FT_HANDLE ftHandle, BYTE *sequence, const size_t length);
FT_STATUS jtag_clear(DWORD portNum);
void set_asic_target(char *asic_name);
void show_asic_target(char *asic_name);
void set_verbosity(int);
void set_bar(ULONGLONG);
void jtag_close();
FT_STATUS spi_init(DWORD portNum);
FT_STATUS spi_wr(ULONGLONG inst, DWORD address, DWORD data);
FT_STATUS spi_rd(ULONGLONG inst, DWORD address, DWORD *data);
void ftHandle_close();
void queue_clear(void);
void spi_csena();
void spi_csdis();

typedef struct _fpga_asic_target {
    char name[10];    /* asic name - no effect for code */
    int size;         /* j2c instance memory space */
    int addr_msb_pos; /* msb position for upper 32 bit address */
    int asic_enum;    /* code representing asic */
} FPGA_ASIC_TARGET;

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

extern BYTE     OutputBuffer[512];
extern DWORD    dwNumBytesToSend;
extern DWORD    dwNumBytesSent;
extern DWORD    dwNumBytesRead;

extern BYTE   setup_reg[3];
extern BYTE   setup_spi[6];
extern BYTE   ena_lpbk[1];
extern BYTE   dis_lpbk[1];
extern BYTE   setClock[3];

