/*
 * Enable Multi-Protocol Synchronous Serial Engine (MPSSE) on an FTDI chip,
 * and use JTAG commands to loop DO back to DI.  Write a known sequence of 
 * bytes then expect to read them back.  Run this with an FT232H, FT2232D, 
 * FT2232H or FT4232H connected.  No additional hardware is needed.
 *
 * Build with:
 *     gcc jtag.c -o jtagloopback -Wall -Wextra -I..
 *         -lftd2xx -lpthread -lrt 
 *         -Wl,-rpath /usr/local/lib
 * 
 * Run with:
 *     sudo ./jtagloopback
 *
 * On Windows, build with:
 *     cl jtag.c ftd2xx.lib -I..
 * and run jtag.exe.
 */
#include "acc.h"

#define UNUSED_PARAMETER(x) (void)(x)

#define ARRAY_SIZE(x) (sizeof((x))/sizeof((x)[0]))
#define CHANNEL_A	0
#define CHANNEL_B	1

FT_HANDLE ftHandle		= NULL;
FT_HANDLE ftHandle_a	= NULL;

const BYTE SPIDATALENGTH = 11;//3 digit command + 8 digit address
const BYTE READ = '\x0B';//110xxxxx
const BYTE WRITE = '\x02';//101xxxxx
const BYTE WREN = '\x98';//10011xxx
const BYTE ERAL = '\x90';//10010xxx
//declare for BAD command
const BYTE AA_ECHO_CMD_1 = '\xAA';
const BYTE AB_ECHO_CMD_2 = '\xAB';
const BYTE BAD_COMMAND_RESPONSE = '\xFA';
//declare for MPSSE command
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_OUT 				= '\x10';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_OUT 				= '\x11';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_OUT 				= '\x12';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_OUT 				= '\x13';
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_IN 				= '\x20';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_IN 				= '\x22';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_IN 				= '\x24';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_IN 				= '\x26';
const BYTE MSB_RISING_FALLING_EDGE_CLOCK_BYTE_IN_OUT	= '\x31';
const BYTE MSB_RISING_FALLING_EDGE_CLOCK_BIT_IN_OUT 	= '\x33';
const BYTE MSB_FALLING_RISING_EDGE_CLOCK_BYTE_IN_OUT 	= '\x34';
const BYTE MSB_FALLING_RISING_EDGE_CLOCK_BIT_IN_OUT 	= '\x36';

BYTE 	OutputBuffer[512];
DWORD	dwNumBytesToSend = 0;
DWORD	dwNumBytesSent  = 0;
DWORD 	dwNumBytesRead;
BYTE	signature_prefix = 0xAB;
BYTE	signature_surfix = 0xBA;

BYTE	is_spi_flash	= 0;
BYTE	is_jtag_flash	= 0;
BYTE	is_jtag			= 0;
BYTE	is_mdio			= 0;

//Read cmd will get 16 bytes data each time
#define READ_BLOCK_SIZE	16

//lsc commands definition
unsigned char lsc_idcode_cmd[]			= {0xE0, 0x0, 0x0, 0x0};
unsigned char lsc_enable_cmd[]			= {0x74, 0x8, 0x0, 0x0};
unsigned char lsc_erase_cmd[]			= {0x0E, 0x4, 0x0, 0x0};
unsigned char lsc_init_cmd[]			= {0x46, 0x0, 0x0, 0x0};
unsigned char lsc_disable_cmd[]			= {0x26, 0x0, 0x0};
unsigned char lsc_prog_done_cmd[]		= {0x5E, 0x0, 0x0, 0x0};
unsigned char lsc_cfg_add_cmd[]			= {0x46, 0x0, 0x0, 0x0};
unsigned char lsc_read_cmd[]			= {0x73, 0x0, 0x0, 0x0};
unsigned char lsc_acc_mode_cmd[]		= {0xC6, 0x8, 0x0};
unsigned char lsc_refresh_cmd[]			= {0x79, 0x0, 0x0};
unsigned char lsc_no_op_cmd[]			= {0xFF, 0xFF, 0xFF, 0xFF};
unsigned char lsc_prog_incr_cmd[]		= {0x70, 0x0, 0x0, 0x0};
unsigned char lsc_status_cmd[]			= {0x3C, 0x0, 0x0, 0x0};

BYTE   setup_jtag[3] =
{
    0x80, 0x08, 0x0B  // TMS start high; TDO is input
};

//BYTE   setup_reg[3] =
//{
//    0x80, 0x00, 0x0B  // TMS start high; TDO is input
//};

BYTE   setup_reg[3] =
{
    0x80, 0x18, 0x1B  // TMS start high; TDO is input
};

BYTE   setup_spi[3] =
{
    0x80, 0x00, 0x0B  // TMS start high; TDO is input
};

BYTE   setup_acbus_high[3] =
{
    0x82, 0x01, 0x01  // TMS start high; TDO is input
};

BYTE   setup_acbus_low[3] =
{
    0x82, 0x00, 0x01  // TMS start high; TDO is input
};

BYTE   setup_bcbus_high[3] =
{
    0x82, 0x01, 0x01  // TMS start high; TDO is input
};

BYTE   setup_bcbus_low[3] =
{
    0x82, 0x00, 0x01  // TMS start high; TDO is input
};

BYTE   setup_gpio[3] =
{
    0x82, 0x00, 0x00  // TMS start high; TDO is input
};

BYTE   ena_lpbk[1] =
{
    0x84              // enable TDI/TDO loopback
};
BYTE   dis_lpbk[1] =
{
    0x85              // disable TDI/TDO loopback
};

//BYTE   set_Clock[3] =
//{
//    0x86, 0x04, 0x00  // TCK divisor: CLK = 6 MHz / (1 + 0004) == 1.2 MHz
//};

BYTE   cfg_clock[3] =
{
    0x8A, 0x97, 0x8D  // clock related setting, for debug only
};

BYTE   setClock[3] =
{
    0x86, 0x00, 0x00  // TCK divisor: CLK = 6 MHz / (1 + 0004) == 1.2 MHz
};

BYTE   transceive[3] =
{
    0x31, 0x00, 0x00  // Write + read; length bytes set later.
};

BYTE   rst_irscan[3] =
{
    0x4B, 0x05, 0x0D  //Navigate TMS through Test-Logic-Reset -> Run-Test-Idle -> Select-DR-Scan -> Select-IR-Scan, tms 101100
};

BYTE   mod_sel[5] =
{
    0x39, 0x01, 0x00, 0xC0, 0x7F  //According to Capri design, select 127 bits mode, 10'b0111111111
};

BYTE   oneclock_high[3] =
{
    0x6B, 0x00, 0x83  //tms one clock cmd from shit to exit, bit 7 is high
};

BYTE   oneclock_low[3] =
{
    0x6B, 0x00, 0x03  //tms one clock cmd from shit to exit, bit 7 is low
};

BYTE   updateir_shiftdr[3] =
{
    0x4B, 0x03, 0x83  //Navigate TMS from Exit-IR through Update-IR -> Select-DR-Scan -> Capture-DR -> Shift-DR, tms 1100
};

BYTE   shiftdr[2] =
{
    0x3B, 0x00  // shift DR; length bytes set later, can use 0x31 if longer than 0xFF
};

BYTE   updatedr_reset[3] =
{
    0x4B, 0x03, 0xFF  //Navigate TMS through Update-DR -> Select-DR-Scan -> Select-IR-Scan -> Test Logic Reset, tms 1111
};

