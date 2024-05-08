#include "accpcie.h"
#include <time.h>

int main(int argc, char *argv[])
{
    DWORD data = 0xdeadbeef;
    DWORD port = 0;
    ULONGLONG address;
    char  acc_mode[20];

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
        set_bar((ULONGLONG)xtoi(argv[3]));
        set_verbosity(1);
        show_bar();
        set_verbosity(0);	
    } else if ( !strcmp("wr", acc_mode) ) {
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        address = (ULONGLONG)xtoi(argv[3]);
	data = (DWORD)xtoi(argv[4]);	
        jtag_wr(0, address, data, 2);
        jtag_close();
    } else if ( !strcmp("rd", acc_mode) ) {
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
	printf("jtag read %d\n", port);
        address = (ULONGLONG)xtoi(argv[3]);
        jtag_rd(0, address, &data, 2);
        printf("DATA READ = %x\n", data);
        jtag_close();
    } else if ( !strcmp("rst", acc_mode) ) {
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        jtag_reset(port);
        jtag_close();
    } else if ( !strcmp("ena", acc_mode) ) {
        port = (DWORD)xtoi(argv[2]);
        jtag_init(port);
        jtag_enable(port);
        jtag_close();
    } else if ( !strcmp("rg", acc_mode) ) {
	printf("jtag read register %d\n", port);
        address = (ULONGLONG)xtoi(argv[2]);
        jtag_rg(address, &data);
        printf("DATA READ = %x\n", data);
    } else if ( !strcmp("wg", acc_mode) ) {
	printf("jtag write register %d\n", port);
        address = (ULONGLONG)xtoi(argv[2]);
	data = (DWORD)xtoi(argv[3]);	
        jtag_wg(address, data);
    } else {
        printf("Unsupported access mode\n");
	return -1;
    }
    return 0;
}
