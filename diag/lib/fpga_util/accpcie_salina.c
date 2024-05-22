#include "accpcie.h"
#include <time.h>

#define WAIT_CNT 1000
int verbosity = 0;
int asic_index = 0;

ULONGLONG bar_addr = 0x10020300000;
FT_HANDLE ftHandle = 0;

FPGA_ASIC_TARGET fpga_asic_target[ ] = {
	/* asic name, nst size, top pos of address bit */
	{"elba", 256, 5},
	{"salina", 256, 15},
	{"", 0, 0}
};

DWORD gen_mask(int bits)
{
    int i;
    DWORD mask = 0x1, bit_mask = 0;

    for ( i = 0; i < bits; i++ ) {
        bit_mask |= mask;
	mask = mask << 1;
    }
    return bit_mask;
}

ULONGLONG xtoi(char *hexstring)
{
    ULONGLONG i = 0;

    if ( (*hexstring == '0') && (*(hexstring + 1) == 'x'))
        hexstring += 2;
    while ( *hexstring ) {
        char c = toupper(*hexstring++);
        if ( (c < '0') || (c > 'F') || ((c > '9') && (c < 'A')) )
            break;
        c -= '0';
        if ( c > 9 )
            c -= 7;
        i = (i << 4) + c;
    }
    return i;
}

void set_verbosity(int level)
{
    verbosity = level;
    return;
}

void set_target(char *asic_name)
{
    int i = 0;
    while ( strcpy(fpga_asic_target[i].name, "")  ) {
        if ( !strcmp(fpga_asic_target[i].name, asic_name) ) {
            asic_index = i;
            return;
        }
        i++;
    };
    printf("invalid asic name %s\n", asic_name);
    asic_index = -1;
    return;
}

void set_bar(ULONGLONG addr)
{
    bar_addr = addr;
    return;
}

ULONGLONG get_bar_from_proc(void)
{
    FILE *fileptr = fopen("/proc/bus/pci/devices", "r");
    char line[512];
    char delim[] = "\t";
    char *ptr = NULL;
    int len;
    unsigned long long int address = 0;

    if ( fileptr == NULL ) {
        printf("pcie device under proc cannot be opened\n");
        return address;
    }
    while ( fgets(line, sizeof(line), fileptr) ) {
        ptr = strtok(line, delim);
        while ( ptr != NULL ) {
           if ( strcmp(ptr, "1dd8000b") == 0 ) {
               ptr = strtok(NULL, delim);
               ptr = strtok(NULL, delim);
               len = strlen(ptr);
               ptr[len - 1] = '0';
               address = strtoll(ptr, NULL, 16);
               break;
           } else
               ptr = strtok(NULL, delim);
        }
        if ( address != 0 ) {
            if ( verbosity )
                printf("PCIE BAR = 0x%llx\n", address);
            fclose(fileptr);
            return address;
        }
    }
    fclose(fileptr);
    return address;
}

ULONGLONG show_bar(void)
{
    if ( verbosity != 0 )
        printf("FPGA PCIe BAR address = %llx\n", bar_addr);
    return bar_addr;
}

int read_fpga_mem32(ULONGLONG inst_offset, DWORD reg, DWORD *data)
{
    unsigned char *addr;

    off_t offset = bar_addr + inst_offset + reg;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;

    if ( verbosity == 2 ) {
        printf("read_fpag_mem32 with inst_offset %llx\n", inst_offset);
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    /* int fd = open("/sys/bus/pci/devices/0000:02:00.0/resource0", O_RDWR | O_SYNC); */
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }

    unsigned char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    /* unsigned char *mem = mmap((void *)bar_addr, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); */
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }

    /* addr = mem + inst_offset + reg; */
    addr = mem + page_offset;
    if ( verbosity == 2 ) {
        printf("allocated mem %llx; addr %llx\n", (ULONGLONG)mem, (ULONGLONG)addr);
    }

    /* addr = (DWORD *)(mem | (unsigned char *)ftHandle | (unsigned char *)reg); */
    *data = *((DWORD *)addr);

    munmap((void *)mem, 4096);
    close(fd);
    return FT_OK;
}

int write_fpga_mem32(ULONGLONG inst_offset, DWORD reg, ULONG value)
{
    unsigned char *addr;

    off_t offset = bar_addr + inst_offset + reg;
    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = (offset / pagesize) * pagesize;
    off_t page_offset = offset - page_base;
    
    if ( verbosity == 2 ) {
        printf("write_fpag_mem32 with inst_offset %llx\n", inst_offset);
        printf("page_size %lx; page_base %lx; offset %lx; page_offset %lx\n", pagesize, page_base, offset, page_offset);
    }
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    /* int fd = open("/sys/bus/pci/devices/0000:02:00.0/resource0", O_RDWR | O_SYNC); */
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }
    
    unsigned char *mem = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, page_base);
    /* unsigned char *mem = mmap((void *)bar_addr, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); */
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd); 
        return FT_ERROR_MAP_PCIE;
    }

    /* addr = mem + inst_offset + (ULONGLONG)reg; */
    addr = mem + page_offset;
    if ( verbosity == 2 ) {
        printf("allocated mem %llx; addr %llx\n", (ULONGLONG)mem, (ULONGLONG)addr);
    }
    *((DWORD *)addr) = (DWORD)value;

    munmap((void *)mem, 4096);
    close(fd); 
    return FT_OK;
}

FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;;
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst, upper_mask, msb_addr_pos;
    int wait_cnt = WAIT_CNT;
    int i;
    int rc = 0;

    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name\n");
        return -1;
    }

    msb_addr_pos = fpga_asic_target[asic_index].addr_msb_pos;
    upper_mask = gen_mask(msb_addr_pos);

    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 3)) | ((flag & 0x1) << (msb_addr_pos + 5)); 
    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }
    rc = write_fpga_mem32(ftHandle, J2C_0_TXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring data\n");
        return -1;
    }
 
    cmd = J2C_WRITE_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte write command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("write command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( verbosity == 2 )
        printf("FINISH WRITE\n");
    return ftStatus;
}

FT_STATUS jtag_wr_inc(DWORD inst, ULONGLONG address, DWORD data, DWORD flag, DWORD num_bits)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;;
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst, upper_mask, msb_addr_pos, bits_remain;
    int wait_cnt = WAIT_CNT;
    int i;
    int rc = 0;

    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name\n");
        return -1;
    }

    msb_addr_pos = fpga_asic_target[asic_index].addr_msb_pos;
    upper_mask = gen_mask(msb_addr_pos);

    rc = write_fpga_mem32(ftHandle, J2C_0_SIZE_REG, num_bits);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    bits_remain = num_bits;
    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 3)) | ((flag & 0x1) << (msb_addr_pos + 5)); 

    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    while ( bits_remain != 0 ) {
        rc = write_fpga_mem32(ftHandle, J2C_0_TXFIFO_REG, data);
        if ( rc ) {
            if ( verbosity )
                printf("failed to wring data\n");
            return -1;
        }
	if ( bits_remain >= 32 )
            bits_remain = bits_remain -32;
        else
            bits_remain = 0;
	data++;
    };

    cmd = J2C_WRITE_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte write command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("write command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( verbosity == 2 )
        printf("FINISH WRITE\n");
    return ftStatus;
}

FT_STATUS jtag_wg(ULONGLONG address, DWORD data)
{
    FT_STATUS ftStatus = FT_OK;
    int rc = 0;

    rc = write_fpga_mem32(address, 0, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write register\n");
        return -1;
    }
    return ftStatus;
}

FT_STATUS jtag_rg(ULONGLONG address, DWORD *data)
{
    FT_STATUS ftStatus = FT_OK;
    int rc = 0;

    rc = read_fpga_mem32(address, 0, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read register\n");
        return -1;
    }
    return ftStatus;
}

FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD cmd;
    DWORD resp;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
    DWORD dummy = inst, upper_mask, msb_addr_pos;
    int wait_cnt = WAIT_CNT;
    int i, rc = 0;
 
    inst = dummy;
    
    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name\n");
	return -1;
    }

    msb_addr_pos = fpga_asic_target[asic_index].addr_msb_pos;
    upper_mask = gen_mask(msb_addr_pos);

    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 3)) | ((flag & 0x1) << (msb_addr_pos + 5)); 
    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    cmd = J2C_READ_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte read command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("read command time out\n");
        return FT_RESP_TIMEOUT;
    }

    cmd = J2C_RESP_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write response command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("response command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( (resp & J2C_VALID_BIT) == 0 ) {
        if ( verbosity ) {
            printf("response value = %x\n", resp);
            printf("invalid response\n");
        }
        return FT_INVALID_RESP;
    } else if ( resp & J2C_ID_BIT ) {
        if ( verbosity )
            printf("invalid ID %x\n", resp);
        /* return FT_ERROR_ID; */
    } 
    rc = read_fpga_mem32(ftHandle, J2C_0_RXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read data\n");
        *data = 0xdeadbeef;
        return -1;
    }
    if ( verbosity == 2 )
        printf("FINISH READ\n");
    return ftStatus;
}