BYTE   tms_low[3] =
{
	0x6B, 0x00, 0x00
};

BYTE   tms_high[3] =
{
	0x6B, 0x00, 0x03
};

BYTE   test1[6] =
{
	0x3C, 0x2, 0x0, 0x00, 0x06, 0x00
};

BYTE   test2[7] =
{
	0x3C, 0x3, 0x0, 0x00, 0x0A, 0xF0, 0x1F
};

BYTE   cpu_wr[15];
//BYTE   cpu_wr[15] =
//{
//	0x3C, 0xB, 0x0, 0x00, 0x12, 0x80, 0x00, 0xC1, 0x80, 0x40, 0x00, 0xC1, 0x80, 0x40, 0x00
//};

BYTE   cpu_rd[11];
//BYTE   cpu_rd[11] =
//{
//	0x3C, 0x7, 0x0, 0x00, 0x22, 0x40, 0x00, 0xC1, 0x80, 0x40, 0x00
//};

BYTE   cpu_res[13];
//BYTE   cpu_res[11] =
//{
//	0x3C, 0x7, 0x0, 0x00, 0x42, 0x00, 0x00, 0xC1, 0x80, 0x40, 0x00
//};

BYTE   con_red[5] =
{
	0x3C, 0x1, 0x0, 0x00, 0x82
};
#if 0
char*	lock_file = "/tmp/cpld.lock";
int		lock_fd = 0;
struct stat st0, st1;

void cpld_lock()
{
	while(1) {
		lock_fd = open(lock_file, O_CREAT);
		flock(lock_fd, LOCK_EX);

		fstat(lock_fd, &st0);
		stat(lock_fd, &st1);
		if(st0.st_ino == st1.st_ino)
			break;

		close(lock_fd);
	}
}

void cpld_unlock()
{
	flock(lock_fd, LOCK_UN);
	close(lock_fd);
}
#endif
void jtag_wr_instruction(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
//	printf("inst 0x%x, address 0x%llx, data 0x%x, flag 0x%x\n", inst, address, data, flag);
	cpu_wr[0] = 0x3C;
	cpu_wr[1] = 0x0B;
	cpu_wr[2] = 0x00;
	DWORD slot = 1 << (inst - 1);
	cpu_wr[3] = slot & 0xFF;
	cpu_wr[4] = JTAG_WR_CMD << 2 | (slot & 0x300) >> 8;
	cpu_wr[5] = (flag & 0x1) << 6;
	DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
//	printf("size 0x%x\n", size);
	cpu_wr[6] = (address & 0x3F) << 2 | size;
	cpu_wr[7] = (address >> 6) & 0xFF;
	cpu_wr[8] = (address >> 14) & 0xFF;
	cpu_wr[9] = (address >> 22) & 0xFF;
	cpu_wr[10] = (data & 0xF) << 4 | ((address >> 30) & 0xF);
	cpu_wr[11] = (data >> 4) & 0xFF;
	cpu_wr[12] = (data >> 12) & 0xFF;
	cpu_wr[13] = (data >> 20) & 0xFF;
	cpu_wr[14] = (JTAG_WR_OP & 0x3) << 4 | ((data >> 28) & 0xF);
//	cpu_wr[5] = 0;
//	DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
//	cpu_wr[6] = (address & 0xF) << 4 | (size) << 2 | (flag & 0x1);
//	cpu_wr[7] = (address >> 4) & 0xFF;
//	cpu_wr[8] = (address >> 12) & 0xFF;
//	cpu_wr[9] = (address >> 20) & 0xFF;
//	//hard code hbm address 2'b0
//	cpu_wr[10] = (data & 0x3) | ((address >> 28) & 0xFF);
//	cpu_wr[11] = (data >> 2) & 0xFF;
//	cpu_wr[12] = (data >> 10) & 0xFF;
//	cpu_wr[13] = (data >> 18) & 0xFF;
//	cpu_wr[14] = (JTAG_WR_OP & 0x3) << 6 | ((data >> 26) & 0x3FF);

//	printf("write: ");
//	for(int i = 0; i < 15; i++)
//	{
//		printf("0x%x ", cpu_wr[i]);
//	}
//	printf("\n");
}

void jtag_rd_instruction(DWORD inst, ULONGLONG address, DWORD flag)
{
//	printf("inst 0x%x, address 0x%llux, flag 0x%x\n", inst, address, flag);
	cpu_rd[0] = 0x3C;
	cpu_rd[1] = 0x07;
	cpu_rd[2] = 0x00;
	DWORD slot = 1 << (inst - 1);
	cpu_rd[3] = slot & 0xFF;
	cpu_rd[4] = JTAG_RD_CMD << 2 | (slot & 0x300) >> 8;
	cpu_rd[5] = (flag & 0x1) << 6;
	DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
	cpu_rd[6] = (address & 0x3F) << 2 | size;
	cpu_rd[7] = (address >> 6) & 0xFF;
	cpu_rd[8] = (address >> 14) & 0xFF;
	cpu_rd[9] = (address >> 22) & 0xFF;
	cpu_rd[10] = (JTAG_RD_OP & 0x3) << 4 | ((address >> 30) & 0xF);
//	cpu_rd[5] = 0;
//	DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
//	cpu_rd[6] = (address & 0xF) << 4 | (size & 0x3) << 2 | (flag & 0x1);
//	cpu_rd[7] = (address >> 4) & 0xFF;
//	cpu_rd[8] = (address >> 12) & 0xFF;
//	cpu_rd[9] = (address >> 20) & 0xFF;
//	//hard code hbm address 2'b0
//	cpu_rd[10] = (JTAG_RD_OP & 0x3) << 6 | ((address >> 28) & 0x3FF);
//	printf("read: ");
//	for(int i = 0; i < 10; i++)
//	{
//		printf("0x%x ", cpu_rd[i]);
//	}
//	printf("\n");

//	cpu_rd[4] = (JTAG_RD_CMD & 0x3) << 2 | (slot & 0x300) >> 8;
//	cpu_rd[5] = JTAG_RD_OP & 0xFF;
//	cpu_rd[6] = (address & 0x3) << 6 | ((JTAG_RD_OP >> 8) & 0xFF);
//	cpu_rd[7] = (address >> 2) & 0xFF;
//	cpu_rd[8] = (address >> 10) & 0xFF;
//	cpu_rd[9] = (address >> 18) & 0xFF;
//	cpu_rd[10] = (address >> 26) & 0xFF;
}

void jtag_res_instruction(DWORD inst)
{
	cpu_res[0] = 0x3C;
	cpu_res[1] = 0x09;
	cpu_res[2] = 0x00;
	DWORD slot = 1 << (inst - 1);
	cpu_res[3] = slot & 0xFF;
	cpu_res[4] = JTAG_RES_CMD << 2 | (slot & 0x300) >> 8;
	cpu_res[5] = 0;
	cpu_res[6] = 0;
	cpu_res[7] = 0;
	cpu_res[8] = 0;
	cpu_res[9] = 0;
	cpu_res[10] = 0;
	cpu_res[11] = 0;
	cpu_res[12] = 0;


//	printf("response: ");
//	for(int i = 0; i < 10; i++)
//	{
//		printf("0x%x ", cpu_res[i]);
//	}
//	printf("\n");
}

FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
	FT_STATUS ftStatus = FT_OK;
    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_wr_instruction(inst, address, data, flag);
    ftStatus = sendJtagCommand(ftHandle, cpu_wr, sizeof cpu_wr);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_res_instruction(inst);
    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }
//temporary ignore valid bit
    queue_read(ftHandle, &data);
