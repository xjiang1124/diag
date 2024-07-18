#include "accpcie.h"
#include <time.h>

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
    } else {
        printf("Unsupported access mode\n");
        return -1;
    }
    return 0;
}
