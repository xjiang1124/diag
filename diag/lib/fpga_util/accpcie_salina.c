#include "accpcie.h"
#include <time.h>

#define WAIT_CNT 5000
int verbosity = 0;
int asic_index = 0;

ULONGLONG bar_addr = 0x10020300000;
FT_HANDLE ftHandle = 0;
int SPI_INIT_RETRY_CNT = 3;

FT_STATUS (*read32)(ULONGLONG inst_offset, DWORD reg, DWORD *data);
FT_STATUS (*write32)(ULONGLONG inst_offset, DWORD reg, ULONG value);

const BYTE SPIDATALENGTH = 11;  /* 3 digit command + 8 digit address */
/* const BYTE READ          = '\xC0'; */ /* 110xxxxx */
/* const BYTE WRITE         = '\xA0'; */ /* 101xxxxx */
const BYTE READ          = '\x0b'; /* 110xxxxx */
const BYTE WRITE         = '\x02'; /* 101xxxxx */
const BYTE WREN          = '\x98';//10011xxx
const BYTE ERAL          = '\x90';//10010xxx

//declare for BAD command
const BYTE AA_ECHO_CMD_1 = '\xAA';
const BYTE AB_ECHO_CMD_2 = '\xAB';
const BYTE BAD_COMMAND_RESPONSE = '\xFA';

//declare for MPSSE command
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_OUT               = '\x10';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_OUT              = '\x11';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_OUT                = '\x12';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_OUT               = '\x13';
const BYTE MSB_RISING_EDGE_CLOCK_BYTE_IN                = '\x20';
const BYTE MSB_RISING_EDGE_CLOCK_BIT_IN                 = '\x22';
const BYTE MSB_FALLING_EDGE_CLOCK_BYTE_IN               = '\x24';
const BYTE MSB_FALLING_EDGE_CLOCK_BIT_IN                = '\x26';
const BYTE MSB_RISING_FALLING_EDGE_CLOCK_BYTE_IN_OUT    = '\x31';
const BYTE MSB_RISING_FALLING_EDGE_CLOCK_BIT_IN_OUT     = '\x33';
const BYTE MSB_FALLING_RISING_EDGE_CLOCK_BYTE_IN_OUT    = '\x34';
const BYTE MSB_FALLING_RISING_EDGE_CLOCK_BIT_IN_OUT     = '\x36';

BYTE    OutputBuffer[512];
BYTE    InputBuffer[512];
DWORD   dwNumBytesToSend = 0;
DWORD   dwNumBytesSent = 0;
DWORD   dwNumBytesRead;

BYTE dis_clock[3] = { 0x8A, 0x97, 0x8D }; /* clock related setting, disable */
BYTE setup_spi[6] = { 0x80, 0x08, 0x0B, 0x86, 0x00, 0x00 };
BYTE dis_lpbk[1] = { 0x85 }; /* disable TDI/TDO loopback */
BYTE setup_reg[3] = { 0x80, 0x00, 0x0B }; /* TMS start high; TDO is input */
BYTE setClock[3] = { 0x86, 0x00, 0x00 }; /* TCK divisor: CLK = 6 MHz / (1 + 0004) == 1.2 MHz */

FPGA_ASIC_TARGET fpga_asic_target[ ] = {
	/* asic name, nst size, top pos of address bit */
	{"elba", 256, 5, 0},
	{"giglio", 256, 5, 0x1},
	{"salina", 256, 16, 0x2 },
	{"", 0, 0, 0}
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

void set_asic_target(char *asic_name)
{
    int reg_value;
    int rc;

    asic_index = 0;
    while ( strcmp(fpga_asic_target[asic_index].name, "")  ) {
        if ( !strcmp(fpga_asic_target[asic_index].name, asic_name) ) {
            break;
        }
        asic_index++;
    };
    rc = read32((ULONGLONG)ftHandle, J2C_0_CMD_REG, (DWORD *)&reg_value);
    if ( rc ) {
        printf("failed to read j2c command register %x\n", reg_value);
        return;
    }
    reg_value = reg_value & ~J2C_ASIC_TYPE_MASK;
    reg_value = reg_value & ~J2C_PRESCALE_MASK;
    reg_value |= asic_index << 8;
    reg_value |= J2C_WR_CONFIG_CMD;
    reg_value |= J2C_PRESCALE_CONF;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, reg_value);
    if ( rc ) {
        printf("failed to set j2c connfig\n");
        return;
    }
    /*
    reg_value &= ~J2C_WR_CONFIG_CMD;
    reg_value |= J2C_RESET_CMD;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, reg_value);
    if ( rc ) {
        printf("failed to reset j2c logic\n");
    }
    */
    return;
}

void show_asic_target(char *asic_name)
{
    int reg_value;
    int rc;

    rc = read32((ULONGLONG)ftHandle, J2C_0_CMD_REG, (DWORD *)&reg_value);
    if ( rc ) {
        printf("failed to read j2c command register %x\n", reg_value);
        return;
    }
    reg_value = reg_value & J2C_ASIC_TYPE_MASK;
    reg_value = reg_value >> 8;

    if ( reg_value != asic_index )
        printf("WARNING: asic type register value is different from driver setting\n");
    strcpy(asic_name, fpga_asic_target[reg_value].name);
    return;
}

