#include "accpcie.h"
#include <time.h>

int verbosity = 0;
ULONG bar_addr = 0x40000000;
FT_HANDLE ftHandle = 0;

void set_verbosity(int level)
{
    verbosity = level;
    return;
}

void set_bar(ULONG addr)
{
    bar_addr = addr;
    return;
}

ULONG show_bar(void)
{
    if ( verbosity != 0 )
        printf("FPGA PCIe BAR address = %x\n", bar_addr);
    return bar_addr;
}

int read_fpga_mem32(ULONG ftHandle, DWORD reg, DWORD *data)
{
    ULONG *addr;

    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = ((ftHandle + reg) / pagesize) * pagesize;
    off_t page_offset = ftHandle + reg - page_base;

    if ( verbosity )
        printf("read_fpag_mem32\n");
    /* int fd = open("/dev/mem", O_SYNC); */
    int fd = open("/sys/bus/pci/devices/0000:07:00.0/resource0", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }

    /* unsigned char *mem = mmap(NULL, page_offset + 256, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, page_base); */
    unsigned char *mem = mmap((void *)0xfb400000, 1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd);
        return FT_ERROR_MAP_PCIE;
    }

    addr = (DWORD *)(ftHandle + reg);
    *data = *addr;

    close(fd);
    return FT_OK;
}

int write_fpga_mem32(ULONG ftHandle, DWORD reg, ULONG value)
{
    DWORD *addr;

    size_t pagesize = sysconf(_SC_PAGE_SIZE);
    off_t page_base = ((ftHandle + reg) / pagesize) * pagesize;
    off_t page_offset = ftHandle + reg - page_base;

    if ( verbosity )
        printf("write_fpag_mem32\n");
    /* int fd = open("/dev/mem", O_RDWR | O_SYNC); */
    int fd = open("/sys/bus/pci/devices/0000:07:00.0/resource0", O_RDWR | O_SYNC);
    if ( fd < 0 ) {
        printf("Can't open /dev/mem\n");
        return FT_ERROR_OPEN_MEM;
    }

    
    unsigned char *mem = mmap((void *)0xfb400000, 1024 *1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if ( mem == NULL ) {
        printf("failed to  map pcie memory\n");
        close(fd); 
        return FT_ERROR_MAP_PCIE;
    }

    addr = (DWORD *)(mem + reg);
    if ( verbosity ) {
        printf("reg address %x\n", reg);
        printf("addr address %x\n", (DWORD)addr);
        printf("data %x\n", value);
    }
    *addr = (DWORD)value;

    close(fd); 
    return FT_OK;
}

int write_fpga_mem64(ULONG ftHandle, DWORD reg, ULONGLONG value)
{
    int rc = 0;

    return rc;
}

FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;;
    DWORD cmd;
    DWORD resp;
    int wait_cnt = 10;
    int i;
    int rc = 0;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & 0x1F) | (size << 8) | ((flag & 0x1) << 10); 
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

    return ftStatus;
}

FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag)
{
    FT_STATUS ftStatus = FT_OK;
    DWORD cmd;
    DWORD resp;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
    int wait_cnt = 10;
    int i, rc = 0;
 
    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    rc = write_fpga_mem32(ftHandle, J2C_0_ADDR0_REG, address & 0xffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & 0x1F) | (size << 8) | ((flag & 0x1) << 10); 
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
    if ( resp & J2C_VALID_BIT ) {
        if ( verbosity )
            printf("invalid response\n");
        return FT_INVALID_RESP;
    } else if ( resp & J2C_ID_BIT ) {
        if ( verbosity )
            printf("invalid ID\n");
        return FT_ERROR_ID;
    } 

    rc = read_fpga_mem32(ftHandle, J2C_0_RXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read data\n");
        *data = 0xdeadbeef;
        return -1;
    }
    return ftStatus;
}

int jtag_tst(DWORD inst, BYTE enable)
{
    return 0;
}

FT_STATUS jtag_init(DWORD portNum)
{
    time_t rawtime;
    struct tm *timeinfo;
    ULONG j2c_mem_addr;
    DWORD magic;
    int rc;

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    j2c_mem_addr = bar_addr + J2C_0_CMD_REG + (portNum - 1) * 32;
    read_fpga_mem32(j2c_mem_addr, J2C_0_MAGIC_REG, &magic);
    printf("01-17-2023 -- port number = 0x%x timeinfo %d:%d:%d\n", portNum, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
    printf("magic number %x\n", magic);
    if ( magic != 0 ) {
        if ( verbosity != 0 )
            printf("jtag for this instance has been opened already!\n");
        return (FT_STATUS)magic;
    }
    ftHandle = j2c_mem_addr;
    rc = write_fpga_mem32(ftHandle, J2C_0_MAGIC_REG, (DWORD)(ftHandle & 0xffffffff));
    if ( rc )
        ftHandle = 0;
    return rc;
}

void jtag_close()
{
    if ( verbosity )
        printf("closing jtag\n");
    if ( ftHandle == 0 ) {
        printf("ftHandle is zero, the port is not opened\n");
    } else {
        write_fpga_mem32(ftHandle, J2C_0_MAGIC_REG, 0);
        write_fpga_mem32(ftHandle, J2C_0_SEM_REG, 0);
    }
    ftHandle = 0;
    return;
}

FT_STATUS jtag_reset(DWORD inst)
{
    DWORD cmd;
    DWORD resp;
    int wait_cnt = 10;
    int i, rc = 0;

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
    return FT_OK;
}

FT_STATUS jtag_enable(DWORD inst)
{
    DWORD cmd;
    DWORD resp;
    int wait_cnt = 10;
    int i, rc = 0;

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
    return FT_OK;
}

int main(void)
{
    DWORD data;

    printf("size of ULONG = %d\n", sizeof(ULONG));
    set_verbosity(1);
    set_bar(0xfb400000);
    jtag_init(1);
    jtag_reset(1);
    jtag_enable(1);
    jtag_wr(0, 0x307c0000, 0x1, 2);
    jtag_rd(0, 0x307c0000, &data, 2);
    printf("data read = %x\n", data);
    return 0;
}
    