//    ftStatus = queue_read(ftHandle, &data);
//    if(ftStatus != FT_OK)
//    {
//    	printf("Write response is not valid!\n");
//    }

    return ftStatus;
}

FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag)
{
	FT_STATUS       ftStatus = FT_OK;
    int tx_buf, rx_buf, event;

//    ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
//    printf("queue1 rx %d, tx %d\n", rx_buf, tx_buf);
//    readBuffer = (unsigned char *)calloc(rx_buf, sizeof(unsigned char));
//    ftStatus = FT_Read(ftHandle, readBuffer, rx_buf, &read_data);
//    free(readBuffer);
//
//    ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
//    printf("queue11 rx %d, tx %d\n", rx_buf, tx_buf);
//    readBuffer = (unsigned char *)calloc(rx_buf, sizeof(unsigned char));
//    ftStatus = FT_Read(ftHandle, readBuffer, rx_buf, &read_data);
//    free(readBuffer);

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_rd_instruction(inst, address, flag);
    ftStatus = sendJtagCommand(ftHandle, cpu_rd, sizeof cpu_rd);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

//    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

//    ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
//    printf("queue2 rx %d, tx %d\n", rx_buf, tx_buf);
//    readBuffer = (unsigned char *)calloc(rx_buf, sizeof(unsigned char));
//    ftStatus = FT_Read(ftHandle, readBuffer, rx_buf, &read_data);
//    free(readBuffer);
//
//    ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
//    printf("queue22 rx %d, tx %d\n", rx_buf, tx_buf);
//    readBuffer = (unsigned char *)calloc(rx_buf, sizeof(unsigned char));
//    ftStatus = FT_Read(ftHandle, readBuffer, rx_buf, &read_data);
//    free(readBuffer);
//sleep(1);
//    queue_clear(ftHandle);

//    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }
//
//    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }
//
//    queue_read(ftHandle);

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_res_instruction(inst);
    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = queue_read(ftHandle, data);
    if(ftStatus == 1)
    {
    	printf("Read failed due to other reason!\n");
    }
    else if(ftStatus == 2)
    {
    	//resend response after 1 second;
        ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        jtag_res_instruction(inst);
        ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
    	sleep(1);
        ftStatus = queue_read(ftHandle, data);
        if(ftStatus == 2)
        	printf("Read failed due to corruption in resend!\n");
        else if(ftStatus == 0)
        	printf("resend successfully!\n");
        else
        	printf("Read failed due to other reason in resend!\n");
    }

#if 0
    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, con_red, sizeof con_red);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }
#endif
//    ftStatus = sendJtagCommand(ftHandle, rst_irscan, sizeof rst_irscan);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }
//
//    ftStatus = sendJtagCommand(ftHandle, mod_sel, sizeof mod_sel);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

//    transceive[1] = (unsigned char)(bytesToWrite & 0x000000FF);
//    transceive[2] = (unsigned char)((bytesToWrite & 0x0000FF00) >> 8);
//    ftStatus = sendJtagCommand(ftHandle, transceive, sizeof transceive);

//    ftStatus = sendJtagCommand(ftHandle, tms, sizeof tms);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

    return ftStatus;
}

FT_STATUS jtag_write(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
	FT_STATUS ftStatus = FT_OK;
    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_wr_instruction(inst, address, data, flag);
    ftStatus = sendJtagCommand(ftHandle, cpu_wr, sizeof cpu_wr);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_res_instruction(inst);
    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    return ftStatus;
}

DWORD jtag_read(DWORD inst, ULONGLONG address, DWORD flag)
{
    FT_STATUS       ftStatus = FT_OK;
    DWORD data;
    int tx_buf, rx_buf, event;

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_rd_instruction(inst, address, flag);
    ftStatus = sendJtagCommand(ftHandle, cpu_rd, sizeof cpu_rd);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_res_instruction(inst);
    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = queue_read(ftHandle, &data);
    if(ftStatus == 1)
    {
    	printf("Read failed due to other reason!\n");
    }
    else if(ftStatus == 2)
    {
    	//resend response after 1 second;
        ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        jtag_res_instruction(inst);
        ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
    	sleep(1);
        ftStatus = queue_read(ftHandle, &data);
        if(ftStatus == 2)
        	printf("Read failed due to corruption in resend!\n");
        else if(ftStatus == 0)
        	printf("resend successfully!\n");
        else
        	printf("Read failed due to other reason in resend!\n");
    }

    return data;
}

FT_STATUS jtag_id(DWORD inst, DWORD* data)
{
	FT_STATUS       ftStatus = FT_OK;

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    jtag_res_instruction(inst);
    ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = queue_read(ftHandle, data);
    if(ftStatus == 1)
    {
    	printf("Read failed due to other reason!\n");
    }
    else if(ftStatus == 2)
    {
    	//resend response after 1 second;
        ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        jtag_res_instruction(inst);
        ftStatus = sendJtagCommand(ftHandle, cpu_res, sizeof cpu_res);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
    	sleep(1);
        ftStatus = queue_read(ftHandle, data);
        if(ftStatus == 2)
        	printf("Read failed due to corruption in resend!\n");
        else if(ftStatus == 0)
        	printf("resend successfully!\n");
        else
        	printf("Read failed due to other reason in resend!\n");
    }
    return ftStatus;
}

ULONGLONG xtoi(char *hexstring)
{
	ULONGLONG	i = 0;

	if ((*hexstring == '0') && (*(hexstring+1) == 'x'))
		  hexstring += 2;
	while (*hexstring)
	{
		char c = toupper(*hexstring++);
		if ((c < '0') || (c > 'F') || ((c > '9') && (c < 'A')))
			break;
		c -= '0';
		if (c > 9)
			c -= 7;
		i = (i << 4) + c;
	}
	return i;
}

FT_STATUS jtag_init()
{

    FT_STATUS       ftStatus = FT_OK;
    int             portNum = CHANNEL_A;
    DWORD           driverVersion = 0;

    if(ftHandle == NULL)
    	ftStatus = FT_Open(portNum, &ftHandle);
    if (ftStatus != FT_OK)
    {
        printf("FT_Open(%d) failed, with error %d.\n", portNum, (int)ftStatus);
        printf("On Linux, lsmod can check if ftdi_sio (and usbserial) are present.\n");
        printf("If so, unload them using rmmod, as they conflict with ftd2xx.\n");
        return ftStatus;
    }

    assert(ftHandle != NULL);

    ftStatus = FT_GetDriverVersion(ftHandle, &driverVersion);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_GetDriverVersion returned %d.\n",
               (int)ftStatus);
        return ftStatus;
    }

//    printf("D2XX version : %x.%x.%x\n",
//           (unsigned int)((driverVersion & 0x00FF0000) >> 16),
//           (unsigned int)((driverVersion & 0x0000FF00) >> 8),
//           (unsigned int)(driverVersion & 0x000000FF)
//           );

//    ftStatus = FT_ResetDevice(ftHandle);
//    if (ftStatus != FT_OK)
//    {
//        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
//        return ftStatus;
//    }

    BYTE byOutputBuffer[1024];
    BYTE byInputBuffer[1024];
    DWORD dwNumBytesToRead = 0;

    //Purge USB receive buffer first by reading out all old data from FT2232H receive buffer
    ftStatus |= FT_GetQueueStatus(ftHandle, &dwNumBytesToRead);
    // Get the number of bytes in the FT2232H receive buffer
    if ((ftStatus == FT_OK) && (dwNumBytesToRead > 0))
    	FT_Read(ftHandle, &byInputBuffer, dwNumBytesToRead, &dwNumBytesRead);
    //Read out the data from FT2232H receive buffer
    ftStatus |= FT_SetUSBParameters(ftHandle, 65536, 65535);
    //Set USB request transfer sizes to 64K
    ftStatus |= FT_SetChars(ftHandle, FALSE, 0, FALSE, 0);