void update_asic_target(void)
{
    DWORD reg_value;
    int rc;

    rc = read32((ULONGLONG)ftHandle, J2C_0_CMD_REG, &reg_value);
    if ( rc ) {
        printf("failed to read j2c command register %x\n", reg_value);
        return;
    }
    reg_value = reg_value & ~(J2C_ASIC_TYPE_MASK | J2C_PRESCALE_MASK);
    reg_value = reg_value | J2C_ASIC_TYPE_SALINA | J2C_PRESCALE_CONF | J2C_WR_CONFIG_CMD;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, reg_value);
    if ( rc ) {
        printf("failed to write j2c command register %x\n", reg_value);
        return;
    }
    reg_value = reg_value & J2C_ASIC_TYPE_MASK;
    reg_value = reg_value >> 8;
    asic_index = reg_value;

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

FT_STATUS read_fpga_mem32(ULONGLONG inst_offset, DWORD reg, DWORD *data)
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

FT_STATUS write_fpga_mem32(ULONGLONG inst_offset, DWORD reg, ULONG value)
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

FT_STATUS spi_rd(ULONGLONG inst_offset, DWORD address, DWORD * data)
{
    FT_STATUS ftStatus = FT_OK;
    dwNumBytesToSend = 0;
    int rcv_data = 0;
    int swp_data = 0;
    ULONGLONG dummy;

    dummy = inst_offset;
    inst_offset = dummy;

    queue_clear();
    spi_csdis();

    //send WRITE command
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
    OutputBuffer[dwNumBytesToSend++] = 7;
    OutputBuffer[dwNumBytesToSend++] = READ;

    //send address
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
    OutputBuffer[dwNumBytesToSend++] = 7;
    OutputBuffer[dwNumBytesToSend++] = (BYTE)(address & 0xFF);

    //dummy byte
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
    OutputBuffer[dwNumBytesToSend++] = 7;
    OutputBuffer[dwNumBytesToSend++] = 0;

    //read data
    OutputBuffer[dwNumBytesToSend++] = MSB_RISING_EDGE_CLOCK_BYTE_IN;
    //Data length of 0x0003 means 4 byte data to clock in
    OutputBuffer[dwNumBytesToSend++] = 0x3; //'\x01';
    OutputBuffer[dwNumBytesToSend++] = 0x0; //'\x00';

    spi_csena();
    ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    dwNumBytesToSend = 0;

    usleep(1500);
    ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
    if ( dwNumBytesSent != 4 ) {
        printf("SPI queue %d bytes, retry\n", dwNumBytesSent);
        usleep(500);
        ftStatus = FT_GetQueueStatus(ftHandle, &dwNumBytesSent);
        if ( dwNumBytesSent != 4 ) {
            printf("SPI queue %d bytes, failed\n", dwNumBytesSent);
        } else
            ftStatus = FT_Read(ftHandle, &rcv_data, dwNumBytesSent, &dwNumBytesRead);
    } else {
        //send out MPSSE command to MPSSE engine
        ftStatus = FT_Read(ftHandle, &rcv_data, dwNumBytesSent, &dwNumBytesRead);
        if ( !dwNumBytesSent || !dwNumBytesRead )
            ftStatus |= 0x80;
    }

    /* revert the byte order */
    swp_data = (rcv_data & 0x000000ff) << 24;
    swp_data |= (rcv_data & 0x0000ff00) << 8;
    swp_data |= (rcv_data & 0x00ff0000) >> 8;
    swp_data |= (rcv_data & 0xff000000) >> 24;
    *data = (DWORD)swp_data;

    return ftStatus;
}

FT_STATUS spi_wr(ULONGLONG inst_offset, DWORD address, DWORD data)
{
    FT_STATUS ftStatus = FT_OK;
    ULONGLONG dummy;

    dummy = inst_offset;
    inst_offset = dummy;

    dwNumBytesSent = 0;
    dwNumBytesToSend = 0;
    queue_clear();
    spi_csdis();

    /* send WRITE command */
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
    OutputBuffer[dwNumBytesToSend++] = 7;
    OutputBuffer[dwNumBytesToSend++] = WRITE;

    /* send address */
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BIT_OUT;
    OutputBuffer[dwNumBytesToSend++] = 7;
    OutputBuffer[dwNumBytesToSend++] = address & 0xFF;

    /* send data */
    OutputBuffer[dwNumBytesToSend++] = MSB_FALLING_EDGE_CLOCK_BYTE_OUT;
    /* Data length of 0x0000 means 1 byte data to clock out */
    OutputBuffer[dwNumBytesToSend++] = 0x03;
    OutputBuffer[dwNumBytesToSend++] = 0x00;
    /* output high byte first */
    OutputBuffer[dwNumBytesToSend++] = (data >> 24) & 0xFF;
    OutputBuffer[dwNumBytesToSend++] = (data >> 16) & 0xFF;
    OutputBuffer[dwNumBytesToSend++] = (data >> 8) & 0xFF;
    OutputBuffer[dwNumBytesToSend++] = data & 0xff;

    spi_csena();

    /* send out MPSSE command to MPSSE engine */
    ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);

    /* Clear output buffer */
    dwNumBytesToSend = 0;

    return ftStatus;
}

FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;;
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst, upper_mask, msb_addr_pos;
    int wait_cnt = WAIT_CNT;
    int i, j;
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

    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 8)) | ((flag & 0x1) << (msb_addr_pos + 10)); 
    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, J2C_0_TXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring data\n");
        return -1;
    }
 
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        return FT_CMD_NOT_READY;
    }
    cmd = J2C_WRITE_COMMAND;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte write command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        return FT_CMD_NOT_READY;
    }
    if ( verbosity > 3 )
        printf("finishing write command\n");
    usleep(2); 
    for ( j = 0; j < 30; j++ ) {
        for ( i = 0; i < wait_cnt; i++ ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
            if ( rc ) {
                if ( verbosity )
                    printf("failed to read response\n");
                return -1;
            }
	    if ( verbosity > 3 )
	        printf("status register value before send response %x\n", resp);
            if ( !(resp & 0x1) )
                break;
        }
        if ( resp & 0x1 ) {
	    if ( verbosity > 3 )
                printf("response command time out\n");
            return FT_RESP_TIMEOUT;
        }
        cmd = J2C_RESP_COMMAND;
        if ( verbosity > 3 )
	    printf("sending resp command\n");
        rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
        if ( rc ) {
            if ( verbosity )
                printf("failed to write response command\n");
            return -1;
        }
        usleep(2);
        for ( i = 0; i < wait_cnt; i++ ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
            return FT_CMD_NOT_READY;
        }
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read response\n");
            return -1;
        }
        if ( resp & J2C_VALID_BIT ) {
            if ( verbosity > 3 )
                printf("valid bit is set %x\n", resp);
            break;
        }
    }

    if ( j == 30 ) {
        if ( verbosity > 3 )
            printf("retry response for write exceed 30 times\n");
        ftStatus = FT_INVALID_RESP;
    }
    if ( verbosity == 2 )
        printf("FINISH WRITE\n");
    return ftStatus;
}

FT_STATUS jtag_wr_dr(DWORD *tx_data, DWORD *rx_data, DWORD num_bits)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD j2c_status, rxdata;
    DWORD bits_remain;
    DWORD *txptr, *rxptr;
    int rc = 0, i;
    int wait_cnt = WAIT_CNT;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_asic_target with a valid asic name\n");
        return -1;
    }

    txptr = tx_data;
    rxptr = rx_data;
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to read status register\n");
            return -1;
        }
        if ( !(j2c_status & J2C_BUSY) )
            break;
    }
    if ( j2c_status & J2C_BUSY ) {
        if ( verbosity ) 
            printf("j2c interface is busy %x\n", j2c_status);
        return FT_CMD_NOT_READY;
    }        

    bits_remain = num_bits;
    while ( bits_remain != 0 ) {
        if ( (j2c_status & J2C_TXFIFO_FULL) == 0 ) {
            rc = write32((ULONGLONG)ftHandle, J2C_0_TXFIFO_REG, *txptr);
            if ( rc ) {
                if ( verbosity )
                    printf("failed to write txfifo\n");
                return -1;
            }
	    if ( bits_remain >= 32 )
                bits_remain = bits_remain - 32;
            else
                bits_remain = 0;
            txptr++;
        }
    };
    rc = write32((ULONGLONG)ftHandle, J2C_0_SIZE_REG, num_bits);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write size register\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, J2C_WR_DR_COMMAND);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write command register\n");
        return -1;
    }

    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to read status register\n");
            return -1;
        }
        if ( !(j2c_status & J2C_BUSY) )
            break;
    }

    if ( j2c_status & J2C_BUSY ) {
        if ( verbosity )
            printf("write command time out\n");
        return FT_RESP_TIMEOUT;
    }

    if ( rxptr == NULL ) {
        i = 0;
        while ( !(j2c_status & J2C_RXFIFO_EMPTY) ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_RXFIFO_REG, &rxdata); 
            if ( rc ) {
                if ( verbosity )
                    printf("failed to rx fifo\n");
                return -1;
            }
            i++;
            if ( i > 4096 ) {
                printf("clear rxfifo exceed 4096 read\n");
                break;
            }
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
            if ( rc ) {
                if ( verbosity )
                    printf("failed to read status register\n");
                return -1;
            }
        }
        return FT_OK;
    }

    bits_remain = num_bits;
    while ( bits_remain != 0 ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to read status register\n");
            return -1;
        }
        i = 0;
        while ( !(j2c_status & J2C_RXFIFO_EMPTY) ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
            if ( rc ) {
                if ( verbosity )
                    printf("failed to read status register\n");
                return -1;
            }
            i++;
            if ( i > WAIT_CNT ) {
                if ( verbosity )
                    printf("RXFIOF is unexpected empty\n");
                return FT_SHORT_RESPONSE;
            } 
        }
        rc = read32((ULONGLONG)ftHandle, J2C_0_RXFIFO_REG, &rxdata); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to rx fifo\n");
            return -1;
        }
	if ( bits_remain >= 32 ) {
            *rxptr++ = rxdata;
            bits_remain = bits_remain - 32;
        } else {
            *rxptr++ = rxdata >> (32 - bits_remain);
            bits_remain = 0;
        }
    };

    if ( verbosity > 2 )
        printf("FINISH DR command\n");
    return ftStatus;
}

