#include <stdio.h>
#include <stdlib.h>

#include "../../include/cType.h"
#include "../../lib/i2csim/i2csim.h"

// Cases:
// ./palutil r "VRM_CAPRI_DVDD" 0x88 2

void usage(void) {
    printf("palutil [r|w] dev_name offset numbytes\n");
    return;
}

int main(int argc, char *argv[]) {

    if (argc != 5) {
        printf("Invalie number of parameters\n");
        usage();
        return -1;
    }
    char rw = argv[1][0];
    char *devName = argv[2];
    //uint64 offset = atoi(argv[3]);
    uint64 offset = strtol(argv[3], NULL, 0);
    uint64 numbytes = atoi(argv[4]);

    printf("rw: %c; devName: %s; offset: %lld; numbytes: %lld\n", rw, devName, offset, numbytes);

    char * pData = (char*)calloc(numbytes, 0);
    pal_i2c_read(devName, offset, pData, numbytes);

    for (int i = 0; i < numbytes; i++) {
        printf("[%d] 0x%x\n", i, (unsigned char)(pData[i]));
    }

    free(pData);


    return 0;
}
