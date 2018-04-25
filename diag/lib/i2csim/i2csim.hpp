/*
 * Simulation code of pal_dev.c
 */

#include <string>

u_int64_t pal_i2c_read(string devName, u_int64_t offset, u_int8_t *data, u_int64_t numBytes);

/*
 * When numByte == 0, work as PMBus send byte command
 */
u_int64_t pal_i2c_write(string devName, u_int64_t offset, u_int8_t *data, u_int64_t numBytes);


//=======================================
// SPI API - CPLD

// Is there maximum number of byte?
u_int64_t pal_spi_read(u_int64_t offset, u_int8_t *data, u_int64_t numBytes);
u_int64_t pal_spi_write(u_int64_t offset, u_int8_t *data, u_int64_t numBytes);


//=======================================
// QSPI API - QSPI flash

// Is there maximum number of byte?
u_int64_t pal_qspi_read(u_int64_t offset, u_int8_t *data, u_int64_t numBytes);
u_int64_t pal_qspi_write(u_int64_t offset, u_int8_t *data, u_int64_t numBytes);

