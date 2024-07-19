#include "accpcie.h"
#include <time.h>

#define SCRATCH_REG1 0x30780000
#define SCRATCH_REG2 0x6f240000

int main(int argc, char *argv[])
{
    DWORD data = 0xdeadbeef;
    DWORD port = 0;
    ULONGLONG address;
    char  acc_mode[20];
    char asic_name[20];

    if ( argc < 2 ) {
        printf("Invalid command syntax\n");
        printf("jtag_accpcie rst port(1 based)\n");
        printf("jtag_accpcie ena port(1 based)\n");
        printf("jtag_accpcie rd port(1 based) address\n");
        printf("jtag_accpcie wr port(1 based) address data\n");
        printf("jtag_accpcie test port(1 based) loopcount\n");
        return -1;
    }
    strcpy(acc_mode, argv[1]);
    if ( !strcmp("setbar", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        set_bar((ULONGLONG)xtoi(argv[2]));
        set_verbosity(1);
        show_bar();
        set_verbosity(0);    
    } else if ( !strcmp("wr", acc_mode) ) {
        if ( argc < 5 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
	    data = (DWORD)xtoi(argv[4]);	
        jtag_wr(0, address, data, 2);
        jtag_close();
    } else if ( !strcmp("rd", acc_mode) ) {
        if ( argc < 4 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
        jtag_rd(0, address, &data, 2);
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("rst", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        jtag_reset(port);
        jtag_close();
    } else if ( !strcmp("ena", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        jtag_enable(port);
        jtag_close();
    } else if ( !strcmp("rg", acc_mode) ) {
        if ( argc < 4 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
        jtag_rg(address, &data);
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("wg", acc_mode) ) {
        if ( argc < 5 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
        data = (DWORD)xtoi(argv[4]);    
        jtag_wg(address, data);
        jtag_close();
    } else if ( !strcmp("set_asic", acc_mode) ) {
        if ( argc < 4 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        strcpy(asic_name, argv[3]);
        set_asic_target(asic_name);
        jtag_close();
    } else if ( !strcmp("show_asic", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        show_asic_target(asic_name);
        printf("asic are target is set for %s\n", asic_name);
        jtag_close();
    } else if ( !strcmp("clr", acc_mode) ) {
        port = (DWORD)xtoi(argv[2]);
        printf("Clear port %d\n", port);
        jtag_clear(port);
    } else if ( !strcmp("test", acc_mode) ) {
        if (argc < 4) {
            printf("ERROR: Invalid command syntax for test\n");
            printf("Usage: jtag_accpcie test <port(1 based)> <loopcount>\n");
            return -1;
        }
        printf("jtag test register %d\n", port);
   
        port = (DWORD)xtoi(argv[2]);
        ULONGLONG loopcount = (DWORD)xtoi(argv[3]);
       
        if (loopcount > 0xFFFFFFFF){
            printf("ERROR: The register can take a 32-bit value (0x00000000 – 0xFFFFFFFF)\n");
            return -1;
        }
        clock_t start, end;
        double cpu_time_used;
        start = clock();

        jtag_init(port);
        for (ULONGLONG i = 0; i < loopcount; i++) {
            // Write to registers
            jtag_wr(0, SCRATCH_REG1, i, 2);
            jtag_wr(0, SCRATCH_REG2, loopcount-i, 2);

            // manually inject a wrong value
            // if (i == 20001){
            //     jtag_wr(0, SCRATCH_REG2, 0, 2);
            // }

            // Read back from registers
            jtag_rd(0, SCRATCH_REG1, &data, 2);
            if (data != i) {
                printf("Error at iteration %lld: Data mismatch at 0x30780000. Expected: %llX, Read: %X\n", i, i, data);
                jtag_close();
                return -1;
            }

            jtag_rd(0, SCRATCH_REG2, &data, 2);
            if (data != loopcount - i) {
                printf("Error at iteration %lld: Data mismatch at 0x6f240000. Expected: %llX, Read: %X\n", i, loopcount - i, data);
                jtag_close();
                return -1;
            }

            if (i%10000 == 0) {
                printf("%.010lld\n", i);
            }
        }
        jtag_close();

        end = clock();
        cpu_time_used = ((double) (end - start)) * 1000 / CLOCKS_PER_SEC;
        printf("Total time used to run test for %lld cycles: %.4f ms\n", loopcount, cpu_time_used);

        return 0;
    } else {
        printf("Unsupported access mode\n");
        return -1;
    }
    return 0;
}


