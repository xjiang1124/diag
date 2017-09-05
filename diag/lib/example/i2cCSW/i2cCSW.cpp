#include "i2cCSW.h"
#include <stdio.h>

int Read (int devAddr, int regAddr, int *value, int numBytes) {
    for (int i = 0; i < numBytes; i++) {
        value[i] = i+1;
        printf("%s: %d\n", __FUNCTION__, value[i]);
    }
    return 0;
}