//    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
//    if (ftStatus != FT_OK)
//    {
//        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
//        return ftStatus;
//    }

    ftStatus = FT_SetTimeouts(ftHandle, 0, 5000);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetTimeouts returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetLatencyTimer(ftHandle, 16);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetLatencyTimer returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_MPSSE);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }
#if 0
    dwNumBytesToSend = 0;
    byOutputBuffer[dwNumBytesToSend++] = 0xAA;//'\xAA';
    //Add bogus command ‘xAA’ to the queue
    ftStatus = FT_Write(ftHandle, byOutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    // Send off the BAD commands
    dwNumBytesToSend = 0; // Reset output buffer pointer
    do
    {
		ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesToRead);
		// Get the number of bytes in the device input buffer
    } while ((dwNumBytesToRead == 0) && (ftStatus == FT_OK)); //or Timeout

    BOOL bCommandEchod = FALSE;
    ftStatus = FT_Read(ftHandle, &byInputBuffer, dwNumBytesToRead, &dwNumBytesRead);
    //Read out the data from input buffer
    for (DWORD dwCount = 0; dwCount < dwNumBytesRead - 1; dwCount++)
    //Check if Bad command and echo command received
    {
    	printf("0x%x 0x%x   ", byInputBuffer[dwCount], byInputBuffer[dwCount+1]);
		if ((byInputBuffer[dwCount] == 0xFA) && (byInputBuffer[dwCount+1] == 0xAA))
		{
			bCommandEchod = TRUE;
			break;
		}
    }
//    if (bCommandEchod == FALSE) {
//		printf("Error in synchronizing the MPSSE\n");
//		FT_Close(ftHandle);
//		return 1; // Exit with error
//    } else {
//    	printf("synchronizing the MPSSE\n");
//    }
    dwNumBytesToSend = 0;
#endif
//    ftStatus = sendJtagCommand(ftHandle, cfg_clock, sizeof cfg_clock);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

	ftStatus = sendJtagCommand(ftHandle, setup_jtag, sizeof setup_jtag);
	if (ftStatus != FT_OK)
	{
		return ftStatus;
	}

	ftStatus = sendJtagCommand(ftHandle, setup_gpio, sizeof setup_gpio);
	if (ftStatus != FT_OK)
	{
		return ftStatus;
	}

    ftStatus = sendJtagCommand(ftHandle, setClock, sizeof setClock);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, dis_lpbk, sizeof dis_lpbk);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    return ftStatus;
}


FT_STATUS jtag_reset(DWORD inst)
{
	FT_STATUS ftStatus = FT_OK;
	BYTE	jtag_reset[6];
	jtag_reset[0] = 0x3C;
	jtag_reset[1] = 0x02;
	jtag_reset[2] = 0x00;
	DWORD slot = 1 << (inst - 1);
	jtag_reset[3] = slot & 0xFF;
	jtag_reset[4] = JTAG_RST_CMD << 2 | (slot & 0x300) >> 8;
	jtag_reset[5] = 0;

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

//	for(int i = 0; i < 6; i++)
//	{
//		printf("reset 0x%x\n", jtag_reset[i]);
//	}
    ftStatus = sendJtagCommand(ftHandle, jtag_reset, sizeof jtag_reset);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

	return ftStatus;
}

FT_STATUS jtag_enable(DWORD inst)
{
	FT_STATUS ftStatus = FT_OK;
	BYTE	jtag_ena[7];
	jtag_ena[0] = 0x3C;
	jtag_ena[1] = 0x03;
	jtag_ena[2] = 0x00;
	DWORD slot = 1 << (inst - 1);
	jtag_ena[3] = slot & 0xFF;
	jtag_ena[4] = JTAG_ENA_CMD << 2 | (slot & 0x300) >> 8;
	jtag_ena[5] = 0xF0;
	jtag_ena[6] = 0x1F;

    ftStatus = sendJtagCommand(ftHandle, tms_low, sizeof tms_low);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, jtag_ena, sizeof jtag_ena);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, tms_high, sizeof tms_high);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

	return ftStatus;
}

void queue_clear(FT_HANDLE ftHandle)
{
	FT_STATUS ftStatus = FT_OK;
	DWORD rx_buf, tx_buf, event, bytesRead, count = 20;
	char buffer[100];
	ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
	if (ftStatus != FT_OK)
	{
		printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
			   (int)ftStatus);
		return;
	}
    while(rx_buf || tx_buf || count)
    {
		// Then copy D2XX's buffer to ours.
		ftStatus = FT_Read(ftHandle, buffer, rx_buf, &bytesRead);
		if (ftStatus != FT_OK)
		{
			printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
			return;
		}
//		printf("queue clear %d bytes\n", bytesRead);

		ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
		if (ftStatus != FT_OK)
		{
			printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
				   (int)ftStatus);
			return;
		}
		if(!rx_buf && !tx_buf)
			count--;
//    	printf("rx %d, tx %d\n", rx_buf, tx_buf);
    }
}

int queue_read(FT_HANDLE ftHandle, DWORD* data)
{
    int             f = 0;
    FT_STATUS       ftStatus = FT_OK;
    DWORD           bytesRead = 0;
    DWORD			rx_buf = 0;
    DWORD			tx_buf = 0;
    DWORD			event = 0;
    DWORD			count = 0;
    DWORD			retry = 0;
    BYTE			v_data = 0;
    unsigned char	buffer[10000];
    struct timeval  startTime;
    int             journeyDuration = 1;
    unsigned char  *readBuffer = NULL;
    int sof = 0, eof = 0;

    gettimeofday(&startTime, NULL);

//    sleep(1);
	ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
	if (ftStatus != FT_OK)
	{
		printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
			   (int)ftStatus);
		return 1;
	}

