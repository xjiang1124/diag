#ifndef UTIL_H
#define UTIL_H
#include <stdint.h>

#define  MEM_ACCESS_32  (1)
#define  MEM_ACCESS_64  (2)

int cpu_mem_read(uint32_t address, uint64_t * rd_data, uint32_t access_type);
int cpu_mem_write(uint32_t address, uint64_t data, uint32_t access_type);
#endif //#define UTIL_H
