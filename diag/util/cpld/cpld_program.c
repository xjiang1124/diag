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
#include <fcntl.h>
#include "acc.h"

#define CFG_SIZE	(16*2175)

void print_usage()
{
	printf("CPLD utility usage:\n");
	printf("read file_name       ----read CPLD contents and dump to a file\n");
	printf("program file_name    ----upgrade CPLD with specific file\n");
	printf("verify file_name     ----compare current CPLD to specific file\n");
}

//program flow: ID check(?)-> enable -> erase -> status -> loop(program-check busy) -> verify
//-> status -> program DONE -> disable

int main(int argc, char *argv[])
{
    int             retCode = -1; // Assume failure
    FT_STATUS       ftStatus = FT_OK;
    DWORD			inst;
    ULONGLONG		address;
    DWORD			data;
    DWORD			flag;
    char			acc_mode[20];
    FILE* 			fptr;

    UNUSED_PARAMETER(argc);
    UNUSED_PARAMETER(argv);
    
    // Make printfs immediate (no buffer)
    setvbuf(stdout, NULL, _IONBF, 0);

    is_spi_flash = 1;
//	is_jtag = 1;
    ftStatus = spi_init();
    if (ftStatus != FT_OK)
    {
        printf("Failure.  Jtag_init returned %d.\n", (int)ftStatus);
        goto exit;
    }

    strcpy(acc_mode, argv[1]);
    if(!strcmp("read", acc_mode))
    {
    	if(argc > 2)
    	{
//			fp = open(argv[2], O_RDWR|O_CREAT, 0660);
    		fptr = fopen(argv[2], "wb");
			if(fptr == NULL)
			{
				printf("Cannot create file %s\n", argv[2]);
				exit(1);
			}
    	}
    	flash_enable();
    	flash_init();
    	BYTE buf[CFG_SIZE];
    	memset(buf, 0, sizeof(buf));
    	if(argc > 2)
    	{
    		ftStatus = flash_read(buf, sizeof(buf));
    	} else {
    		ftStatus = flash_read(buf, 32);
    		printf("data:");
    		for(int i = 0; i < 32; i++)
    		{
    			printf("0x%x ", buf[i]);
    		}
    		printf("\n");
    	}
		if (ftStatus != FT_OK)
		{
			printf("Failure.  flash_read returned %d.\n", (int)ftStatus);
		}
		flash_disable();
		if(argc > 2)
		{
			printf("file size %ld\n", sizeof(buf));
			fwrite(buf, sizeof(buf), 1, fptr);
			fclose(fptr);
		}
		return ftStatus;

    } else if(!strcmp("program", acc_mode))
    {
    	char buf[2000000];
    	memset(buf, 0, sizeof(buf));
        fptr = fopen(argv[2], "rb");
    	int read_byte = fread(buf, 1, sizeof(buf), fptr);

//    	BYTE* pos_start = strstr(buffer, "L0000000");
//    	BYTE* pos_end = strstr(buffer, "NOTE END CONFIG DATA");
//    	for(int i = 0; i < 32; i++)
//    	{
//    		printf("%c", *(pos_end - 10 + i));
//    	}
//    	printf("\n");
//    	int size = (unsigned long long)pos_end - 5 - (unsigned long long)pos_start - 10;
    	printf("program size %d\n", read_byte);
//        ftStatus = flash_program(pos + 10, CFG_SIZE);
//    	flash_refresh();
//    	flash_acc_enable();
    	flash_enable();
    	flash_init();
    	flash_erase();
//    	flash_acc_enable();
        ftStatus = flash_program(buf, read_byte);
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
		flash_program_done();
		flash_disable();

		fclose(fptr);
    } else if(!strcmp("id", acc_mode))
	{
        ftStatus = flash_id_check();
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
    } else if(!strcmp("erase", acc_mode))
	{
    	flash_enable();
    	flash_init();
        ftStatus = flash_erase();
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
    } else if(!strcmp("refresh", acc_mode))
	{
//    	flash_enable();
//    	flash_init();
        ftStatus = flash_refresh();
		if (ftStatus != FT_OK)
		{
			return ftStatus;
		}
		flash_check_status();
    } else {
    	printf("Unsupported access mode\n");
    	return -1;
    }


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