//	printf("first queue status %d %d bytes\n", rx_buf, tx_buf);

    while(!sof || !eof)
    {
    	retry++;
        struct timeval now;
        struct timeval elapsed;

        gettimeofday(&now, NULL);
        timersub(&now, &startTime, &elapsed);

        if (elapsed.tv_sec > (long int)journeyDuration)
        {
            // We've waited too long.  Give up.
            printf("\nFailure. Timed out after %ld seconds\n", elapsed.tv_sec);
//            break;
            goto corrupt;
        }
		// Then copy D2XX's buffer to ours.
		ftStatus = FT_Read(ftHandle, &buffer[count], rx_buf, &bytesRead);
		if (ftStatus != FT_OK)
		{
			printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
			return 1;
		}
//		if(bytesRead)
//			printf("FT_read %d bytes\n", bytesRead);
#if 0
		if(bytesRead != 0)
		{
			for(f = count; f < count + bytesRead - 1; f++)
			{
				if(buffer[f] == 0x40 && buffer[f+1] == 0x1)
				{
					sof = 1;
					if(f + 5 <= count + bytesRead)
					{
						if(buffer[f+5] == 0xc8)
							eof = 1;
						else
							sof = 0;
					}
					else
						goto corrupt;
				}
			}
		}
#else
		if(bytesRead != 0)
		{
			//fixeme: 3 corner cases: 0x40 is the last one; 0x40, 0x01 and 0xc8 are in 3 frames;
			// multiple 0x40 0x01
			if(!sof)
			{
				for(f = count; f < count + bytesRead; f++)
				{
					if(buffer[f] == signature_prefix)
					{
						sof = 1;
						if(f + 7 < count + bytesRead)
						{
							if(buffer[f + 7] == signature_surfix)
							{
								eof = 1;
								//verification 4 bytes
								v_data = (buffer[f+1] & 0xF0) >> 4 | (buffer[f+2] & 0x0F) << 4;
								*data = (buffer[f+6] & 0x0F) << 28 | buffer[f+5] << 20 | buffer[f+4] << 12 | buffer[f+3] << 4 | (buffer[f+2] & 0xF0) >> 4;
								//workaround on HAPS
//								v_data = (buffer[f+1] & 0xC0) >> 6 | (buffer[f+2] & 0x3F) << 6;
//								*data = (buffer[f+6] & 0x3F) << 26 | buffer[f+5] << 18 | buffer[f+4] << 10 | buffer[f+3] << 2 | (buffer[f+2] & 0xC0) >> 6;
//								printf("data 0x%x\n", ((buffer[f+6] & 0x3F) << 26) | (buffer[f+5] << 18));
//								printf("data f+2 0x%x\n", (buffer[f+2] & 0xC0) >> 2);
								break;
							}
							else
								sof = 0;
						}
						else
							continue;
					}
				}
			}
			else
			{
				for(f = count; f < count + bytesRead - 1; f++)
				{
					if((buffer[f] == signature_surfix) && (buffer[f-7] == signature_prefix))
					{
						eof = 1;
						//verification 4 bytes
						v_data = (buffer[f-6] & 0xF0) >> 4 | (buffer[f-5] & 0x0F) << 4;
						*data = (buffer[f-1] & 0x0F) << 28 | buffer[f-2] << 20 | buffer[f-3] << 12 | buffer[f-4] << 4 | (buffer[f-5] & 0xF0) >> 4;

						//workaround on HAPS
//						v_data = (buffer[f-6] & 0xC0) >> 6 | (buffer[f-5] & 0x3F) << 6;
//						*data = (buffer[f-1] & 0x3F) << 26 | buffer[f-2] << 18 | buffer[f-3] << 10 | buffer[f-4] << 2 | (buffer[f-5] & 0xC0) >> 6;

						//						printf("data 0x%x\n", ((buffer[f-1] & 0x3F) << 26) | (buffer[f-2] << 18));
//						printf("data f-5 0x%x\n", (buffer[f-5] & 0xC0) >> 2);
						break;
					}
				}
			}
		}
#endif
		count += bytesRead;
//		if(count >= 8)
//			break;
//		printf("queue clear %d bytes\n", bytesRead);

		ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
		if (ftStatus != FT_OK)
		{
			printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
				   (int)ftStatus);
			return 1;
		}
    }

//	printf("data 0x%08x, valid bit 0x%x, error 0x%02x, RSP 0x%02x\n", v_data, (v_data&0x1), (v_data&0x6) >> 1, (v_data&0x18) >> 3);
	//    printf("Max retry %d\n", retry);
//	printf("Receive data:\n");
//	for(f = 0; f < count; f++)
//	{
//		printf("0x%x ", buffer[f]);
//	}
//	printf("\n");

	//check valid bit is set and error bits are clean
	if((v_data&0x1) && !((v_data&0x6) >> 1))
	{
		return 0;
	} else
		return 3;

corrupt:
	printf("\nFailure. Frame was corrupted\n");
	printf("Corrupted data:\n");
	for(f = 0; f < count + bytesRead; f++)
	{
		printf("0x%x ", buffer[f]);
	}
	printf("\n");
	return 2;
}

int ftdi_buffer_read(FT_HANDLE ftHandle, BYTE* data, DWORD size)
{
	DWORD           f = 0;
    FT_STATUS       ftStatus = FT_OK;
    DWORD           bytesRead = 0;
    DWORD			rx_buf = 0;
    DWORD			tx_buf = 0;
    DWORD			event = 0;
    DWORD			count = 0;
    DWORD			retry = 0;
    unsigned char	buffer[10000];
    struct timeval  startTime;
    int             journeyDuration = 1;

    gettimeofday(&startTime, NULL);

//    sleep(1);
	ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
	if (ftStatus != FT_OK)
	{
		printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
			   (int)ftStatus);
		return 1;
	}

//	printf("first queue status %d %d bytes\n", rx_buf, tx_buf);

    while(1)
    {
    	retry++;
        struct timeval now;
        struct timeval elapsed;

        gettimeofday(&now, NULL);
        timersub(&now, &startTime, &elapsed);

        if (elapsed.tv_sec > (long int)journeyDuration)
        {
            // We've waited too long.  Give up.
            printf("\nFailure. Timed out after %ld seconds\n", elapsed.tv_sec);
//            break;
            goto corrupt;
        }
		// Then copy D2XX's buffer to ours.
		ftStatus = FT_Read(ftHandle, &buffer[count], rx_buf, &bytesRead);
		if (ftStatus != FT_OK)
		{
			printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
			return 1;
		}

//		if(bytesRead)
//			printf("FT_read %d bytes\n", bytesRead);
//		for(int i = 0; i < bytesRead; i++)
//			printf("0x%x ", buffer[i]);
//		printf("###\n");

		count += bytesRead;
		if(count == size)
		{
			//extra copy here, to avoid data overflow, may be optimized
			memcpy(data, buffer, size);
//			printf("FT_read got expected %d bytes\n", size);
			break;
		} else if(count > size)
		{
			printf("count %d bytes is greater than size\n", count);
			goto corrupt;
		}

		ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
		if (ftStatus != FT_OK)
		{
			printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
				   (int)ftStatus);
			return 1;
		}
    }

	return 0;

corrupt:
	printf("\nFailure. Frame was corrupted\n");
	printf("Corrupted data:\n");
	for(f = 0; f < count + bytesRead; f++)
	{
		printf("0x%x ", buffer[f]);
	}
	printf("\n");
	return 2;
}


FT_STATUS sendJtagCommand(FT_HANDLE      ftHandle,
                                 BYTE *sequence,
                                 const size_t   length)
{
    FT_STATUS  ftStatus = FT_OK;
    DWORD      bytesToWrite = (DWORD)length;
    DWORD      bytesWritten = 0;
  
    ftStatus = FT_Write(ftHandle, sequence, bytesToWrite, &bytesWritten);
//    printf("bytesWritten 0x%x\n", sequence[0]);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
        return ftStatus;
    }
    
    if (bytesWritten != bytesToWrite)
    {
        printf("Failure.  FT_Write wrote %d bytes instead of %d.\n",
               (int)bytesWritten,
               (int)bytesToWrite);
    }

    return ftStatus;
}

void spi_csena()
{
	for(int i = 0; i < 5; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = 0x80;
//		OutputBuffer[dwNumBytesToSend++] = 0x08;
		OutputBuffer[dwNumBytesToSend++] = 0x18;
		OutputBuffer[dwNumBytesToSend++] = 0x0b;
	}
}

void spi_csdis()
{
	for(int i = 0; i < 5; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = 0x80;
//		OutputBuffer[dwNumBytesToSend++] = 0x08;
		OutputBuffer[dwNumBytesToSend++] = 0x10;
		OutputBuffer[dwNumBytesToSend++] = 0x1b;

	}
}

