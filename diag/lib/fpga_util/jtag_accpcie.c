#include "accpcie.h"
#include <time.h>

#define SCRATCH_REG1 0x30780000
#define SCRATCH_REG2 0x6f240000

uint64_t rdtsc() {
    unsigned int lo, hi;
    __asm__ __volatile__ (
        "rdtsc"
        : "=a"(lo), "=d"(hi)
    );
    return ((uint64_t)hi << 32) | lo;
}

double get_cpu_frequency() {
    struct timespec start, end;
    uint64_t start_cycles, end_cycles;
    double elapsed_time;

    // Measure starting time and cycles
    clock_gettime(CLOCK_MONOTONIC, &start);
    start_cycles = rdtsc();

    // Sleep for 1 second
    sleep(1);

    // Measure ending time and cycles
    clock_gettime(CLOCK_MONOTONIC, &end);
    end_cycles = rdtsc();

    elapsed_time = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    return (end_cycles - start_cycles) / elapsed_time;
}

int reg_perf_test(uint64_t reg_addr, unsigned int loopcount, char* mode) {
    unsigned int ite;
    int ret = -1;
    //clock_t start, end;
    uint64_t start, end;
    double cpu_freq;
    double cpu_time_used;
    double cpu_time_per_ite;
    unsigned int data;

    printf("=================\n");
    printf("REG %s at 0x%lx\n", mode, reg_addr);

	cpu_freq = (double)get_cpu_frequency();
    printf("CPU Frequency: %.2f Hz\n", cpu_freq);

    //start = clock();
    start = rdtsc();
    for ( ite = 0; ite < loopcount; ite++) {
        if ( !strcmp("rd", mode) ) {
            jtag_rd(0, SCRATCH_REG1, &data, 2);
        } else if ( !strcmp("wr", mode) ) { 
            jtag_wr(0, SCRATCH_REG1, ite, 2);
        } else if ( !strcmp("comp", mode) ) {
            jtag_wr(0, reg_addr, ite, 2);

            // Read back from registers
            jtag_rd(0, reg_addr, &data, 2);
            if (data != ite) {
                printf("Error at iteration %d: Data mismatch at 0x30780000. Expected: %X, Read: %X\n", ite, ite, data);
                return -1;
            }

            if (ite%10000 == 0) {
                printf("%d\n", ite);
            }
        } else if ( !strcmp("rev_comp", mode) ) {
            // Write to registers
            jtag_wr(0, reg_addr, loopcount-ite, 2);

            jtag_rd(0, reg_addr, &data, 2);
            if (data != loopcount - ite) {
                printf("Error at iteration %d: Data mismatch at 0x6f240000. Expected: %X, Read: %X\n", ite, loopcount - ite, data);
                return -1;
            }

            if (ite%10000 == 0) {
                printf("%d\n", ite);
            }
        } else {
            printf("Wrong mode! %s\n", mode);
            printf("Support mode: rd/wr/comp/rev_comp\n");
            return -1;
        }
    }
    printf("REG: 0x%lx; ite: %d\n", reg_addr, ite);
    //end = clock();
    end = rdtsc();
    cpu_time_used = ((double) (end - start)) * 1000.0 / cpu_freq;
    cpu_time_per_ite = cpu_time_used / loopcount;
    printf("Total time used to run test for cycles: %.4f ms\n", cpu_time_used);
    printf("OP Time per iteration: %.4f ms\n", cpu_time_per_ite);
    
    ret = 0;
    return ret;
}


int main(int argc, char *argv[])
{
    DWORD data = 0xdeadbeef;
    DWORD port = 0, mode, size, flag;
    ULONGLONG address;
    char  acc_mode[20];
    char asic_name[20];

    if ( argc < 2 ) {
        printf("Invalid command syntax\n");
        printf("jtag_accpcie rst <port(1 based)>\n");
        printf("jtag_accpcie ena <port(1 based)>\n");
        printf("jtag_accpcie rd <port(1 based)> <address>\n");
        printf("jtag_accpcie wr <port(1 based)> <address> <data>\n");
        printf("jtag_accpcie test <mode: rd/wr/comp/rev_comp> <port(1 based)> <address> <loopcount>\n");
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
    } else if ( !strcmp("rdow", acc_mode) ) {
        if ( argc < 7 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
        mode = (DWORD)xtoi(argv[4]);
        size = (DWORD)xtoi(argv[5]);
        flag = (DWORD)xtoi(argv[6]);    
        jtag_ow_read(mode, size, address, &data, flag);
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("wrow", acc_mode) ) {
        if ( argc < 8 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
        mode = (DWORD)xtoi(argv[4]);
        size = (DWORD)xtoi(argv[5]);
        data = (DWORD)xtoi(argv[6]);    
        flag = (DWORD)xtoi(argv[7]);    
        jtag_ow_write(mode, size, address, data, flag);
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
        if (argc < 5) {
            printf("ERROR: Invalid command syntax for test\n");
            printf("Usage: jtag_accpcie test <mode> <port(1 based)> <reg_addr> <loopcount>\n");
            return -1;
        }

        char* mode = argv[2];

        printf("jtag test register %d\n", port);
   
        port = (DWORD)xtoi(argv[3]);
        uint64_t reg_addr = (uint64_t)xtoi(argv[4]);

        char *endptr;
        unsigned int loopcount = (DWORD)strtol(argv[5], &endptr, 10);
        printf("loopcount: %d\n", loopcount);
        if (loopcount > 0xFFFFFFFF){
            printf("ERROR: The register can take a 32-bit value (0x00000000 – 0xFFFFFFFF)\n");
            return -1;
        }

        int ret;

        jtag_init(port);

        ret = reg_perf_test(reg_addr, loopcount, mode);
        if (ret != 0) {
            return -1;
        }

        jtag_close();

        return 0;
    } else {
        printf("Unsupported access mode\n");
        return -1;
    }
    return 0;
}
