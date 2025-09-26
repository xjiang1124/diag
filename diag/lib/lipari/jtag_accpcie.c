#include "accpcie.h"
#include <time.h>

void show_help() 
{
    printf("Invalid command syntax\n");
    printf("NOTE: port is 1 based!!\n");
    printf("jtag_accpcie rst port\n");
    printf("jtag_accpcie ena port\n");
    printf("jtag_accpcie rd port address\n");
    printf("jtag_accpcie wr port address data\n");
    return;
}

int main(int argc, char *argv[])
{
    DWORD readData = 0xdeadbeef, data = 0xdeadbeef;
    DWORD port = 0;
    ULONGLONG address;
    FT_STATUS rc = FT_OK;
    char  acc_mode[20];

    if ( argc < 2 ) {
        show_help();
        return -1;
    }
    strcpy(acc_mode, argv[1]);
    port = (DWORD)xtoi(argv[2]);
    jtag_init(port);
    if ( !strcmp("rst", acc_mode) ) {
        return(jtag_reset(port));
    } else if ( !strcmp("ena", acc_mode) ) {
        return(jtag_enable(port));
    } else if ( !strcmp("test1", acc_mode) ) {
        ULONGLONG address2;
        unsigned int data1, data2, rdData, LoopCount, i;
        address = strtoul(argv[3], NULL, 0);
        address2 = strtoul(argv[4], NULL, 0);
        LoopCount = strtoul(argv[5], NULL, 0);
        printf(" Rd Address1=%llx   Rd Address2=%llx     Loop Count=%d\n", address, address2, LoopCount);
        rc = jtag_rg(address, &data1);
        if (rc != 0) { printf("ERROR: INIT FAILED (read data1)\n"); return -1; }
        rc = jtag_rg(address2, &data2);
        if (rc != 0) { printf("ERROR: INIT FAILED (read data2)\n"); return -1; }

        for(i=0;i<LoopCount;i++) {
            rc = jtag_rg(address, &rdData);
            if (rc != 0) { 
                printf(" ERROR: (read data1)\n"); 
                return -1; 
            }
            if (rdData != data1) {
                printf(" ERROR: Loop-%d Data Mismatch:  Read=%x    Expected=%x\n", i, rdData, data1); 
                return -1; 
            }
            rc = jtag_rg(address2, &rdData);
            if (rc != 0) { 
                printf(" ERROR: (read data2)\n"); 
                return -1; 
            }
            if (rdData != data2) {
                printf(" ERROR: Loop-%d Data Mismatch:  Read=%x    Expected=%x\n", i, rdData, data2); 
                return -1; 
            }

        }
        return 0;
    } else if ( !strcmp("test2", acc_mode) ) {
        unsigned int rdData, LoopCount;
        address = strtoul(argv[3], NULL, 0);
        LoopCount = strtoul(argv[4], NULL, 0);

        PalermoVspiMBPoll(address, &rdData, LoopCount);
        return 0;
    }


    if ( argc == 4 ) {
        if ( !strcmp("setbar", acc_mode) ) {
            set_bar((ULONGLONG)xtoi(argv[3]));
            set_verbosity(1);
            show_bar();
            set_verbosity(0);
            return 0;	
        } else if ( !strcmp("rd", acc_mode) ) {
    	    //address = (ULONGLONG)xtoi(argv[3]);
            address = strtoul(argv[3], NULL, 0);
            printf("asic read register 0x%llx\n", address);
            rc = jtag_rd(0, address, &data, 2);
            printf("DATA READ = 0x%x\n", data);
            return rc;
        } else if ( !strcmp("rg", acc_mode) ) {
    	    //address = (ULONGLONG)xtoi(argv[3]);
            address = strtoul(argv[3], NULL, 0);
            printf("mailbox read register 0x%llx\n", address);
            rc = jtag_rg(address, &data);
            printf("DATA READ = 0x%x\n", data);
            return rc;
        //For HPE Palermo Switch to read raw address on fpga on Capaci module
        } else if ( !strcmp("spiread", acc_mode) ) {
            //address = (ULONGLONG)xtoi(argv[3]);
            address = strtoul(argv[3], NULL, 0);
            printf("spi read register 0x%llx\n", address);
            rc = palermo_platform_spi_read(address, &data);
            printf("DATA READ = 0x%x\n", data);
            return rc;
        } else {
            printf("ARGC=3 Unsupported command or wrong command syntax.  Type jtag_accpcie to bring up the help\n");
    	    return -1;
        }
    }

    if ( argc == 5 ) {
        if ( !strcmp("wr", acc_mode) ) {
            //address = (ULONGLONG)xtoi(argv[3]);
            //data = (DWORD)xtoi(argv[4]);	
            address = strtoul(argv[3], NULL, 0);
            data = strtoul(argv[4], NULL, 0);	
            printf("jtag asic write 0x%llx -> 0x%x\n", address, data);
            rc = jtag_wr(0, address, data, 2);
            return rc;
        } else if ( !strcmp("wg", acc_mode) ) {
            //address = (ULONGLONG)xtoi(argv[3]);
            //data = (DWORD)xtoi(argv[4]);	
            address = strtoul(argv[3], NULL, 0);
            data = strtoul(argv[4], NULL, 0);	
            printf("jtag write mailbox register 0x%llx -> 0x%x\n", address, data);
            rc = jtag_wg(address, data);
            if( rc == FT_OK ) {
                if( address == J2C_0_CONF_REG
                  ||address == J2C_0_MUX_REG) {
                    rc = jtag_rg(address, &readData);
                    if(readData != data) {
                        printf("ERROR ERROR ERROR\n");
                        printf("ERROR: Port=%d Reg=0x%llx  Write=0x%x  Read=0x%x\n", port, address, data, readData);
                        printf("ERROR ERROR ERROR\n");
                        return -1;
                    }
                    return rc;
                }
            } else {
                printf("ERROR: J2C MailBox Access Failed.  Port=%d Reg=0x%llx\n", port, address);
            }
            return rc;
        //For HPE Palermo Switch to write to raw address on fpga on Capaci module
        } else if ( !strcmp("spiwrite", acc_mode) ) {
            //address = (ULONGLONG)xtoi(argv[3]);
            //data = (DWORD)xtoi(argv[4]);	
            address = strtoul(argv[3], NULL, 0);
            data = strtoul(argv[4], NULL, 0);
            printf("spi write fpga register 0x%llx -> 0x%x\n", address, data);
            rc = palermo_platform_spi_write(address, data);
            return rc;
        } else {
            printf("ARGC=4 Unsupported command or wrong command syntax.  Type jtag_accpcie to bring up the help\n");
    	    return -1;
        }
    }

    printf("Unsupported command or wrong command syntax.  Type jtag_accpcie to bring up the help\n");
    return -1;
}



