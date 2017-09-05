#include "i2c.h"
//#include <iostream>

using namespace std;

CxxBase::CxxBase() {
    printf("CxxBase const\n");
}

CxxBase::CxxBase(char* dspLog) {
//CxxBase::CxxBase(string dspLog) {
    //printf("CxxBase const: %s\n", dspLog);
}

I2c::I2c() {
    cout << "I2C obj init" << endl;
    printf("outputmode: %d\n", outputMode);
}

//I2c::I2c(string dspLog) {
I2c::I2c(char *dspLog) {
    printf("dspLog: %s\n", dspLog);
}

int I2c::Read (int devAddr, int regAddr, int *value, int numByte) {
    for (int i = 0; i < numByte; i++) {
        value[i] = i+1;
        cout << "devAddr " << devAddr << " regAddr " << regAddr << " value " << value[i] << " numByte " << numByte << endl << flush;
    }
    return 0;
}

int I2c::Write (int devAddr, int regAddr, int *value, int numByte) {
    for (int i = 0; i < numByte; i++) {
        cout << "devAddr " << devAddr << " regAddr " << regAddr << " value " << value[i] << " numByte " << numByte << endl << flush;
    }
    return 0;
}
