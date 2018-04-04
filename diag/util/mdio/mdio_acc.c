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

#if 0
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "ftd2xx.h"



#define UNUSED_PARAMETER(x) (void)(x)

#define ARRAY_SIZE(x) (sizeof((x))/sizeof((x)[0]))

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
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_OUT = '\x10';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_OUT = '\x11';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_OUT = '\x12';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_OUT = '\x13';
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_IN = '\x20';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_IN = '\x22';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_IN = '\x24';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_IN = '\x26';

BYTE 	OutputBuffer[512];
DWORD	dwNumBytesToSend = 0;
DWORD	dwNumBytesSent  = 0;
DWORD 	dwNumBytesRead;

BYTE   setup[3] =
{
    0x80, 0x10, 0x1B  // TMS start high; TDO is input
};

BYTE   ena_lpbk[1] =
{
    0x84              // enable TDI/TDO loopback
};
BYTE   dis_lpbk[1] =
{
    0x85              // disable TDI/TDO loopback
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

BYTE   cpu_wr[15] =
{
	0x3C, 0xB, 0x0, 0x00, 0x12, 0x80, 0x00, 0xC1, 0x80, 0x40, 0x00, 0xC1, 0x80, 0x40, 0x00
};

BYTE   cpu_rd[11] =
{
	0x3C, 0x7, 0x0, 0x00, 0x22, 0x40, 0x00, 0xC1, 0x80, 0x40, 0x00
};

BYTE   cpu_res[11] =
{
	0x3C, 0x7, 0x0, 0x00, 0x42, 0x00, 0x00, 0xC1, 0x80, 0x40, 0x00
};

BYTE   con_red[5] =
{
	0x3C, 0x1, 0x0, 0x00, 0x82
};

#ifdef _WIN32
/* Windows doesn't have gettimeofday but winsock.h does have a
 * definition of timeval:
 *
 * struct timeval 
 * {
 *     long  tv_sec;
 *     long  tv_usec;
 * };
 */
static int gettimeofday(struct timeval *tv, void *timezone)
{
    SYSTEMTIME st;

    UNUSED_PARAMETER(timezone);

    GetSystemTime(&st);

    tv->tv_sec = (long)(
        (st.wHour * 60 * 60) +
        (st.wMinute * 60) +
        (st.wSecond));

    tv->tv_usec = 0; // We're not using microseconds here.

    return 0;
}



static void timersub(struct timeval *a,
                     struct timeval *b,
                     struct timeval *res)
{
    res->tv_sec = a->tv_sec - b->tv_sec;
    res->tv_usec = 0;
}
#else
    #include <sys/time.h>
#endif // _WIN32

int xtoi(char *hexstring)
{
	int	i = 0;

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


static FT_STATUS sendJtagCommand(FT_HANDLE      ftHandle,
                                 BYTE *sequence,
                                 const size_t   length)
{
    FT_STATUS  ftStatus = FT_OK;
    DWORD      bytesToWrite = (DWORD)length;
    DWORD      bytesWritten = 0;
  
    ftStatus = FT_Write(ftHandle, sequence, bytesToWrite, &bytesWritten);
    printf("bytesWritten 0x%x\n", sequence[0]);
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
		OutputBuffer[dwNumBytesToSend++] = 0x18;
		OutputBuffer[dwNumBytesToSend++] = 0x1b;
	}
}

void spi_csdis()
{
	for(int i = 0; i < 5; i++)
	{
		OutputBuffer[dwNumBytesToSend++] = 0x80;
		OutputBuffer[dwNumBytesToSend++] = 0x10;
		OutputBuffer[dwNumBytesToSend++] = 0x1b;
	}
}

static FT_STATUS spi_init(FT_HANDLE ftHandle)
{
    FT_STATUS       ftStatus = FT_OK;

    ftStatus = FT_ResetDevice(ftHandle);
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

    ftStatus = FT_SetLatencyTimer(ftHandle, 1);
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

    ftStatus = FT_SetBitMode(ftHandle, 0x0B, FT_BITMODE_MPSSE);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        return ftStatus;
    }


    ftStatus = sendJtagCommand(ftHandle, setup, sizeof setup);
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

static FT_STATUS spi_wr(FT_HANDLE ftHandle, BYTE address, BYTE data)
{
	FT_STATUS       ftStatus = FT_OK;
//printf("spiwr 0x%x\n", data);
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
	//Clear output buffer
	dwNumBytesToSend = 0;
	return ftStatus;
}

static FT_STATUS spi_rd(FT_HANDLE ftHandle, BYTE address, BYTE* data)
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

//	for(int i = 0; i < 3; i++ )
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
	printf("SPI write %d bytes\n", dwNumBytesSent);
	sleep(1);
	ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
	if(dwNumBytesSent != 1)
		printf("SPI queue %d bytes, failed\n", dwNumBytesSent);
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
#endif

int main(int argc, char *argv[])
{
    int             retCode = -1; // Assume failure
//    int             f = 0;
    DWORD           driverVersion = 0;
    FT_STATUS       ftStatus = FT_OK;
    int             portNum = 1; // First device found
//    struct timeval  startTime;
    BYTE			dev_addr = 0;
    DWORD			data = 0;
    BYTE			instance = 0;
    BYTE			offset = 0;

    UNUSED_PARAMETER(argc);
    UNUSED_PARAMETER(argv);
    
    // Make printfs immediate (no buffer)
    setvbuf(stdout, NULL, _IONBF, 0);
    is_spi_flash = 0;
    is_mdio = 1;
#if 0
    printf("Opening FTDI device %d.\n", portNum);

    ftStatus = FT_Open(portNum, &ftHandle);
    if (ftStatus != FT_OK)
    {
        printf("FT_Open(%d) failed, with error %d.\n", portNum, (int)ftStatus);
        printf("On Linux, lsmod can check if ftdi_sio (and usbserial) are present.\n");
        printf("If so, unload them using rmmod, as they conflict with ftd2xx.\n");
        goto exit;
    }

    assert(ftHandle != NULL);

    ftStatus = FT_GetDriverVersion(ftHandle, &driverVersion);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_GetDriverVersion returned %d.\n",
               (int)ftStatus);
        goto exit;
    }

    printf("D2XX version : %x.%x.%x\n", 
           (unsigned int)((driverVersion & 0x00FF0000) >> 16),
           (unsigned int)((driverVersion & 0x0000FF00) >> 8),
           (unsigned int)(driverVersion & 0x000000FF) 
           );
