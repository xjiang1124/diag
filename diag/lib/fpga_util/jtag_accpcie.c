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
    } else if ( !strcmp("wrdr32", acc_mode) ) {
        DWORD dr_rx_data; 
        DWORD dr_tx_data; 
        DWORD read_op;

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
        dr_tx_data = (DWORD)xtoi(argv[3]);
        read_op = (DWORD)xtoi(argv[4]);

        if ( read_op ) 
            rc = jtag_wr_dr(&dr_tx_data, &dr_rx_data, 32);
        else
            rc = jtag_wr_dr(&dr_tx_data, NULL, 32);
       
        if ( rc ) 
            printf("write dr error with return value is %x\n", rc);
        else {
            if ( read_op ) {
                printf("data back: %8.8x\n", dr_rx_data);
            }
        }
        jtag_close();
    } else if ( !strcmp("wrdr", acc_mode) ) {
        char filename[32];
        DWORD numBYTES, numDWORDS;
        DWORD *rxptr, *txptr;
        char *tmpptr;
        char hex_char[3];
        DWORD bitsize, read_op, i;
        FILE *fd;
 
        if ( argc < 6 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]); 

        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }

        strcpy(filename, argv[3]);
        bitsize = (DWORD)xtoi(argv[4]);
        read_op = (DWORD)xtoi(argv[5]);

        if ( (bitsize % 32) ) {
            numDWORDS = bitsize / 32 + 1;
        } else {
            numDWORDS = bitsize / 32;
        }
        if ( bitsize % 8 ) {
            numBYTES = bitsize / 8 + 1;
        } else {
            numBYTES = bitsize / 8;
        }

        fd = fopen(filename, "r");
        if ( fd == NULL ) {
            printf("failed to open file %s\n", filename);
            return 0;
        }

        txptr = (DWORD *)malloc(numDWORDS);
        memset(txptr, 0, numDWORDS * 4);
        tmpptr = (char *)txptr + numBYTES - 1;
        for ( i = 0; i < numBYTES; i++ ) {
            fread(hex_char, 2, 1, fd);
            hex_char[2] = 0;
            *tmpptr = atoi(hex_char);
            tmpptr--;
        }
        fclose(fd);

        if ( read_op ) 
            rxptr = (DWORD *)malloc(numDWORDS * 4);
        else
            rxptr = NULL;

        rc = jtag_wr_dr(txptr, rxptr, bitsize);
        free(txptr);
       
        if ( rc ) 
            printf("write dr error with return value is %x\n", rc);
        if ( rxptr != NULL && rc == 0 ) {
            for ( i = 0; i < numDWORDS + 1; i++ ) {
                printf("data back: \n");
                printf("    %8.8x", *rxptr);
                rxptr++;
                if ( (i % 8) == 0 )
                    printf("\n");
            }
        }
        free(rxptr);
        jtag_close();
    } else if ( !strcmp("ddrobs", acc_mode) ) {
        DWORD rx_data = 0xbeefdead;
        DWORD tx_data1 = 0x00000013;
        DWORD tx_data2 = 0x00000001;
        DWORD tx_data3 = 0x00000213;
        DWORD tx_data4 = 0x00000011;
        DWORD tx_data5 = 0x00002213;
        DWORD tx_data6 = 0x00001104;
        DWORD tx_data7 = 0x00220803;
        DWORD tx_data8 = 0x00022081;
        DWORD tx_data9 = 0x08820443;
        DWORD tx_data10[7] = {0x04000000, 0x01000200, 0x00800080, 0x00700000, 0x00000000, 0x08000000, 0x00022021};
        DWORD tx_data11 = 0x00000001;
        DWORD tx_data12 = 0x00000213;
        DWORD tx_data13 = 0x00000011;
        DWORD tx_data14 = 0x00002213;
        DWORD tx_data15 = 0x00001104;
        DWORD tx_data16 = 0x00220803;
        DWORD tx_data17 = 0x00022081;
        DWORD tx_data18 = 0x0882044C;

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

        rc = jtag_wr_ir(&tx_data1, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data2, NULL, 2);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data3, NULL, 11);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data4, NULL, 6);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data5, NULL, 15);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data6, NULL, 14);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data7, NULL, 23);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data8, NULL, 19);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data9, NULL, 29);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(tx_data10, NULL, 212);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data11, NULL, 2);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data12, NULL, 11);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data13, NULL, 6);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data14, NULL, 15);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data15, NULL, 14);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data16, NULL, 23);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data17, NULL, 19);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data18, NULL, 29);
        printf("write dr return value is %x\n", rc);

        printf("data back %x\n", rx_data);

        jtag_close();
    } else if ( !strcmp("wrir", acc_mode) ) {
        DWORD tx_data;
        DWORD bit_size;

        if ( argc < 5 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        tx_data = (DWORD)xtoi(argv[3]);
        bit_size = (DWORD)xtoi(argv[4]);

        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_wr_ir(&tx_data, bit_size);
        if ( rc ) {
            printf("ERROR: jtag wr ir failed with error %x\n", rc);
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
            /* goto error_exit; */
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
            /* goto error_exit; */
        }
        jtag_close();
    } else if ( !strcmp("jtagid", acc_mode) ) {
        DWORD rx_data;
        DWORD tx_ir_data1 = 0x00000003;
        DWORD tx_dr_data1 = 0x00000001;
        DWORD tx_ir_data2 = 0x00000002;
        DWORD tx_ir_data3 = 0x00000059;
        DWORD tx_dr_data2[3] = {0x00000000, 0x00000000, 0x00000000};
        DWORD tx_ir_data4 = 0x00000002;
        DWORD tx_ir_data5 = 0x0000001F;
        DWORD tx_dr_data3 = 0x00000000;
        DWORD tx_ir_data6 = 0x00000002;
        DWORD tx_dr_data4 = 0x00000000;
        DWORD tx_ir_data7 = 0x0000001F;
        DWORD tx_dr_data5 = 0x00000000;

        DWORD tx_ir_data8 = 0x00000002;
        DWORD tx_dr_data6 = 0x00000000;
        DWORD tx_dr_data7 = 0x00000000;
        DWORD tx_dr_data8 = 0x00000000;

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

        rc = jtag_wr_ir(&tx_ir_data1, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data1, NULL, 8);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data2, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data3, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(tx_dr_data2, NULL, 70);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data4, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data5, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data3, NULL, 32);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data6, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data4, NULL, 32);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_ir(&tx_ir_data7, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data5, &rx_data, 32);
        printf("write dr return value is %x\n", rc);

        printf("data back %x\n", rx_data);


        rc = jtag_wr_ir(&tx_ir_data8, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data6, NULL, 32);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_dr_data7, &rx_data, 32);
        printf("write dr return value is %x\n", rc);

        printf("data back %x\n", rx_data);

        rc = jtag_wr_dr(&tx_dr_data8, &rx_data, 32);
        printf("write dr return value is %x\n", rc);

        jtag_close();
    } else if ( !strcmp("ddrobs", acc_mode) ) {
        DWORD rx_data = 0xbeefdead;
        DWORD tx_data1 = 0x00000013;
        DWORD tx_data2 = 0x00000001;
        DWORD tx_data3 = 0x00000213;
        DWORD tx_data4 = 0x00000011;
        DWORD tx_data5 = 0x00002213;
        DWORD tx_data6 = 0x00001104;
        DWORD tx_data7 = 0x00220803;
        DWORD tx_data8 = 0x00022081;
        DWORD tx_data9 = 0x08820443;
        DWORD tx_data10[7] = {0x04000000, 0x01000200, 0x00800080, 0x00700000, 0x00000000, 0x08000000, 0x00022021};
        DWORD tx_data11 = 0x00000001;
        DWORD tx_data12 = 0x00000213;
        DWORD tx_data13 = 0x00000011;
        DWORD tx_data14 = 0x00002213;
        DWORD tx_data15 = 0x00001104;
        DWORD tx_data16 = 0x00220803;
        DWORD tx_data17 = 0x00022081;
        DWORD tx_data18 = 0x0882044C;

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

        rc = jtag_wr_ir(&tx_data1, 8);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data2, NULL, 2);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data3, NULL, 11);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data4, NULL, 6);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data5, NULL, 15);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data6, NULL, 14);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data7, NULL, 23);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data8, NULL, 19);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data9, NULL, 29);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(tx_data10, NULL, 212);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data11, NULL, 2);
        printf("write ir return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data12, NULL, 11);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data13, NULL, 6);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data14, NULL, 15);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data15, NULL, 14);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data16, NULL, 23);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data17, NULL, 19);
        printf("write dr return value is %x\n", rc);
        rc = jtag_wr_dr(&tx_data18, NULL, 29);
        printf("write dr return value is %x\n", rc);

        printf("data back %x\n", rx_data);

        jtag_close();
    } else if ( !strcmp("wrir", acc_mode) ) {
        DWORD tx_data;
        DWORD bit_size;

        if ( argc < 5 ) {
            printf("incorrect command syntax, missing parameters\n");
            return 0;
        }
        port = (DWORD)xtoi(argv[2]);
        tx_data = (DWORD)xtoi(argv[3]);
        bit_size = (DWORD)xtoi(argv[4]);

        rc = jtag_init(port);
        if ( rc ) {
            printf("ERROR: jtag_init failed with error %x\n", rc);
            goto error_exit;
        }
        rc = jtag_wr_ir(&tx_data, bit_size);
        if ( rc ) {
            printf("ERROR: jtag wr ir failed with error %x\n", rc);
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
