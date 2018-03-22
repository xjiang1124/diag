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


int main(int argc, char *argv[])
{
    int             retCode = -1; // Assume failure
//    int             f = 0;
    FT_STATUS       ftStatus = FT_OK;
//    struct timeval  startTime;
    BYTE			address = 0;
    BYTE			data = 0;
    char			acc_mode[20];

    UNUSED_PARAMETER(argc);
    UNUSED_PARAMETER(argv);
    
    // Make printfs immediate (no buffer)
    setvbuf(stdout, NULL, _IONBF, 0);

    strcpy(acc_mode,argv[1]);
    if(!strcmp("spi", acc_mode))
    {
    	printf("spi mode\n");
    	is_spi_flash = 1;
    } else if(!strcmp("reg", acc_mode))
    {
    	printf("internal reg access mode\n");
    	is_spi_flash = 0;
    } else {
    	printf("Unsupported mode\n");
    	goto exit;
    }

    ftStatus = spi_init();
    if (ftStatus != FT_OK)
    {
        printf("Failure.  spi_init returned %d.\n", (int)ftStatus);
        goto exit;
    }


//    for(int i = 1; i < argc; i++)
//    {
//		byOutputBuffer[bytesToWrite++] = (BYTE)xtoi(argv[i]);
//		printf("arg 0x%x\n", byOutputBuffer[bytesToWrite - 1]);
//    }

    address = (BYTE)xtoi(argv[2]);

    if(argc > 3)
    {
    	data = (BYTE)xtoi(argv[3]);
        ftStatus = spi_wr(ftHandle, address, data);
        if (ftStatus != FT_OK)
        {
        	printf("spi write failed!\n");
            return ftStatus;
        }
    }
    else
    {
//    	ftStatus = flash_id_check();
		ftStatus = spi_rd(ftHandle, address, &data);
		if (ftStatus != FT_OK)
		{
			printf("spi read failed!\n");
			return ftStatus;
		}
		printf("SPI read address 0x%x, data 0x%x\n", address, data);
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
	if(ftHandle_a)
		FT_Close(ftHandle_a);
	if(ftHandle)
		FT_Close(ftHandle);

    return retCode;
}