#endif

    ftStatus = spi_init();
    if (ftStatus != FT_OK)
    {
        printf("Failure.  spi_init returned %d.\n", (int)ftStatus);
        goto exit;
    }
    assert(ftHandle);

//    for(int i = 1; i < argc; i++)
//    {
//		byOutputBuffer[bytesToWrite++] = (BYTE)xtoi(argv[i]);
//		printf("arg 0x%x\n", byOutputBuffer[bytesToWrite - 1]);
//    }
    instance = (BYTE)xtoi(argv[1]);
    dev_addr = (BYTE)xtoi(argv[2]);
    offset = (BYTE)xtoi(argv[3]);

    printf("inst %d, dev 0x%x, offset 0x%x\n", instance, dev_addr, offset);

    if(argc > 4)
    {
    	data = xtoi(argv[4]);
    	ftStatus = mdio_wr(instance, dev_addr, offset, data);
        if (ftStatus != FT_OK)
        {
        	printf("spi write failed!\n");
            return ftStatus;
        }
    }
    else
    {
    	ftStatus = mdio_rd(instance, dev_addr, offset, &data);
		if (ftStatus != FT_OK)
		{
			printf("spi read failed!\n");
			return ftStatus;
		}
		printf("SPI read 0x%x\n",data);
    }

//    bytesToWrite = 0;
//    for(int i = 1; i < 4; i++)
//    {
//		byOutputBuffer[bytesToWrite++] = (BYTE)xtoi(argv[i]);
//		printf("arg 0x%x\n", byOutputBuffer[bytesToWrite - 1]);
//    }
//
//    ftStatus = sendJtagCommand(ftHandle, byOutputBuffer, bytesToWrite);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }
//
//    bytesToWrite = 0;
//    for(int i = 4; i < argc; i++)
//    {
//		byOutputBuffer[bytesToWrite++] = (BYTE)xtoi(argv[i]);
//		printf("arg 0x%x\n", byOutputBuffer[bytesToWrite - 1]);
//    }
//
//    ftStatus = sendJtagCommand(ftHandle, byOutputBuffer, bytesToWrite);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

