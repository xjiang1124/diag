#ifndef I2C_H
#define I2C_H

#include "../../include/cType.h"

int I2cRead(int devAddr, int regAddr, int* value, int numBytes);
int I2cWrite(int devAddr, int regAddr, int *value, int numBytes);

#endif //#define I2C_H
