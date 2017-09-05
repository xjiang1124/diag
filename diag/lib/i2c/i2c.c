#include <stdio.h>
#include "i2c.h"
#include "../../../include/diag.h"

//#define DPRINTF(f_, ...) {printf((f_), __VA_ARGS__); fflush(stdout);}

int I2cRead(int devAddr, int regAddr, int *value, int numBytes) {
    for(int i = 0; i < numBytes; i++) {
        value[i] = i+10;
        DPRINTF("%s: Dvalue=%u\n", __FUNCTION__, value[i]);
    }
}

int I2cWrite(int devAddr, int regAddr, int *value, int numBytes) {
    for(int i = 0; i < numBytes; i++) {
        printf("%s: value=%u\n", __FUNCTION__, value[i]);
    }
}
