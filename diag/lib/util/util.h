#ifndef UTIL_H
#define UTIL_H
#include <stdint.h>

#define  MEM_ACCESS_32  (1)
#define  MEM_ACCESS_64  (2)

int cpu_mmap(uint64_t *membase, int *fd, uint64_t address, uint32_t size);
int cpu_munmmap(uint64_t *membase, int *fd, uint32_t size);
int cpu_mem_read(uint64_t address, uint64_t * rd_data, uint32_t access_type);
int cpu_mem_write(uint64_t address, uint64_t data, uint32_t access_type);
#endif //#define UTIL_H
