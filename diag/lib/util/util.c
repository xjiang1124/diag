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
cpu_mmap(uint64_t *membase, int *fd, uint64_t address, uint32_t size)
{
    *fd = open("/dev/mem", O_RDWR|O_SYNC); 
    if (*fd < 0) {
        printf("ERROR %s: open /dev/memp failed.  Errno=%d : %s  ", __FUNCTION__, errno, strerror(errno)); 
        return(-1);
    }

    membase = (uint64_t * ) mmap(0, size, PROT_READ | PROT_WRITE, MAP_SHARED, *fd,  address);
    close(fd); 
    if (membase == MAP_FAILED) {
        printf("ERROR %s: MMAP failed.  Errno=%d  ", __FUNCTION__, errno); 
        close(*fd);
        return(errno);
    } 
    return(0);
}


int 
cpu_munmmap(uint64_t *membase, int *fd, uint32_t size)
{
    if (munmap((void*)membase, size)  < 0) {
        printf("ERROR %s: munmap failed.  Errno=%d %s  ", __FUNCTION__, errno, strerror(errno)); 
        close(*fd);
        return(errno);
    }
    close(*fd);
    return(0);
}


   
int 
cpu_mem_read(uint64_t address, uint64_t * rd_data, uint32_t access_type)
{
    volatile uint64_t *membase;
    int fd = 0;
    off_t offset;
    off_t phymem, diff;
    size_t pagesize = getpagesize();
    size_t pagemask = pagesize - 1;
    

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

    fd = open("/dev/mem", O_RDWR|O_SYNC);
    if (fd < 0) {
        printf("ERROR %s: open /dev/memp failed.  Errno=%d : %s  ", __FUNCTION__, errno, strerror(errno)); 
        return(-1);
    }

    phymem = address;
    diff = phymem - (phymem & (~pagemask));
    offset = phymem & (~pagemask);

    membase = (uint64_t * ) mmap(0, pagesize, PROT_READ | PROT_WRITE, MAP_SHARED, fd,  offset);
    close(fd);
    if (membase == MAP_FAILED) {
        printf("ERROR %s: MMAP failed.  Errno=%d  ", __FUNCTION__, errno); 
        close(fd);
        return(errno);
    } 
    if(access_type==MEM_ACCESS_32) {
        *rd_data = ((uint32_t *)membase)[diff/4];
    } else {
        *rd_data = ((uint64_t *)membase)[diff/8];
    }
    

    if (munmap((void*)membase, pagesize)  < 0) {
        printf("ERROR %s: munmap failed.  Errno=%d %s  ", __FUNCTION__, errno, strerror(errno)); 
        close(fd);
        return(errno);
    }
    close(fd);
    return(0);
}

int cpu_mem_write(uint64_t address, uint64_t data, uint32_t access_type)
{
    volatile uint64_t *membase;
    int fd = 0;
    off_t offset, phymem, diff;
    size_t pagesize = getpagesize();
    size_t pagemask = pagesize - 1;
    
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

    fd = open("/dev/mem", O_RDWR|O_SYNC);
    if (fd < 0) {
        printf("ERROR %s: open /dev/memp failed.  Errno=%d : %s  ", __FUNCTION__, errno, strerror(errno)); 
        return(-1);
    }


    phymem = address;
    diff = phymem - (phymem & (~pagemask));
    offset = phymem & (~pagemask);

    membase = (uint64_t * ) mmap(0, pagesize, PROT_READ | PROT_WRITE, MAP_SHARED, fd,  offset);
    close(fd);
    if (membase == MAP_FAILED) {
        printf("ERROR %s: mmap failed.  Errno=%d : %s  ", __FUNCTION__, errno, strerror(errno)); 
        close(fd);
        return(errno);
    }

    if(access_type==MEM_ACCESS_32){
        ((uint32_t *) membase)[diff/4] = data&0xFFFFFFFF;
    } else {
        ((uint64_t *) membase)[diff/8] = data;
    }

    if (munmap((void*)membase, pagesize)  < 0) {
        printf("ERROR %s: munmap failed.  Errno=%d : %s  ", __FUNCTION__, errno, strerror(errno)); 
        close(fd);
        return(errno);
    }

    close(fd);
    return(0);
}


