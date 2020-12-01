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
#define HAPS
int main(int argc, char *argv[])
{
    int             retCode = -1; // Assume failure
    FT_STATUS       ftStatus = FT_OK;
    DWORD			inst;
    // CHANNEL_A 0; CHANNEL_B 1
    int				port = 1;
    ULONGLONG		address;
    DWORD			data;
    DWORD			flag;
    char			acc_mode[20];

    UNUSED_PARAMETER(argc);
    UNUSED_PARAMETER(argv);
    
    // Make printfs immediate (no buffer)
    setvbuf(stdout, NULL, _IONBF, 0);
    strcpy(acc_mode, argv[1]);
#ifdef HAPS
    port = (int)xtoi(argv[2]);
    inst = (DWORD)xtoi(argv[3]);
#else
    inst = (DWORD)xtoi(argv[2]);
#endif

//    memset(buffer, 0, 100);
    ftStatus = jtag_init(port);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  Jtag_init returned %d.\n", (int)ftStatus);
        goto exit;
    }

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

    ftStatus = FT_ResetDevice(ftHandle);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
        goto exit;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        goto exit;
    }

    ftStatus = FT_SetLatencyTimer(ftHandle, 1);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_SetLatencyTimer returned %d\n", (int)ftStatus);
        goto exit;
    }

    ftStatus = FT_SetTimeouts(ftHandle, 3000, 3000);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_SetTimeouts returned %d\n", (int)ftStatus);
        goto exit;
    }
    
    ftStatus = FT_SetBitMode(ftHandle, 0x0B, FT_BITMODE_MPSSE);
    if (ftStatus != FT_OK) 
    {
        printf("Failure.  FT_SetBitMode returned %d\n", (int)ftStatus);
        goto exit;
    }
#endif

#if 0
    bytesToWrite = bufferSize;
    ftStatus = setupJtagConfig(ftHandle, bytesToWrite);
    if (ftStatus != FT_OK)
    {
        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
        goto exit;
    }
#endif

    if(!strcmp("wr", acc_mode))
    {
#ifdef HAPS
        address = (ULONGLONG)xtoi(argv[4]);
    	data = (DWORD)xtoi(argv[5]);
    	flag = (DWORD)xtoi(argv[6]);
#else
        address = (ULONGLONG)xtoi(argv[3]);
    	data = (DWORD)xtoi(argv[4]);
    	flag = (DWORD)xtoi(argv[5]);
#endif
        ftStatus = jtag_wr(inst, address, data, flag);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
    } else if(!strcmp("rd", acc_mode))
    {
#ifdef HAPS
        address = (ULONGLONG)xtoi(argv[4]);
    	flag = (DWORD)xtoi(argv[5]);
#else
        address = (ULONGLONG)xtoi(argv[3]);
        flag = (DWORD)xtoi(argv[4]);
#endif
        ftStatus = jtag_rd(inst, address, &data, flag);
		if (ftStatus != FT_OK)
		{
			printf("JTAG Read failed!\n");
			return ftStatus;
		}
		printf("0x%08x\n", data);
//		return data;
    } else if(!strcmp("rst", acc_mode))
	{
        ftStatus = jtag_reset(inst);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
    } else if(!strcmp("ena", acc_mode))
	{
        ftStatus = jtag_enable(inst);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
    } else if(!strcmp("id", acc_mode))
    {
        ftStatus = jtag_id(inst, &data);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
		printf("Read data 0x%08x\n", data);
    } else if(!strcmp("test", acc_mode))
    {
#ifdef HAPS
        address = (ULONGLONG)xtoi(argv[4]);
    	data = (DWORD)xtoi(argv[5]);
    	flag = (DWORD)xtoi(argv[6]);
#else
    	address = (ULONGLONG)xtoi(argv[3]);
    	data = (DWORD)xtoi(argv[4]);
    	flag = (DWORD)xtoi(argv[5]);
#endif
    	ftStatus = jtag_wr(inst, address, data, flag);
		if (ftStatus != FT_OK)
		{
			printf(" write failed %d\n", ftStatus);
			return ftStatus;
		}

		//test purpose only
		DWORD rd_data = 0;

		ftStatus = jtag_rd(inst, address, &rd_data, flag);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
		if(data == rd_data)
			printf("Match! read data 0x%08x\n", rd_data);
		else{
			printf("Failed! write 0x%08x, read 0x%08x\n", data, rd_data);

			ftStatus = jtag_init(port);
			sleep(1);
			ftStatus = jtag_rd(inst, address, &rd_data, flag);
			if (ftStatus != FT_OK)
			{
				return ftStatus;
			}
			if(data == rd_data)
				printf("reMatch! read data 0x%08x\n", rd_data);
			else
				printf("Fatal! write 0x%08x, read 0x%08x\n", data, rd_data);
		}

    } else {
    	printf("Unsupported access mode\n");
    	return -1;
    }