FT_STATUS cpld_csena()
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = 0, dwNumBytesSent;
	for(int i = 0; i < 5; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = 0x80;
		//mtp
		OutputBuffer[dwNumBytesToSend++] = 0x18;
		//bb flash
//		OutputBuffer[dwNumBytesToSend++] = 0x18;
		OutputBuffer[dwNumBytesToSend++] = 0x1b;
	}
	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    if (ftStatus != FT_OK)
    {
        printf("Failure. %s\n", __FUNCTION__);
        return ftStatus;
    }
    return ftStatus;
}

FT_STATUS cpld_csdis()
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = 0, dwNumBytesSent;
	for(int i = 0; i < 5; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = 0x80;
		//mtp
		OutputBuffer[dwNumBytesToSend++] = 0x10;
		//bb flash
//		OutputBuffer[dwNumBytesToSend++] = 0x08;
		OutputBuffer[dwNumBytesToSend++] = 0x1b;
	}
	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    if (ftStatus != FT_OK)
    {
        printf("Failure. %s\n", __FUNCTION__);
        return ftStatus;
    }
    return ftStatus;
}

FT_STATUS spi_reg_init()
{
	FT_STATUS       ftStatus = FT_OK;
	is_spi_flash = 0;
	ftStatus = spi_init();
	return ftStatus;
}

FT_STATUS spi_mdio_init()
{
	FT_STATUS       ftStatus = FT_OK;
	is_spi_flash = 0;
	is_mdio = 1;
	ftStatus = spi_init();
	return ftStatus;
}

FT_STATUS spi_flash_init()
{
	FT_STATUS       ftStatus = FT_OK;
	is_spi_flash = 1;
	ftStatus = spi_init();
	return ftStatus;
}

FT_STATUS jtag_flash_init()
{
	FT_STATUS       ftStatus = FT_OK;
	is_spi_flash = 1;
	is_jtag_flash = 1;
	ftStatus = spi_init();
	return ftStatus;
}

FT_STATUS spi_init()
{
    FT_STATUS       ftStatus = FT_OK;
//    int             portNum = 1; // First device found
    DWORD           driverVersion = 0;

//    printf("Opening FTDI device.\n");

    if(ftHandle_a == NULL)
    	ftStatus = FT_Open(CHANNEL_A, &ftHandle_a);
    if(ftHandle == NULL)
    	ftStatus |= FT_Open(CHANNEL_B, &ftHandle);
    if (ftStatus != FT_OK)
    {
        printf("FT_Open failed, with error %d.\n", (int)ftStatus);
        printf("On Linux, lsmod can check if ftdi_sio (and usbserial) are present.\n");
        printf("If so, unload them using rmmod, as they conflict with ftd2xx.\n");
        return ftStatus;
    }

    assert(ftHandle != NULL);

    ftStatus = FT_GetDriverVersion(ftHandle, &driverVersion);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_GetDriverVersion returned %d.\n",
               (int)ftStatus);
        return ftStatus;
    }

//    printf("D2XX version : %x.%x.%x\n",
//           (unsigned int)((driverVersion & 0x00FF0000) >> 16),
//           (unsigned int)((driverVersion & 0x0000FF00) >> 8),
//           (unsigned int)(driverVersion & 0x000000FF)
//           );

    ftStatus = FT_ResetDevice(ftHandle);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_ResetDevice(ftHandle_a);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle_a, 0x00, FT_BITMODE_RESET);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetLatencyTimer(ftHandle, 1);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetLatencyTimer returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetLatencyTimer(ftHandle_a, 1);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetLatencyTimer returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetTimeouts(ftHandle, 3000, 3000);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetTimeouts returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetTimeouts(ftHandle_a, 3000, 3000);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetTimeouts returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x0B, FT_BITMODE_MPSSE);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle_a, 0x0B, FT_BITMODE_MPSSE);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }

//	ftStatus = sendJtagCommand(ftHandle, cfg_clock, sizeof cfg_clock);
//	if (ftStatus != FT_OK)
//	{
//		return ftStatus;
//	}

//	ftStatus = sendJtagCommand(ftHandle_a, cfg_clock, sizeof cfg_clock);
//	if (ftStatus != FT_OK)
//	{
//		return ftStatus;
//	}

    ftStatus = sendJtagCommand(ftHandle_a, setup_reg, sizeof setup_reg);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

	ftStatus = sendJtagCommand(ftHandle, setup_reg, sizeof setup_reg);
	if (ftStatus != FT_OK)
	{
		return ftStatus;
	}

    if(is_spi_flash)
    {
    	if(is_jtag_flash)
    		ftStatus = sendJtagCommand(ftHandle_a, setup_acbus_low, sizeof setup_acbus_low);
    	else
    		ftStatus = sendJtagCommand(ftHandle_a, setup_acbus_high, sizeof setup_acbus_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
       	ftStatus = sendJtagCommand(ftHandle, setup_bcbus_low, sizeof setup_bcbus_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
    } else if(is_jtag)
    {
        ftStatus = sendJtagCommand(ftHandle_a, setup_acbus_low, sizeof setup_acbus_low);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
        printf("ac low\n");
    } else {
        ftStatus = sendJtagCommand(ftHandle_a, setup_acbus_high, sizeof setup_acbus_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }

        ftStatus = sendJtagCommand(ftHandle, setup_bcbus_high, sizeof setup_bcbus_high);
        if (ftStatus != FT_OK)
        {
            return ftStatus;
        }
    }

    ftStatus = sendJtagCommand(ftHandle, setClock, sizeof setClock);
    if (ftStatus != FT_OK) 
    {
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, dis_lpbk, sizeof dis_lpbk);
    if (ftStatus != FT_OK)
    {
        return ftStatus;
    }

//    transceive[1] = (unsigned char)(bytesToWrite & 0x000000FF);
//    transceive[2] = (unsigned char)((bytesToWrite & 0x0000FF00) >> 8);
//    ftStatus = sendJtagCommand(ftHandle, transceive, sizeof transceive);

//    ftStatus = sendJtagCommand(ftHandle, tms, sizeof tms);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

    return ftStatus;
}

FT_STATUS cpld_flash_wr(BYTE* data, int size)
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = dwNumBytesSent = 0;

	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BYTE_OUT;
	OutputBuffer[dwNumBytesToSend++] = size - 1;
	OutputBuffer[dwNumBytesToSend++] = 0;
	for(int i = 0; i < size; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = data[i];
	}
//	printf("instruction: ");
//	for(int i = 0; i < size; i++)
//	{
//		printf("0x%x ", data[i]);
//	}
//	printf("\n");

	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);

    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
    }
    return ftStatus;
}

FT_STATUS cpld_flash_wr_clear(BYTE* data, int size)
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = dwNumBytesSent = 0;

	OutputBuffer[dwNumBytesToSend++] = MSB_RISING_FALLING_EDGE_CLOCK_BYTE_IN_OUT;
	OutputBuffer[dwNumBytesToSend++] = size - 1;
	OutputBuffer[dwNumBytesToSend++] = 0;
	for(int i = 0; i < size; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = data[i];
	}

	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);

    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
    }

    return ftStatus;
}

FT_STATUS cpld_flash_rd(BYTE* data, int size)
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = dwNumBytesSent = 0;

	dwNumBytesSent = 0;
	queue_clear(ftHandle);

	//send WRITE command
	OutputBuffer[dwNumBytesToSend++] = MSB_RISING_FALLING_EDGE_CLOCK_BYTE_IN_OUT;
	OutputBuffer[dwNumBytesToSend++] = size - 1;
	OutputBuffer[dwNumBytesToSend++] = 0;
	for(int i = 0; i < size; i++)
		OutputBuffer[dwNumBytesToSend++] = 0;