FT_STATUS jtag_wr_ir(DWORD *tx_data, DWORD num_bits)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD j2c_status;
    DWORD bits_remain;
    DWORD *txptr;
    DWORD rxdata;
    int rc = 0, i;
    int wait_cnt = WAIT_CNT;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_asic_target with a valid asic name\n");
        return -1;
    }

    bits_remain = num_bits;
    txptr = tx_data;
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to read status register\n");
            return -1;
        }
        if ( !(j2c_status & J2C_BUSY) )
            break;
    }
    if ( j2c_status & J2C_BUSY ) {
        if ( verbosity ) 
            printf("j2c interface is busy %x\n", j2c_status);
        return FT_CMD_NOT_READY;
    }        

    while ( bits_remain != 0 ) {
        if ( (j2c_status & J2C_TXFIFO_FULL) == 0 ) {
            rc = write32((ULONGLONG)ftHandle, J2C_0_TXFIFO_REG, *txptr);
            if ( rc ) {
                if ( verbosity )
                    printf("failed to write txfifo\n");
                return -1;
            }
            if ( bits_remain >= 32 )
                bits_remain = bits_remain - 32;
            else
                bits_remain = 0;
            txptr++;
        }
    };
    rc = write32((ULONGLONG)ftHandle, J2C_0_SIZE_REG, num_bits);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write size register\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, J2C_WR_IR_COMMAND);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write command register\n");
        return -1;
    }

    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
        if ( rc ) {
            if ( verbosity )
                printf("failed to read status register\n");
            return -1;
        }
        if ( !(j2c_status & J2C_BUSY) )
            break;
    }

    if ( j2c_status & J2C_BUSY ) {
        if ( verbosity )
            printf("write command time out\n");
        return FT_RESP_TIMEOUT;
    }
    i = 0;
    while ( !(j2c_status & J2C_RXFIFO_EMPTY) ) {
       rc = read32((ULONGLONG)ftHandle, J2C_0_RXFIFO_REG, &rxdata); 
       if ( rc ) {
           if ( verbosity )
               printf("failed to rx fifo\n");
           return -1;
       }
       i++;
       if ( i > 4096 ) {
           printf("clear rxfifo exceed 4096 read\n");
           break;
       }
       rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &j2c_status); 
       if ( rc ) {
           if ( verbosity )
               printf("failed to read status register\n");
           return -1;
       }
    }
    if ( verbosity > 2 )
        printf("FINISH DR command\n");
    return ftStatus;
}

FT_STATUS jtag_ow_write(DWORD mode, DWORD size, ULONGLONG address, DWORD data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    int rc = 0;
    DWORD cmd, response;
    int wait_cnt = WAIT_CNT;

    rc = write32((ULONGLONG)ftHandle, OW_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW lower address\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, OW_0_ADDR1_REG, (address >> 32) & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW higher address\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, OW_0_DATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW date register\n");
        return -1;
    }

    cmd = J2C_OW_WRITE_CMD | ((mode & 0x1) << 3) | (size & 0x3) | ((flag & J2C_OW_SECURE_MASK) << J2C_OW_SECURE_SHIFT);
    while ( wait_cnt != 0 ) {
        rc = read32((ULONGLONG)ftHandle, OW_0_STAT_REG, &response);
        if ( rc ) {
            if ( verbosity )
                printf("ERROR: reading OW response register\n");
            return -1;
        }
        if ( response & J2C_OW_DRDY )
            break;
        wait_cnt--;
        usleep(10);
    }
    if ( wait_cnt == 0 ) {
        if ( verbosity )
            printf("ERROR: OW write not ready\n");
        ftStatus = FT_CMD_NOT_READY;
        return ftStatus;
    }
    wait_cnt = WAIT_CNT;
    rc = write32((ULONGLONG)ftHandle, OW_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW command register\n");
        return -1;
    }
    while ( wait_cnt != 0 ) {
        rc = read32((ULONGLONG)ftHandle, OW_0_STAT_REG, &response);
        if ( rc ) {
            if ( verbosity )
                printf("ERROR: reading OW response register\n");
            return -1;
        }
        if ( response & J2C_OW_DRDY )
            break;
        wait_cnt--;
        usleep(10);
    }
    if ( wait_cnt == 0 ) {
        if ( verbosity )
            printf("ERROR: OW write timeout\n");
        ftStatus = FT_WRITE_FAILURE;
        return ftStatus;
    }
    if ( response & J2C_OW_RESP_ERROR ) {
        if ( verbosity )
            printf("ERROR: OW write with errors %x\n", response);
        ftStatus = FT_RESP_ERROR;
    }
    return ftStatus;
}

