#include <stdio.h>
#include <stdint.h>

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include <errno.h>
#include <sys/stat.h>
#include <sys/mman.h>

#include "util.h"
#include "../../include/diag.h"


   
int 
cpu_mem_read(uint32_t address, uint64_t * rd_data, uint32_t access_type)
{
    volatile uint64_t *membase;
    int fd = open("/dev/mem", O_RDWR|O_SYNC); 
    off_t offset;
    uint32_t phymem, diff;
    size_t pagesize = getpagesize();
    size_t pagemask = pagesize - 1;
    
    printf("ADD DEBUG: %s", __FUNCTION__);    

    if(access_type==MEM_ACCESS_32) {
        if((address%4) != 0) {
            printf(" ERROR: %s: 32-bit Access type must mod by 4", __FUNCTION__);
            return(-1);
        }
    } else if(access_type==MEM_ACCESS_64) {
        if((address%8) != 0) {
            printf(" ERROR: %s: 64-bit Access type must mod by 8", __FUNCTION__);
            return(-1);
        }
    } else {
        printf(" ERROR: %s: Access type passed is not valid", __FUNCTION__);
        return(-1);
    }

    if (fd < 0) {
        perror("Open /dev/mem failed.. Error:");
        return(-1);
    }

    phymem = address;
    diff = phymem - (phymem & (~pagemask));
    offset = phymem & (~pagemask);

    membase = (uint64_t * ) mmap(0, pagesize, PROT_READ | PROT_WRITE, MAP_SHARED, fd,  offset);
    if (membase == MAP_FAILED) {
        perror("MMAP failed:  Error:");
        close(fd);
        return(-1);
    } 
    if(access_type==MEM_ACCESS_32) {
        *rd_data = ((uint32_t *)membase)[diff/4];
    } else {
        *rd_data = ((uint64_t *)membase)[diff/8];
    }
    
    close(fd);
    return(0);
}

int cpu_mem_write(uint32_t address, uint64_t data, uint32_t access_type)
{
    volatile uint64_t *membase;
    int fd = open("/dev/mem", O_RDWR|O_SYNC);
    off_t offset;
    uint32_t phymem, diff;
    size_t pagesize = getpagesize();
    size_t pagemask = pagesize - 1;
    
    printf("ADD DEBUG: %s", __FUNCTION__);

    if(access_type==MEM_ACCESS_32){
        if((address%4) != 0) {
            printf(" ERROR: %s: 32-bit Access type must mod by 4", __FUNCTION__);
            return(-1);
        }
    }
    else if(access_type==MEM_ACCESS_64){
        if((address%8) != 0) {
            printf(" ERROR: %s: 64-bit Access type must mod by 8", __FUNCTION__);
            return(-1);
        }
    }
    else{
        printf(" ERROR: %s: Access type passed is not valid", __FUNCTION__);
        return(-1);
    }

    if (fd < 0) {
        perror("Open /dev/mem failed.. Error:");
        return(-1);
    }

    phymem = address;
    diff = phymem - (phymem & (~pagemask));
    offset = phymem & (~pagemask);

    membase = (uint64_t * ) mmap(0, pagesize, PROT_READ | PROT_WRITE, MAP_SHARED, fd,  offset);
    if (membase == MAP_FAILED) {
        perror("MMAP Failed:  Error:");
        close(fd);
        return(-1);
    }

    if(access_type==MEM_ACCESS_32){
        ((uint32_t *) membase)[diff/4] = data&0xFFFFFFFF;
    } else {
        ((uint64_t *) membase)[diff/8] = data;
    }

    close(fd);
    return(0);
}


