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

int reg_perf_test(ULONGLONG reg_addr, ULONGLONG loopcount, char* mode, DWORD stop_on_error) {
    unsigned int ite;
    int rc;
    //clock_t start, end;
    uint64_t start, end;
    double cpu_freq;
    double cpu_time_used;
    double cpu_time_per_ite;
    DWORD data;

    printf("=================\n");
    printf("REG %s at 0x%llx\n", mode, reg_addr);

    cpu_freq = (double)get_cpu_frequency();
    printf("CPU Frequency: %.2f Hz\n", cpu_freq);

    //start = clock();
    start = rdtsc();
    for ( ite = 0; ite < loopcount; ite++) {
        if ( !strcmp("rd", mode) ) {
            rc = jtag_rd(0, SCRATCH_REG1, &data, 2);
            if ( rc ) {
                printf("read register 0x%x with error code %d\n", SCRATCH_REG1, rc);
                if ( stop_on_error )
                    return rc;
            }
        } else if ( !strcmp("wr", mode) ) { 
            rc = jtag_wr(0, SCRATCH_REG1, ite, 2);
            if ( rc ) {
                printf("write register 0x%x with error code %d\n", SCRATCH_REG1, rc);
                if ( stop_on_error )
                    return rc;
            }
        } else if ( !strcmp("comp", mode) ) {
            rc = jtag_wr(0, reg_addr, ite, 2);
            if ( rc ) {
                printf("write register 0x%llx with error code %d\n", reg_addr, rc);
                if ( stop_on_error )
                    return rc;
            }

            // Read back from registers
            rc = jtag_rd(0, reg_addr, &data, 2);
            if ( rc ) {
                printf("read register 0x%llx with error code %d\n", reg_addr, rc);
                if ( stop_on_error )
                    return rc;
            }
            if (data != ite) {
                printf("Error at iteration %d: Data mismatch at 0x30780000. Expected: %X, Read: %X\n", ite, ite, data);
                return -1;
            }

            if (ite%10000 == 0) {
                printf("%d\n", ite);
            }
        } else if ( !strcmp("rev_comp", mode) ) {
            // Write to registers
            rc = jtag_wr(0, reg_addr, loopcount-ite, 2);
            if ( rc ) {
                printf("write register 0x%llx with error code %d\n", reg_addr, rc);
                if ( stop_on_error )
                    return rc;
            }

            rc = jtag_rd(0, reg_addr, &data, 2);
            if ( rc ) {
                printf("read register 0x%llx with error code %d\n", reg_addr, rc);
                if ( stop_on_error )
                    return rc;
            }
            if (data != loopcount - ite) {
                printf("Error at iteration %d: Data mismatch at 0x6f240000. Expected: %llX, Read: %X\n", ite, loopcount - ite, data);
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
    printf("REG: 0x%llx; ite: %d\n", reg_addr, ite);
    //end = clock();
    end = rdtsc();
    cpu_time_used = ((double) (end - start)) * 1000.0 / cpu_freq;
    cpu_time_per_ite = cpu_time_used / loopcount;
    printf("Total time used to run test for cycles: %.4f ms\n", cpu_time_used);
    printf("OP Time per iteration: %.4f ms\n", cpu_time_per_ite);
    
    return 0;
}

int string_to_integer(const char *s) {
    // Check if the string starts with "0x" or "0X"
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
        return (int)strtol(s, NULL, 16); // Convert hexadecimal to integer
    } else {
        return (int)strtol(s, NULL, 10); // Convert decimal to integer
    }
}

int main(int argc, char *argv[])
{
    DWORD data = 0xdeadbeef;
    DWORD port = 0, mode, size, flag;
    ULONGLONG address;
    char  acc_mode[20];
    char asic_name[20];
    int rc;

    if ( argc < 2 ) {
        printf("Invalid command syntax\n");
        printf("jtag_accpcie rst <port(1 based)>\n");
        printf("jtag_accpcie ena <port(1 based)>\n");
        printf("jtag_accpcie rd <port(1 based)> <address>\n");
        printf("jtag_accpcie wr <port(1 based)> <address> <data>\n");
        printf("jtag_accpcie test <mode: rd/wr/comp/rev_comp> <port(1 based)> <address> <loopcount> <stop_on_error>\n");
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
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        address = (ULONGLONG)xtoi(argv[3]);
	data = (DWORD)xtoi(argv[4]);	
        rc = jtag_wr(0, address, data, 2);
        if ( rc ) {
            printf("ERROR: jtag write failed with error %x\n", rc);
            goto error_exit;
        }
        jtag_close();
    } else if ( !strcmp("rd", acc_mode) ) {
        if ( argc < 4 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        address = (ULONGLONG)xtoi(argv[3]);
        rc = jtag_rd(0, address, &data, 2);
        if ( rc ) {
            printf("ERROR: jtag read failed with error %x\n", rc);
            goto error_exit;
        }
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("wrdr", acc_mode) ) {
        DWORD tx_data[64] = {0x00, 0x00, 0x00};
        DWORD rx_data[64] = {0x00, 0x00, 0x00};
        int bits = 24;
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_wr_dr(tx_data, rx_data, bits);
        if ( rc ) {
            printf("ERROR: jtag read failed with error %x\n", rc);
            goto error_exit;
        }
        jtag_close();
    } else if ( !strcmp("wrir", acc_mode) ) {
        DWORD tx_data[64] = {0x00, 0x00, 0x00};
        int bits = 24;
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_wr_ir(tx_data, bits);
        if ( rc ) {
            printf("ERROR: jtag read failed with error %x\n", rc);
            goto error_exit;
        }
        jtag_close();
    } else if ( !strcmp("rst", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_reset(port);
        if ( rc ) {
            printf("ERROR: jtag reset failed with error %x\n", rc);
            goto error_exit;
        }
        jtag_close();
    } else if ( !strcmp("ena", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_enable(port);
        if ( rc ) {
            printf("ERROR: jtag enable failed with error %x\n", rc);
            goto error_exit;
        }
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
        jtag_clear(port);
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
        jtag_clear(port);
    } else if ( !strcmp("rdow", acc_mode) ) {
        if ( argc < 7 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        address = (ULONGLONG)xtoi(argv[3]);
        mode = (DWORD)xtoi(argv[4]);
        size = (DWORD)xtoi(argv[5]);
        flag = (DWORD)xtoi(argv[6]);    
        rc = jtag_ow_read(mode, size, address, &data, flag);
        if ( rc ) {
            printf("ERROR: jtag read one wire failed with error %x\n", rc);
            goto error_exit;
        }
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("wrow", acc_mode) ) {
        if ( argc < 8 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        address = (ULONGLONG)xtoi(argv[3]);
        mode = (DWORD)xtoi(argv[4]);
        size = (DWORD)xtoi(argv[5]);
        data = (DWORD)xtoi(argv[6]);    
        flag = (DWORD)xtoi(argv[7]);    
        rc = jtag_ow_write(mode, size, address, data, flag);
        if ( rc ) {
            printf("ERROR: jtag write one wire failed with error %x\n", rc);
            goto error_exit;
        }
        jtag_close();
    } else if ( !strcmp("set_asic", acc_mode) ) {
        if ( argc < 4 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        strcpy(asic_name, argv[3]);
        set_asic_target(asic_name);
        show_asic_target(asic_name);
        printf("asic are target is set for %s\n", asic_name);
        jtag_close();
    } else if ( !strcmp("show_asic", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        show_asic_target(asic_name);
        printf("asic are target is set for %s\n", asic_name);
        jtag_close();
    } else if ( !strcmp("clr", acc_mode) ) {
        if ( argc < 3 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }

        //port = (DWORD)xtoi(argv[2]);
        port = string_to_integer(argv[2]);

        printf("Clear port %d\n", port);
        jtag_clear(port);
    } else if ( !strcmp("test", acc_mode) ) {
        if (argc < 7) {
            printf("ERROR: Invalid command syntax for test\n");
            printf("Usage: jtag_accpcie test <mode> <port(1 based)> <reg_addr> <loopcount>\n");
            return -1;
        }

        char* mode = argv[2];
        port = (DWORD)xtoi(argv[3]);
        ULONGLONG reg_addr = (ULONGLONG)xtoi(argv[4]);
        ULONGLONG loopcount = (DWORD)xtoi(argv[5]);
        DWORD stop_on_error = (DWORD)xtoi(argv[6]);

        printf("jtag test register %d\n", port);
        printf("loopcount: %llx\n", loopcount);
       
        if (loopcount > 0xFFFFFFFF){
            printf("ERROR: The register can take a 32-bit value (0x00000000 – 0xFFFFFFFF)\n");
            return -1;
        }

        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag port %x init failed with error code %d\n", port, rc);
            goto error_exit;
        }

        rc = reg_perf_test(reg_addr, loopcount, mode, stop_on_error);
        if ( rc )
            printf("ERROR: perf test failed\n");
        jtag_close();

        return 0;
    } else {
        printf("Unsupported access mode\n");
        return -1;
    }

    return 0;

error_exit: 
    jtag_clear(port);
    return -1;
}