FT_STATUS jtag_ow_read(DWORD mode, DWORD size, ULONGLONG address, DWORD *data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    int rc = 0;
    DWORD cmd, response;
    int wait_cnt = WAIT_CNT;

    rc = write32((ULONGLONG)ftHandle, OW_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW lower address\n");
        return -1;
    }
    rc = write32((ULONGLONG)ftHandle, OW_0_ADDR1_REG, (address >> 32) & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW higher address\n");
        return -1;
    }

    cmd = J2C_OW_READ_CMD | ((mode & 0x1) << 3) | (size & 0x3) | ((flag & J2C_OW_SECURE_MASK) << J2C_OW_SECURE_SHIFT);
    while ( wait_cnt != 0 ) {
        rc = read32((ULONGLONG)ftHandle, OW_0_STAT_REG, &response);
        if ( rc ) {
            if ( verbosity )
                printf("ERROR: reading OW response register\n");
            return -1;
        }
        if ( response & J2C_OW_DRDY )
            break;
        wait_cnt--;
        usleep(10);
    }
    if ( wait_cnt == 0 ) {
        if ( verbosity )
            printf("ERROR: OW read not ready\n");
        ftStatus = FT_CMD_NOT_READY;
        return ftStatus;
    }
    wait_cnt = WAIT_CNT;
    rc = write32((ULONGLONG)ftHandle, OW_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: writing OW command register\n");
        return -1;
    }
    while ( wait_cnt != 0 ) {
        rc = read32((ULONGLONG)ftHandle, OW_0_STAT_REG, &response);
        if ( rc ) {
            if ( verbosity )
                printf("ERROR: reading OW response register\n");
            return -1;
        }
        if ( response & J2C_OW_DRDY )
            break;
        wait_cnt--;
        usleep(10);
    }
    if ( wait_cnt == 0 ) {
        if ( verbosity )
            printf("ERROR: OW read timeout\n");
        ftStatus = FT_READ_FAILURE;
        return ftStatus;
    }
    if ( response & J2C_OW_RESP_ERROR ) {
        if ( verbosity )
            printf("ERROR: OW write with errors %x\n", response);
        ftStatus = FT_RESP_ERROR;
    }
    rc = read32((ULONGLONG)ftHandle, OW_0_DATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("ERROR: reading OW date register\n");
        return -1;
    }
    return ftStatus;
}