//	for(int i = 0; i < 3; i++ )
//		printf("0x%x ", OutputBuffer[i]);
//	printf("\ndwNumBytesToSend %d\n", dwNumBytesToSend);

	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
	dwNumBytesToSend = 0;

    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
    }

	ftStatus = ftdi_buffer_read(ftHandle, data, size);
	if(ftStatus)
	{
		printf("%s failed\n", __FUNCTION__);
		return ftStatus;
	}

//	ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
//	if(dwNumBytesSent != 1)
//		printf("SPI queue %d bytes, failed\n", dwNumBytesSent);
//	else
//		//send out MPSSE command to MPSSE engine
//		ftStatus = FT_Read(ftHandle, data, dwNumBytesSent, &dwNumBytesRead);
	return ftStatus;
}

FT_STATUS cpld_flash_rd_bit(BYTE* data, int size)
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD dwNumBytesToSend = dwNumBytesSent = 0;

	dwNumBytesSent = 0;
	queue_clear(ftHandle);

	//send WRITE command
	OutputBuffer[dwNumBytesToSend++] = MSB_RISING_FALLING_EDGE_CLOCK_BIT_IN_OUT;
	OutputBuffer[dwNumBytesToSend++] = size - 1;
//	OutputBuffer[dwNumBytesToSend++] = 0;
	for(int i = 0; i < size; i++)
		OutputBuffer[dwNumBytesToSend++] = 0;


//	for(int i = 0; i < 3; i++ )
//		printf("0x%x ", OutputBuffer[i]);
//	printf("\ndwNumBytesToSend %d\n", dwNumBytesToSend);

	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
	dwNumBytesToSend = 0;

    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
    }

	ftStatus = ftdi_buffer_read(ftHandle, data, size);
	if(ftStatus)
	{
		printf("%s failed\n", __FUNCTION__);
		return ftStatus;
	}

//	ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
//	if(dwNumBytesSent != 1)
//		printf("SPI queue %d bytes, failed\n", dwNumBytesSent);
//	else
//		//send out MPSSE command to MPSSE engine
//		ftStatus = FT_Read(ftHandle, data, dwNumBytesSent, &dwNumBytesRead);

	return ftStatus;
}

FT_STATUS flash_id_check()
{
	FT_STATUS       ftStatus = FT_OK;
	BYTE id[4] = {0};
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_idcode_cmd, sizeof(lsc_idcode_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
        return ftStatus;
    }
	ftStatus = cpld_flash_rd(id, sizeof(id));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
        return ftStatus;
    }
	cpld_csena();
    if (ftStatus != FT_OK)
    {
        printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
        return ftStatus;
    }
    printf("%s ", __FUNCTION__);
    for(unsigned int i = 0; i < sizeof(id); i++)
    {
    	printf("0x%02x ", id[i]);
    }
    printf("\n");

    return ftStatus;
}

FT_STATUS spi_wr(BYTE address, BYTE data)
{
	FT_STATUS       ftStatus = FT_OK;

	dwNumBytesSent = 0;
	spi_csdis();
	 //send WRITE command
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
	OutputBuffer[dwNumBytesToSend++] = 7;
	OutputBuffer[dwNumBytesToSend++] = WRITE;
	//send address
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
	OutputBuffer[dwNumBytesToSend++] = 7;
	OutputBuffer[dwNumBytesToSend++] = address;
	//send data
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BYTE_OUT;
	//Data length of 0x0000 means 1 byte data to clock out
	OutputBuffer[dwNumBytesToSend++] = 0;
	OutputBuffer[dwNumBytesToSend++] = 0;
	//output high byte
//	OutputBuffer[dwNumBytesToSend++] = data >> 8;
	//output low byte
	OutputBuffer[dwNumBytesToSend++] = data & 0xff;

	spi_csena();
	//send out MPSSE command to MPSSE engine
	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
//	printf("write \n");
//	for(int i = 0; i < dwNumBytesToSend; i++ )
//		printf("0x%x ", OutputBuffer[i]);
//	printf(", sent %d bytes, status %d\n", dwNumBytesSent, ftStatus);

	//Clear output buffer
	dwNumBytesToSend = 0;
	return ftStatus;
}

FT_STATUS spi_rd(BYTE address, BYTE* data)
{
	FT_STATUS       ftStatus = FT_OK;

	dwNumBytesSent = 0;
	queue_clear(ftHandle);
	spi_csdis();
	//send WRITE command
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
	OutputBuffer[dwNumBytesToSend++] = 7;
	OutputBuffer[dwNumBytesToSend++] = READ;
	//send address
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
	OutputBuffer[dwNumBytesToSend++] = 7;
	OutputBuffer[dwNumBytesToSend++] = (BYTE)(address);
	//dummy byte
	OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
	OutputBuffer[dwNumBytesToSend++] = 7;
	OutputBuffer[dwNumBytesToSend++] = 0;
	//read data
	OutputBuffer[dwNumBytesToSend++] = MSB_RISING_EDGE_CLOCK_BYTE_IN;
	//Data length of 0x0001 means 2 byte data to clock in
	OutputBuffer[dwNumBytesToSend++] = 0x0; //'\x01';
	OutputBuffer[dwNumBytesToSend++] = 0x0; //'\x00';

//	for(int i = 0; i < dwNumBytesToSend; i++ )
//		printf("0x%x ", OutputBuffer[i]);
//	printf("\ndwNumBytesToSend %d\n", dwNumBytesToSend);
	spi_csena();
	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
	dwNumBytesToSend = 0;
//	ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
//	ftStatus = sendJtagCommand(ftHandle, cpu_wr, sizeof cpu_wr);
//	ftStatus = FT_Write(ftHandle, cpu_wr, dwNumBytesToSend, &dwNumBytesSent);
//	        if (ftStatus != FT_OK)
//	        {
//	            return ftStatus;
//	        }
//	printf("SPI write %d bytes\n", dwNumBytesSent);
	usleep(5000);
	ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
//	printf("Queue have %d bytes\n", dwNumBytesSent);
	if(dwNumBytesSent != 1 && !is_mdio)
	{
		printf("SPI queue %d bytes, retry\n", dwNumBytesSent);
		sleep(1);
		ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
		if(dwNumBytesSent != 1 && !is_mdio)
		{
			printf("SPI queue %d bytes, failed\n", dwNumBytesSent);
		}
		else
			ftStatus = FT_Read(ftHandle, data, dwNumBytesSent, &dwNumBytesRead);
	}
	else
		//send out MPSSE command to MPSSE engine
		ftStatus = FT_Read(ftHandle, data, dwNumBytesSent, &dwNumBytesRead);
//	ftStatus = FT_Read(ftHandle, OutputBuffer, dwNumBytesSent, &dwNumBytesRead);
//	for(int i = 0; i < dwNumBytesSent; i++ )
//		printf("0x%x ", OutputBuffer[i]);
//	printf("\n");
	//Read 2 bytes from device receive buffer
//	*data = (InputBuffer[0] << 8) + InputBuffer[1];
	return ftStatus;
}

int flash_enable()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_enable_cmd, sizeof(lsc_enable_cmd));
//	ftStatus = cpld_flash_wr(lsc_refresh_cmd, sizeof(lsc_refresh_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    usleep(1000);

	return ftStatus;
}

int flash_acc_enable()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_acc_mode_cmd, sizeof(lsc_acc_mode_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    sleep(1);
    printf("sleep 1 sec\n");

	return ftStatus;
}

