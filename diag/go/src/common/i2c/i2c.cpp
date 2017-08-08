#include "i2c.h"
//#include <iostream>

using namespace std;

I2c::I2c(int v) {
    cout << "I2C obj init" << v << endl;
}

int I2c::Read (int devAddr, int regAddr, uint32 *value, int numByte) {
    for (int i = 0; i < numByte; i++) {
        value[i] = i+1;
        cout << "devAddr " << devAddr << " regAddr " << regAddr << " value " << value[i] << " numByte " << numByte << endl << flush;
    }
    return 0;
}