FT_STATUS jtag_wg(ULONGLONG address, DWORD data)
{
    FT_STATUS ftStatus = FT_OK;
    int rc = 0;

    rc = write32(0, (ULONGLONG)address, data);
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

    rc = read32(0, (ULONGLONG)address, data);
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
    int i, j, rc = 0;
 
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

    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 8)) | ((flag & 0x1) << (msb_addr_pos + 10)); 
    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        return FT_CMD_NOT_READY;
    }
    cmd = J2C_READ_COMMAND;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte read command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        /* return FT_RESP_TIMEOUT; */
    }
    usleep(2);
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        return FT_CMD_NOT_READY;
    }
    for ( j = 0; j < 30; j++ ) {
        cmd = J2C_RESP_COMMAND;
	if ( verbosity > 3 )
            printf("send resp command %d time\n", j + 1);
        rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
        if ( rc ) {
            if ( verbosity )
                printf("failed to write response command\n");
            return -1;
        }
        for ( i = 0; i < wait_cnt; i++ ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
            /* return FT_RESP_TIMEOUT; */
        }
        usleep(2); 
        for ( i = 0; i < wait_cnt; i++ ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
            return FT_CMD_NOT_READY; 
        }
        for ( i = 0; i < wait_cnt; i++ ) {
            rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
            if ( rc ) {
                if ( verbosity )
                    printf("failed to read response\n");
                return -1;
            }
            if ( resp & J2C_VALID_BIT )
                break;
        }
        if ( (resp & J2C_VALID_BIT) == 0 ) {
            if ( verbosity ) {
                printf("response value = %x\n", resp);
                printf("invalid response\n");
            }
            continue;
        }
        break;
    }

    if ( j == 30 ) {
        if ( verbosity )
            printf("ERROR: J2C doesn't repy valid bit with 30 retries\n");
        return FT_INVALID_RESP;
    }
    if ( resp & J2C_ID_BIT ) {
        if ( verbosity )
            printf("invalid ID %x\n", resp);
        return FT_ERROR_ID; 
    } 
    rc = read32((ULONGLONG)ftHandle, J2C_0_RXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read data\n");
        *data = 0xbeefdead;
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

    rc = write32((ULONGLONG)ftHandle, J2C_0_SIZE_REG, num_bits);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    bits_remain = num_bits;
    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & upper_mask) | (size << (msb_addr_pos + 8)) | ((flag & 0x1) << (msb_addr_pos + 10)); 
    rc = write32((ULONGLONG)ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    cmd = J2C_READ_COMMAND;
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte read command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write response command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
        rc = read32((ULONGLONG)ftHandle, J2C_0_RXFIFO_REG, data);
        if ( rc ) {
            if ( verbosity )
                printf("failed to read data\n");
            *data = 0xabcdabcd;
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
    FT_STATUS rc;
    int i;

    time(&rawtime);
    timeinfo = localtime(&rawtime);
    printf("08-05-2024 -- port number = 0x%x timeinfo %d:%d:%d\n", portNum, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);

    if ( portNum & 0x100 ) {
        printf("API is using dongle implementation to access asic j2c port\n");
        read32 = spi_rd;
        write32 = spi_wr;
        for ( i = 0; i < SPI_INIT_RETRY_CNT; i++ ) {
            rc = spi_init((portNum >> 8) & 0x1);
            if ( rc == FT_OK )
               break;
        }
    } else {
        printf("API is using fpga implementation to access asic j2c port\n");
        read32 = read_fpga_mem32;
        write32 = write_fpga_mem32;
        rc = fpga_j2c_init(portNum & 0x7F);
    }
    update_asic_target();
    if ( asic_index == -1 ) {
        printf("Invalid asic type. Please use set_target with a valid asic name before use\n");
    }

    printf("asic target is %s\n", fpga_asic_target[asic_index].name);
    if ( portNum & 0x80 )
        rc |= jtag_ow_init();
    return rc;
}

FT_STATUS jtag_ow_init(void) {
    FT_STATUS rc;
    int wait_cnt = WAIT_CNT;
    DWORD response;

    rc = write32((ULONGLONG)ftHandle, OW_0_INIT_REG, J2C_OW_INIT);
    if ( rc ) {
        if ( verbosity == 1 )
            printf("ERROR: failed writing ow init register\n");
        return -1;
    }
    while ( wait_cnt != 0 ) {
        rc = read32((ULONGLONG)ftHandle, OW_0_STAT_REG, &response);
        if ( rc ) {
            if ( verbosity )
                printf("ERROR: reading OW response register\n");
            return -1;
        }
        if ( response & J2C_OW_INIT_DONE )
            break;
        wait_cnt--;
        usleep(10);
    }
    if ( wait_cnt == 0 ) {
        if ( verbosity )
            printf("ERROR: failed initializing ow interface\n");
        return FT_INIT_FAILURE;
    }
    return FT_OK;
}

FT_STATUS fpga_j2c_init(DWORD portNum)
{
    ULONGLONG j2c_mem_addr;
    ULONGLONG pcie_bar;
    DWORD magic;
    FT_STATUS rc;

    pcie_bar = get_bar_from_proc();
    if ( pcie_bar != 0 ) {
        bar_addr = pcie_bar;
    }

    j2c_mem_addr = (ULONGLONG)(J2C_0_OFFSET + (portNum - 1) * fpga_asic_target[asic_index].size);
    printf("bar address is set with  0x%llx\n", bar_addr);
    write32(j2c_mem_addr, J2C_0_SEM_REG, 0x1);
    read32(j2c_mem_addr, J2C_0_SEM_REG, &magic);
    if ( magic == 0 ) {
        printf("j2c interface (port %d) is not locked\n", portNum - 1);
        return FT_ERROR_LOCKPORT;
    }
    printf("j2c interface (port %d) is locked for this process\n", portNum - 1);
    read32(j2c_mem_addr, J2C_0_MAGIC_REG, &magic);
    printf("magic number %x\n", magic);
    if ( magic != 0 ) {
        write32(j2c_mem_addr, J2C_0_SEM_REG, 0);
        printf("jtag for this instance has been opened already!\n");
        return (FT_STATUS)magic;
    }
    ftHandle = (PVOID)(j2c_mem_addr & 0xffffffff);
    rc = write32(j2c_mem_addr, J2C_0_MAGIC_REG, (ULONG)(ULONGLONG)ftHandle);
    if ( rc ) {
        ftHandle = 0;
        write32(j2c_mem_addr, J2C_0_MAGIC_REG, (ULONG)(ULONGLONG)ftHandle);
        write32(j2c_mem_addr, J2C_0_SEM_REG, 0);
    }
    if ( verbosity == 2 )
        printf("FINISH INIT\n");
    return rc;
}

FT_STATUS spi_init(DWORD portNum)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD driverVersion = 0;
    DWORD dwNumInputBuffer;
    BOOL bCommandEchod = FALSE;
    DWORD dwCount;

    if ( ftHandle == NULL)
        ftStatus = FT_Open(portNum & 0x1, &ftHandle);
    if ( ftStatus != FT_OK ) {
        printf("FT_Open failed, with error %d.\n", (int)ftStatus);
        printf("On Linux, lsmod can check if ftdi_sio (and usbserial) are present.\n");
        printf("If so, unload them using rmmod, as they conflict with ftd2xx.\n");
        return ftStatus;
    }

    assert(ftHandle != NULL);

    ftStatus = FT_GetDriverVersion(ftHandle, &driverVersion);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_GetDriverVersion returned %d.\n", (int)ftStatus);
        return ftStatus;
    }

    if ( verbosity ) {
        printf("D2XX version : %x.%x.%x\n",
               (unsigned int)((driverVersion & 0x00FF0000) >> 16),
               (unsigned int)((driverVersion & 0x0000FF00) >> 8),
               (unsigned int)(driverVersion & 0x000000FF));
    }

    ftStatus = FT_ResetDevice(ftHandle);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_ResetDevice returned %d.\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_GetQueueStatus(ftHandle, &dwNumInputBuffer);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_GETQueueStatus returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    if ( dwNumInputBuffer > 0 ) {
        ftStatus = FT_Read(ftHandle, InputBuffer, dwNumInputBuffer, &dwNumBytesRead);
        if ( ftStatus != FT_OK ) {
            printf("Failure. FT_Read - clear buffer returned %d\n", (int)ftStatus);
            return ftStatus;
       }
    }

    ftStatus = FT_SetUSBParameters(ftHandle, 65535, 65535);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetUSBParameters returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetChars(ftHandle, FALSE, 0, FALSE, 0);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetChars returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetTimeouts(ftHandle, 3000, 3000);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetTimeouts returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetLatencyTimer(ftHandle, 1);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetLatencyTimer returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_RESET);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetBitMode Reset returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = FT_SetBitMode(ftHandle, 0x00, FT_BITMODE_MPSSE);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_SetBitMode MPSSE returned %d\n", (int)ftStatus);
        return ftStatus;
    }
    usleep(60000);

    dwNumBytesToSend = 0;
    OutputBuffer[dwNumBytesToSend++] = 0xAA;
    ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    if ( ftStatus != FT_OK ) {
        printf("Failure. FT Send 0xAA %d\n", (int)ftStatus);
        return ftStatus;
    }
    dwNumBytesToSend = 0;

    usleep(800);
    do  {
        ftStatus = FT_GetQueueStatus(ftHandle, &dwNumInputBuffer);
    } while ( (dwNumInputBuffer == 0) && (ftStatus == FT_OK) );

    ftStatus = FT_Read(ftHandle, InputBuffer, dwNumInputBuffer, &dwNumBytesRead);
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed reading input buffer for echo %d\n", (int)ftStatus);
        return ftStatus;
    }

    for ( dwCount = 0; dwCount < (dwNumBytesRead - 1); dwCount++ ) {
        if ( verbosity )
            printf("receive input buffer %x %x\n", InputBuffer[dwCount], InputBuffer[dwCount + 1]);
        if ( (InputBuffer[dwCount] == 0xFA) && (InputBuffer[dwCount + 1] == 0xAA) ) {
            bCommandEchod = TRUE;
            break;
        }
    }

    if ( bCommandEchod == FALSE ) {
        printf("received %d char echoed for 0xAA command\n", dwNumBytesRead);
        printf("fail to synchronize MPSSE with command '0xAA' ");
        return FT_DEVICE_NOT_OPENED;
    }

    OutputBuffer[dwNumBytesToSend++] = 0xAB;
    ftStatus = FT_Write(ftHandle, OutputBuffer, dwNumBytesToSend, &dwNumBytesSent);
    if ( ftStatus != FT_OK ) {
        printf("Failure. FT Send 0xab %d\n", (int)ftStatus);
        return ftStatus;
    }
    dwNumBytesToSend = 0;

    usleep(800);
    do  {
        ftStatus = FT_GetQueueStatus(ftHandle, &dwNumInputBuffer);
    } while ( (dwNumInputBuffer == 0) && (ftStatus == FT_OK) );

    ftStatus = FT_Read(ftHandle, InputBuffer, dwNumInputBuffer, &dwNumBytesRead);
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed reading input buffer for echo %d\n", (int)ftStatus);
        return ftStatus;
    }

    for ( dwCount = 0; dwCount < (dwNumBytesRead -1); dwCount++ ) {
        if ( (InputBuffer[dwCount] == 0xFA) && (InputBuffer[dwCount + 1] == 0xAB) ) {
            bCommandEchod = TRUE;
            break;
        }
    }

    if ( bCommandEchod == FALSE ) {
        printf("received %d char echoed for 0xAB command\n", dwNumBytesRead);
        printf("fail to synchronize MPSSE with command '0xAB' \n");
        return FT_DEVICE_NOT_OPENED;
    }
