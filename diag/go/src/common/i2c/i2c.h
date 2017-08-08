#ifndef I2C_H
#define I2C_H

#include "../../../include/cxxType.h"
#include <iostream>

class I2c
{
    public:
        typedef unsigned int uint32;
        I2c(int v);
        int Read(int devAddr, int regAddr, uint32 *value, int numByte);
};

#endif //define I2C_H