FT_STATUS jtag_rd_inc(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag, DWORD num_bits)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD cmd;
    DWORD resp;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
    DWORD dummy = inst, upper_mask, msb_addr_pos, bits_remain;
    int wait_cnt = WAIT_CNT;
    int i, rc = 0;
 
    inst = dummy;
    
    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name\n");
	return -1;
    }

    msb_addr_pos = fpga_asic_target[asic_index].addr_msb_pos;
    upper_mask = gen_mask(msb_addr_pos);

    rc = write_fpga_mem32(ftHandle, J2C_0_SIZE_REG, num_bits);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    bits_remain = num_bits;
    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 3)) | ((flag & 0x1) << (msb_addr_pos + 5)); 
    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    cmd = J2C_READ_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte read command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("read command time out\n");
        return FT_RESP_TIMEOUT;
    }

    cmd = J2C_RESP_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write response command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("response command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( (resp & J2C_VALID_BIT) == 0 ) {
        if ( verbosity ) {
            printf("response value = %x\n", resp);
            printf("invalid response\n");
        }
        return FT_INVALID_RESP;
    } else if ( resp & J2C_ID_BIT ) {
        if ( verbosity )
            printf("invalid ID %x\n", resp);
        /* return FT_ERROR_ID; */
    } 
    while ( bits_remain != 0 ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_RXFIFO_REG, data);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read data\n");
            *data = 0xdeadbeef;
            return -1;
        }
	if ( bits_remain >= 32 )
	    bits_remain = bits_remain - 32;
	else
	    bits_remain = 32;
	data++;
    }
    if ( verbosity == 2 )
        printf("FINISH READ\n");
    return ftStatus;
}

FT_STATUS jtag_init(DWORD portNum)
{
    time_t rawtime;
    struct tm *timeinfo;
    ULONGLONG j2c_mem_addr;
    ULONGLONG pcie_bar;
    DWORD magic;
    int rc;

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    pcie_bar = get_bar_from_proc();
    if ( pcie_bar != 0 ) {
        bar_addr = pcie_bar;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name\n");
	return -1;
    }

    j2c_mem_addr = (ULONGLONG)(J2C_0_OFFSET + (portNum - 1) * fpga_asic_target[asic_index].size);
    printf("05-16-2024 -- port number = 0x%x timeinfo %d:%d:%d\n", portNum, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
    printf("asic target is %s\n", fpga_asic_target[asic_index].name);
    printf("bar address is set with  0x%llx\n", bar_addr);
    write_fpga_mem32(j2c_mem_addr, J2C_0_SEM_REG, 0x1);
    read_fpga_mem32(j2c_mem_addr, J2C_0_SEM_REG, &magic);
    if ( magic == 0 ) {
        printf("j2c interface (port %d) is not locked\n", portNum - 1);
        return FT_ERROR_LOCKPORT;
    }
    printf("j2c interface (port %d) is locked for this process\n", portNum - 1);
    read_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, &magic);
    printf("magic number %x\n", magic);
    if ( magic != 0 ) {
        write_fpga_mem32(j2c_mem_addr, J2C_0_SEM_REG, 0);
        printf("jtag for this instance has been opened already!\n");
        return (FT_STATUS)magic;
    }
    ftHandle = (DWORD)j2c_mem_addr & 0xffffffff;
    rc = write_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, ftHandle);
    if ( rc ) {
        ftHandle = 0;
        write_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, ftHandle);
        write_fpga_mem32(j2c_mem_addr, J2C_0_SEM_REG, 0);
    }
    if ( verbosity == 2 )
        printf("FINISH INIT\n");
    return rc;
}

void jtag_close()
{
    if ( verbosity )
        printf("closing jtag\n");
    write_fpga_mem32(ftHandle, J2C_0_MAGIC_REG, 0);
    write_fpga_mem32(ftHandle, J2C_0_SEM_REG, 0);
    ftHandle = 0;
    return;
}

FT_STATUS jtag_reset(DWORD inst)
{
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst;

    int wait_cnt = WAIT_CNT;
    int i, rc = 0;

    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return FT_NO_HANDLE;
    }

    cmd = J2C_RESET_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write reset command\n");
        return FT_WRITE_FAILURE;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return FT_READ_FAILURE;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("reset command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( verbosity == 2 )
        printf("FINISH RESET\n");
    return FT_OK;
}

FT_STATUS jtag_enable(DWORD inst)
{
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst;
    int wait_cnt = WAIT_CNT;
    int i, rc = 0;

    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return FT_NO_HANDLE;
    }

    cmd = J2C_ENABLE_COMMAND;
    rc = write_fpga_mem32(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write enable command\n");
        return FT_WRITE_FAILURE;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read_fpga_mem32(ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return FT_READ_FAILURE;
        }
        if ( !(resp & 0x1) )
            break;
    }
    if ( resp & 0x1 ) {
        if ( verbosity )
            printf("enable command time out\n");
        return FT_RESP_TIMEOUT;
    }
    if ( verbosity == 2 )
        printf("FINISH ENABLE\n");
    return FT_OK;
}

/* Following routines are dummy function to be compatible with asic lib compilation */
FT_STATUS spi_reg_init(void)
{
    return FT_OK;
}

FT_STATUS spi_wr(BYTE address, BYTE data)
{
    BYTE dummy;

    dummy = address;
    dummy = data;
    data = dummy;

    return FT_OK;
}

FT_STATUS spi_rd(BYTE address, BYTE* data)
{
    BYTE dummy;

    dummy = address;
    dummy = *data;
    address = dummy;

    return FT_OK;
}

void ftHandle_close()
{
    return;
}