/*
    ftStatus = sendJtagCommand(ftHandle, dis_clock, sizeof(dis_clock));
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed to send dis_clock %d\n", (int)ftStatus);
        return ftStatus;
    }
*/
    ftStatus = sendJtagCommand(ftHandle, setup_reg, sizeof(setup_reg));
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed to send setup_reg %d\n", (int)ftStatus);
        return ftStatus;
    }

    ftStatus = sendJtagCommand(ftHandle, setup_spi, sizeof(setup_spi));
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed to send setup_spi %d\n", (int)ftStatus);
        return ftStatus;
    }
    usleep(30000);

    ftStatus = sendJtagCommand(ftHandle, setClock, sizeof(setClock));
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed to send setClock %d\n", (int)ftStatus);
        return ftStatus;
    }
    ftStatus = sendJtagCommand(ftHandle, dis_lpbk, sizeof dis_lpbk);
    if ( ftStatus != FT_OK ) {
        printf("Failure. Failed to send dis_lpbk %d\n", (int)ftStatus);
        return ftStatus;
    }

    usleep(50000);
    printf("SPI initial successful\n");
    return ftStatus;
}

void queue_clear(void)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD rx_buf, tx_buf, event, bytesRead, count = 20;
    char buffer[100];

    ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
    if ( ftStatus != FT_OK ) {
        printf("\nFailure.  FT_GetQueueStatus returned %d.\n", (int)ftStatus);
        return;
    }

    while ( (rx_buf || tx_buf) && count ) {
        // Then copy D2XX's buffer to ours.
        ftStatus = FT_Read(ftHandle, buffer, rx_buf, &bytesRead);
        if ( ftStatus != FT_OK ) {
            printf("Failure.  FT_Read returned %d.\n", (int)ftStatus);
            return;
        }

        ftStatus = FT_GetStatus(ftHandle, &rx_buf, &tx_buf, &event);
        if ( ftStatus != FT_OK ) {
            printf("\nFailure.  FT_GetQueueStatus returned %d.\n", (int)ftStatus);
            return;
        }
    }
    if ( rx_buf || tx_buf )
        printf("failed to clear buffer\n");
    return;
}