int flash_init()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_init_cmd, sizeof(lsc_init_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    usleep(1000);

	return ftStatus;
}

int flash_disable()
{
	FT_STATUS       ftStatus = FT_OK;
    cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_disable_cmd, sizeof(lsc_disable_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    sleep(1);
    printf("sleep 1 sec\n");
    cpld_csdis();
    ftStatus = cpld_flash_wr(lsc_no_op_cmd, sizeof(lsc_no_op_cmd));
    cpld_csena();
    sleep(3);
    printf("sleep 1 sec\n");
    cpld_csdis();

    return ftStatus;
}

int flash_check_status()
{
	FT_STATUS       ftStatus = FT_OK;
	BYTE busy;
	cpld_csdis();
	ftStatus = cpld_flash_rd_bit(&busy, 1);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    printf("Busy is %d\n", busy);
    cpld_csena();
//    usleep(5000);
    sleep(1);

    BYTE status[4];

    for(int temp = 0; temp < 10; temp++)
    {
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_status_cmd, sizeof(lsc_status_cmd));
	ftStatus = cpld_flash_rd(status, 4);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    printf("Status register is ");
    for(int i = 0; i < 4; i++)
    {
    	printf("0x%x ", status[i]);
    }
    printf("\n");
    cpld_csena();
    usleep(1000);
    }

	return ftStatus;
}

int flash_erase()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_erase_cmd, sizeof(lsc_erase_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    sleep(10);
    printf("sleep 10 sec\n");

	return ftStatus;
}

int flash_refresh()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_refresh_cmd, sizeof(lsc_refresh_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
//    sleep(1);
//    printf("sleep 1 sec\n");

	return ftStatus;
}

int flash_program_done()
{
	FT_STATUS       ftStatus = FT_OK;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_prog_done_cmd, sizeof(lsc_prog_done_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    sleep(1);
    printf("sleep 1 sec\n");

	return ftStatus;
}

int flash_program(BYTE* buf, int size)
{
	FT_STATUS       ftStatus = FT_OK;
	int row = 0;
	cpld_csdis();
	ftStatus = cpld_flash_wr(lsc_cfg_add_cmd, sizeof(lsc_cfg_add_cmd));
    if (ftStatus != FT_OK)
    {
        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
        return ftStatus;
    }
    cpld_csena();
    usleep(1000);
//    printf("sleep 1 sec\n");
	do {
		cpld_csdis();
		ftStatus = cpld_flash_wr(lsc_prog_incr_cmd, sizeof(lsc_prog_incr_cmd));
	    if (ftStatus != FT_OK)
	    {
	        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
	        return ftStatus;
	    }
	    if(size/16 == 0)
	    	ftStatus = cpld_flash_wr(buf, size%16);
	    else
	    	ftStatus = cpld_flash_wr(buf, 16);
	    if (ftStatus != FT_OK)
	    {
	        printf("Failure.  %s returned %d.\n", __FUNCTION__, (int)ftStatus);
	        return ftStatus;
	    }
	    cpld_csena();
	    usleep(1000);
//	    printf("row %d\n", ++row);
	    buf = buf + 16;
	    size -= 16;
	} while(size > 0);

	return ftStatus;
}

int flash_read(BYTE* buf, DWORD size)
{
	FT_STATUS       ftStatus = FT_OK;
	DWORD count = 0;

    do {
        cpld_csdis();
    	ftStatus = cpld_flash_wr(lsc_read_cmd, sizeof(lsc_read_cmd));
        if (ftStatus != FT_OK)
        {
            printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
            return ftStatus;
        }
		ftStatus = cpld_flash_rd(buf+count, 16);
	    cpld_csena();
	    usleep(1000);
		if (ftStatus != FT_OK)
		{
			printf("Failure.  flash_id_check returned %d.\n", (int)ftStatus);
			return ftStatus;
		}
//		for(int i = 0; i < 16; i++)
//			printf("0x%x ", buf[count + i]);
//		printf("\n");

		count += 16;
    } while(count < size);

	return ftStatus;
}

FT_STATUS cpld_program(char* file_name)
{
	FT_STATUS       ftStatus = FT_OK;
	FILE* 			fptr;
	unsigned char buf[2000000];
	memset(buf, 0, sizeof(buf));
    fptr = fopen(file_name, "rb");
	int read_byte = fread(buf, 1, sizeof(buf), fptr);

	printf("program size %d\n", read_byte);

	flash_enable();
	flash_init();
	flash_erase();

    ftStatus = flash_program(buf, read_byte);
	if (ftStatus != FT_OK)
	{
		return ftStatus;
	}
	flash_program_done();
	flash_disable();

	fclose(fptr);

	return ftStatus;
}

FT_STATUS cpld_read(char* file_name)
{
	FT_STATUS       ftStatus = FT_OK;
	FILE* 			fptr;
	fptr = fopen(file_name, "wb");
	if(fptr == NULL)
	{
		printf("Cannot create file %s\n", file_name);
		exit(1);
	}

	flash_enable();
	flash_init();
	BYTE buf[CFG_SIZE];
	memset(buf, 0, sizeof(buf));

	ftStatus = flash_read(buf, sizeof(buf));

	if (ftStatus != FT_OK)
	{
		printf("Failure.  flash_read returned %d.\n", (int)ftStatus);
	}
	flash_disable();

	printf("file size %lu\n", sizeof(buf));
	fwrite(buf, sizeof(buf), 1, fptr);
	fclose(fptr);

	return ftStatus;
}

FT_STATUS mdio_wr(DWORD instance, DWORD dev_addr, DWORD offset, DWORD data)
{
	FT_STATUS       ftStatus = FT_OK;
    ftStatus = spi_wr((MDIO_INST0_CRTL_HI_REG + instance * 4), offset);
    ftStatus |= spi_wr((MDIO_INST0_DATA_LO_REG + instance * 4), (data & 0xFF));
    ftStatus |= spi_wr((MDIO_INST0_DATA_HI_REG + instance * 4), ((data >> 8) & 0xFF));
    ftStatus |= spi_wr((MDIO_INST0_CRTL_LO_REG + instance * 4), (dev_addr << 3) | MDIO_WR_ENA | MDIO_ACC_ENA);
    ftStatus |= spi_wr((MDIO_INST0_CRTL_LO_REG + instance * 4), 0);
    if (ftStatus != FT_OK)
    {
    	printf("spi write failed!\n");
    }

	return ftStatus;
}

FT_STATUS mdio_rd(DWORD instance, DWORD dev_addr, DWORD offset, DWORD* data)
{
	FT_STATUS       ftStatus = FT_OK;
    BYTE			data_lo = 0;
    BYTE			data_hi = 0;

	ftStatus = spi_wr((MDIO_INST0_CRTL_HI_REG + instance * 4), offset);
	ftStatus |= spi_wr((MDIO_INST0_CRTL_LO_REG + instance * 4), (dev_addr << 3) | MDIO_RD_ENA | MDIO_ACC_ENA);
	ftStatus |= spi_wr((MDIO_INST0_CRTL_LO_REG + instance * 4), 0);
	ftStatus |= spi_rd((MDIO_INST0_DATA_LO_REG + instance * 4), &data_lo);
	ftStatus |= spi_rd((MDIO_INST0_DATA_HI_REG + instance * 4), &data_hi);
	*data = data_hi << 8 | data_lo;
    if (ftStatus != FT_OK)
    {
    	printf("spi write failed!\n");
    }

	return ftStatus;
}
