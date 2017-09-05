#ifndef I2C_H
#define I2C_H

#include "../../../include/cxxType.h"
#include <iostream>
#include <string>

class CxxBase {
    private:

    public:
        typedef signed char int8;
        typedef unsigned char uint8;
        
        typedef signed short int16;
        typedef unsigned short uint16;
        
        typedef signed int int32;
        typedef unsigned int uint32;
        
        typedef signed long long int64;
        typedef unsigned long long uint64;

        // OutputMode 
        // 0: output to log file
        // 1: output to stdout
        int outputMode = 1;

        CxxBase(char *fileName);
        //CxxBase(string fileName);
        CxxBase();
};


class I2c : public CxxBase{
    public:
//        typedef unsigned int uint32;
        I2c();
        I2c(char *dspLog);
        //I2c(string dspLog);
        int Read(int devAddr, int regAddr, int *value, int numByte);
        int Write (int devAddr, int regAddr, int *value, int numByte);
        //int Write (int devAddr, int regAddr, long long *value, int numByte);
};

#endif //define I2C_H