FT_STATUS jtag_clear(DWORD portNum)
{
    ULONGLONG j2c_mem_addr;
    ULONGLONG pcie_bar;
    DWORD magic;
    int rc;

    if ( portNum & 0x100 ) {
        printf("Clear Dongle port settings\n");
        rc = spi_init((portNum >> 8) & 0x1);
        printf("spi_init returns %d\n", rc);
        rc = spi_rd(0, J2C_0_MAGIC_REG, &magic);
        printf("magic number %x with error code %d\n", magic, rc);

        spi_wr(0, J2C_0_MAGIC_REG, 0);
        printf("write magic number to 0 with error code %d\n", rc);
        spi_wr(0, J2C_0_SEM_REG, 0);
        printf("write semaphor number to 0 with error code %d\n", rc);

        rc = spi_rd(0, J2C_0_MAGIC_REG, &magic);
        printf("magic number is %x after clear with error code %d\n", magic, rc);
    } else if ( portNum > 0 && portNum < 12 ) {
        printf("Clear FPGA port settings for port %d\n", portNum);
        pcie_bar = get_bar_from_proc();
        if ( pcie_bar != 0 ) {
            bar_addr = pcie_bar;
        }
    
        if ( asic_index == -1 ) {
            printf("Invalid asic type. Please use set_target with a valid asic name\n");
	    return -1;
        }

        j2c_mem_addr = (ULONGLONG)(J2C_0_OFFSET + ((portNum & 0x7f) - 1) * fpga_asic_target[asic_index].size);
        rc = read_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, &magic);
        printf("magic number %x with error code %d\n", magic, rc);

        rc = write_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, 0);
        printf("write magic number to 0 with error code %d\n", rc);
        rc = write_fpga_mem32(j2c_mem_addr, J2C_0_SEM_REG, 0);
        printf("write semaphor number to 0 with error code %d\n", rc);

        rc = read_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, &magic);
        printf("magic number is %x after clear with error code %d\n", magic, rc);
    }
    return rc;
}

void jtag_close()
{
    if ( verbosity )
        printf("closing jtag\n");
    write32((ULONGLONG)ftHandle, J2C_0_MAGIC_REG, 0);
    write32((ULONGLONG)ftHandle, J2C_0_SEM_REG, 0);
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
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write reset command\n");
        return FT_WRITE_FAILURE;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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
    rc = write32((ULONGLONG)ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write enable command\n");
        return FT_WRITE_FAILURE;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = read32((ULONGLONG)ftHandle, J2C_0_STAT_REG, &resp);
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

FT_STATUS sendJtagCommand(FT_HANDLE ftHandle, BYTE *sequence, const size_t length)
{
    FT_STATUS  ftStatus = FT_OK;
    DWORD bytesToWrite = (DWORD)length;
    DWORD bytesWritten = 0;

    ftStatus = FT_Write(ftHandle, sequence, bytesToWrite, &bytesWritten);
    if ( ftStatus != FT_OK ) {
        printf("Failure.  FT_Write returned %d\n", (int)ftStatus);
        return ftStatus;
    }

    if ( bytesWritten != bytesToWrite ) {
        printf("Failure.  FT_Write wrote %d bytes instead of %d.\n",
               (int)bytesWritten,
               (int)bytesToWrite);
        ftStatus = FT_OTHER_ERROR;
    }

    return ftStatus;
}

void spi_csena()
{
    int i;

    for ( i = 0; i < 5; i++ ) {
        OutputBuffer[dwNumBytesToSend++] = 0x80;
        OutputBuffer[dwNumBytesToSend++] = 0x08; /* indicates which cs to enable */
        OutputBuffer[dwNumBytesToSend++] = 0x0b;
    }

    return;
}

void spi_csdis()
{
    int i;

    for ( i = 0; i < 5; i++ ) {
        OutputBuffer[dwNumBytesToSend++] = 0x80;
        OutputBuffer[dwNumBytesToSend++] = 0x00; /* indicates which cs to disable */
        OutputBuffer[dwNumBytesToSend++] = 0x0b;
    }

    return;
}

/* Following routines are dummy function to be compatible with asic lib compilation */
FT_STATUS spi_reg_init(void)
{
    return FT_OK;
}

void ftHandle_close()
{
    return;
}