//    bytesToWrite = 0;
//    printf("argc %d, argv2 0x%x\n", argc, stoi(argv[3]));
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[1], NULL, 10);
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[2], NULL, 10);
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[3], NULL, 10);
//
//    ftStatus = sendJtagCommand(ftHandle, byOutputBuffer, bytesToWrite);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }
//
//    bytesToWrite = 0;
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[4], NULL, 10);
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[5], NULL, 10);
//    byOutputBuffer[bytesToWrite++] = (BYTE)strtol(argv[6], NULL, 10);
//
//    ftStatus = sendJtagCommand(ftHandle, byOutputBuffer, bytesToWrite);
//    if (ftStatus != FT_OK)
//    {
//        return ftStatus;
//    }

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
#endif
#if 0
    bytesReceived = 4242;
    while(bytesReceived)
    {
		//get status first
		ftStatus = FT_GetQueueStatus(ftHandle, &bytesReceived);
		if (ftStatus != FT_OK)
		{
			printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
				   (int)ftStatus);
			goto exit;
		}
		printf("\nGot %d (of %d) bytes.\n", (int)bytesReceived, (int)bytesWritten);

		// Even if D2XX has the wrong number of bytes, create our
		// own buffer so we can read and display them.
		// fix me: bytesRerceived need to be changed according to how many bytes will be read from chip
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
		printf("FT_read %d bytes\n", bytesRead);
	    printf("Receive data:\n");
	    for(f = 0; f < bytesRead; f++)
	    {
	    	printf("0x%x ", readBuffer[f]);
	    }
	    printf("\n");
	    free(readBuffer);
    }
#endif

#if 0
    gettimeofday(&startTime, NULL);

//    sleep(1);
	ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
	if (ftStatus != FT_OK)
	{
		printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
			   (int)ftStatus);
		goto exit;
	}

	printf("first queue status %d %d bytes\n", rx_buf, tx_buf);

    while(retry < 20)
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
		// Then copy D2XX's buffer to ours.
		ftStatus = FT_Read(ftHandle, &buffer[count], rx_buf, &bytesRead);
		if (ftStatus != FT_OK)
		{
			printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
			goto exit;
		}
		printf("FT_read %d bytes\n", bytesRead);

		count += bytesRead;
//		if(count >= 8)
//			break;
//		printf("queue clear %d bytes\n", bytesRead);

		ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
		if (ftStatus != FT_OK)
		{
			printf("\nFailure.  FT_GetQueueStatus returned %d.\n",
				   (int)ftStatus);
			goto exit;
		}

		if(!rx_buf)
			retry ++;
		else
			retry = 0;
    }

	printf("Receive data:\n");
	for(f = 0; f < count; f++)
	{
		printf("0x%x ", buffer[f]);
	}
	printf("\n");
#endif
//    if (bytesRead != bytesReceived)
//    {
//        printf("Failure.  FT_Read only read %d (of %d) bytes.\n",
//               (int)bytesRead,
//               (int)bytesReceived);
//        goto exit;
//    }
#if 0
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
#endif
    // Check that queue hasn't gathered any additional unexpected bytes

//    bytesReceived = 4242; // deliberately junk
//    ftStatus = FT_GetQueueStatus(ftHandle, &bytesReceived);
//    if (ftStatus != FT_OK)
//    {
//        printf("Failure.  FT_GetQueueStatus returned %d.\n",
//               (int)ftStatus);
//        goto exit;
//    }
//
//    if (bytesReceived > 1)
//    {
//        printf("Failure.  %d bytes in input queue -- expected none.\n",
//               (int)bytesReceived);
//        goto exit;
//    }

    // Success
//    printf("\nTest PASSED.\n");
//    printf("Receive data:\n");
//    for(f = 0; f < bytesRead; f++)
//    {
//    	printf("0x%x ", readBuffer[f]);
//    }
//    printf("\n");

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