//    spi_rd(ftHandle, 0x2, &data);
//    printf("SPI read 0x%x\n",data);

#if 0
    writeBuffer = (unsigned char *)malloc((size_t)bufferSize);
    if (writeBuffer == NULL)
        goto exit;

    // Fill write buffer with consecutive values.
    for (f = 0; f < (int)bufferSize; f++) 
    {
        writeBuffer[f] = (unsigned char)f;
    }
    
    printf("\nWriting %d bytes to JTAG loopback...\n", 
           (int)bytesToWrite);

    ftStatus = FT_Write(ftHandle, 
                        writeBuffer,
                        bytesToWrite, 
                        &bytesWritten);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
        goto exit;
    }
    
    if (bytesWritten != bytesToWrite)
    {
        printf("Failure.  FT_Write wrote %d bytes instead of %d.\n",
               (int)bytesWritten,
               (int)bytesToWrite);
        goto exit;
    }

    printf("%d bytes written.\n", (int)bytesWritten);
    
    // Keep checking queue until D2XX has received all the bytes we wrote.
    journeyDuration = 1;  // One second should be enough
    
    gettimeofday(&startTime, NULL);
    
    for (bytesReceived = 0, queueChecks = 0; 
         bytesReceived < bytesWritten; 
         queueChecks++)
    {
        // Periodically check for time-out 
        if (queueChecks % 512 == 0)
        {
            struct timeval now;
            struct timeval elapsed;
            
            gettimeofday(&now, NULL);
            timersub(&now, &startTime, &elapsed);

            if (elapsed.tv_sec > (long int)journeyDuration)
            {
                // We've waited too long.  Give up.
                printf("\nTimed out after %ld seconds\n", elapsed.tv_sec);
                break;
            }
            
            // Display number of bytes D2XX has received
            printf("%s%d", 
                   queueChecks == 0 ? "Number of bytes in D2XX receive-queue: " : ", ",
                   (int)bytesReceived);
        }

        ftStatus = FT_GetQueueStatus(ftHandle, &bytesReceived);
        if (ftStatus != FT_OK)
        {
            printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
                   (int)ftStatus);
            goto exit;
        }
    }

    printf("\nGot %d (of %d) bytes.\n", (int)bytesReceived, (int)bytesWritten);

    // Even if D2XX has the wrong number of bytes, create our
    // own buffer so we can read and display them.
    readBuffer = (unsigned char *)calloc(bytesReceived, sizeof(unsigned char));
    if (readBuffer == NULL)
    {
        printf("Failed to allocate %d bytes.\n", (int)bytesReceived);
        goto exit;
    }

    // Then copy D2XX's buffer to ours.
    ftStatus = FT_Read(ftHandle, readBuffer, bytesReceived, &bytesRead);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
        goto exit;
    }

    if (bytesRead != bytesReceived)
    {
        printf("Failure.  FT_Read only read %d (of %d) bytes.\n",
               (int)bytesRead,
               (int)bytesReceived);
        goto exit;
    }
    
    if (0 != memcmp(writeBuffer, readBuffer, bytesRead))
    {
        printf("Failure.  Read-buffer does not match write-buffer.\n");
        printf("Write buffer:\n");
        dumpBuffer(writeBuffer, bytesReceived);
        printf("Read buffer:\n");
        dumpBuffer(readBuffer, bytesReceived);
        goto exit;
    }

    printf("Received bytes match transmitted bytes.\n");

    // Check that queue hasn't gathered any additional unexpected bytes
    bytesReceived = 4242; // deliberately junk
    ftStatus = FT_GetQueueStatus(ftHandle, &bytesReceived);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_GetQueueStatus returned %d.\n",
               (int)ftStatus);
        goto exit;
    }

    if (bytesReceived != 0)
    {
        printf("Failure.  %d bytes in input queue -- expected none.\n",
               (int)bytesReceived);
        goto exit;
    }

    // Success
    printf("\nTest PASSED.\n");
#endif

    retCode = 0;

exit:
//    free(readBuffer);
//    free(writeBuffer);

//    if (ftHandle != NULL)
//    {
//        (void)FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
//        FT_Close(ftHandle);
//    }

    return retCode;
}
