/*
 * Simulation code of pal_dev.c
 */

#include "../../include/cType.h"

uint64 pal_i2c_read(char* pDevName, uint64 offset, char *data, uint64 numBytes);

/*
 * When numByte == 0, work as PMBus send byte command
 */
uint64 pal_i2c_write(char* pDevName, uint64 offset, char *data, uint64 numBytes);


//=======================================
// SPI API - CPLD

// Is there maximum number of byte?
uint64 pal_spi_read(uint64 offset, char *data, uint64 numBytes);
uint64 pal_spi_write(uint64 offset, char *data, uint64 numBytes);


//=======================================
// QSPI API - QSPI flash

// Is there maximum number of byte?
uint64 pal_qspi_read(uint64 offset, char *data, uint64 numBytes);
uint64 pal_qspi_write(uint64 offset, char *data, uint64 numBytes);

