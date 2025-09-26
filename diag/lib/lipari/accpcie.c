#include "accpcie.h"
#include <time.h>
#include <stdio.h>
#include <unistd.h>

/********************************************************************************************************** 
 NOTES FOR HOW THE HPE PALERMO SYSTEM WORKS.
 IT IS A BIT DIFFERENT THAN LIPARI AND MTFUJI (CICSCO).
 ON PALERMO THERE IS AN FPGA INSTEAD OF A CPLD ON EACH CAPACI CARD WITH AN ELBA.
 THTA FPGA ON CAPACI CONTROLS J2C DIRECTLY.   IT IS NOT DRIVEN FROM THE HOST FPGA.
 SPI IS USED TO COMMUNICATE TO THE FPGA ON CAPACI TO DRIVE THE J2C MAILBOX.
 [PALERMO HOST]HOST --> SPI --> [CAPACI MODULE][ELBA FPGA --> J2C --> ELBA]
 
 NOTES FROM CHARLES (FROM HPE)
 -----------------------------
 Two things will have to happen to get the J2C server to work correctly with Elba:
1) change the reset mask in the CPLD to allow Elba to reset itself
2) ensure stage 2 power is on for the particular slot you are using
If you want to access the Elba Console port, our preferred method is though pyserial (needs to be loaded externally, not built into Halon image) or it can also be done with screen (built in but sometimes drops characters), following these steps:
 1. (optional) install pyserial (I can provide the package and instructions)
 2. change the FPGA MUX to the correct Capaci slot
 3. open the connection through ttyS3 with an SR2 release of Halon or ttyS8 with an SR3 release of Halon
To change any CPLD registers you first need to find the base address of our "MCBE" which I like to do with lspci -vvPPnd 1590:180 | grep "Memory at" where the second output is the base address of our MCBE.
Here is my example output with the base address being 0x10a1700000 and I verified the device ID right after:
  10040:/fs/nos# lspci -vvPPnd 1590:180 | grep "Memory at"
         Region 0: Memory at 10a1b00000 (64-bit, prefetchable) [size=1M]
        Region 0: Memory at 10a1700000 (64-bit, prefetchable) [size=1M]
  10040:/fs/nos# memtool md 0x10a1700000+1
  10a1700000: 060dcf05          



After you know this base address, you can determine the state of Stage 2 power for the Capaci cards by subtracting 0x100000 and adding 0x300 to get to the Stage 2 power control register.  In my case, I have a single Capaci in slot 5 that I have powered on, the rest of the slots are unpowered currently (all present cards should be powered automatically if everything is working correctly). There is one nibble per card with a value of 6 turning the card on and a value of 9 turning the card off, all other values do nothing.
  10040:/fs/nos# memtool md 0x10A1600300+1
  10a1600300: 00969999 

The reset mask is a bit more complicated.  It has to be set through a virtual SPI interface to the Capaci CPLD.  The VSPI controllers are all in the group of registers with a -200000 offset from the base address.
There are 4 VSPI registers you need to interact with:
  1) control (base offset for controller, 0x7C0 for slot 6)
  2) address (base+4, 0x7C4 for slot 6)
  3) tx data (base+8, 0x7C8 for slot 6)
  4) rx data (base+12, 0x7CC for slot 6)

To set the reset mask in address 0x3C0 of the Capaci CPLD, you need to load that value into the address register, then load the mask value into the TX register, then set the command register to 0x105.
To read back the mask, you need to set the address register to 0x3C0, then set the command register to 0x103, then read the data in the rx register.
Here is an example of enabling Elba resets for slot six with my MCBE base address of 0x10A1700000 and reading it back:
  10040:/fs/nos# memtool mw 0x10A15007C4 0x3C0
  10040:/fs/nos# memtool mw 0x10A15007C8 0x990000
  10040:/fs/nos# memtool mw 0x10A15007C0 0x105
  10040:/fs/nos# memtool mw 0x10A15007C4 0x3C0
  10040:/fs/nos# memtool mw 0x10A15007C0 0x103
  10040:/fs/nos# memtool md 0x10A15007CC+1
  10a15007cc: 00990000   
the offset between each VSPI controller is 64, so you can subtract 64 from each address to talk to slot 5 instead.  this works all the way down to slot 1. 
 
 
After you know this base address, you can determine the state of Stage 2 power for the Capaci cards by subtracting 0x100000 and adding 0x300 to get to the 
Stage 2 power control register. 
In my case, I have a single Capaci in slot 5 that I have powered on, the rest of the slots are unpowered 
currently (all present cards should be powered automatically if everything is working correctly). 
There is one nibble per card with a value of 6 turning the card on and a value of 9 turning the card off, all other values do nothing.
10040:/fs/nos# memtool md 0x10A1600300+1
10a1600300: 00969999 
 
 
 
The other item that can be done is the status can be checked before starting a register transaction.  before any transaction, 
the CMD_STAT_REG should be read and bit 8 needs to be asserted.  the value should be 0x10y where the "y" is a "don't care" 
**********************************************************************************************************/

#define WAIT_CNT 1000

#define LIPARI   1
#define MTFUJI   2
#define PALERMO  3

int verbosity = 5;
ULONGLONG bar_addr = 0;//0x10021100000;
FT_HANDLE ftHandle = 0;
DWORD portNumber = 0;
unsigned int platform = LIPARI;

struct platform {
    char *  pciDevice;
    char *  Name;
    int     PlatformNumber;
    int     MaxJtagDevices;
    int     found;
};

struct platform Platform_t[] = { { "1dd8000a", "LIPARI", LIPARI, 8, 0},
                                 { "11370183", "MTFUJI", MTFUJI, 4, 0},
                                 { "15900180","PALERMO", PALERMO, 6, 0}};

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

void set_bar(ULONGLONG addr)
{
    bar_addr = addr;
    return;
}

int FindPlatform(ULONGLONG * bar, uint32_t * entry) {
    int i=0;
    FILE *fileptr;
    char line[512];
    char delim[] = "\t";
    char *ptr = NULL;
    int len;
    int palermo_bar_cnt = 0; //Palermo has two FPGA with the same dev id.  Need to get bar from the 2nd instance
    unsigned long long int address = 0;

    for(i=0; i<sizeof(Platform_t)/(sizeof(struct platform)); i++) {
        fileptr = fopen("/proc/bus/pci/devices", "r");
        if ( fileptr == NULL ) {
            printf("pcie device under proc cannot be opened\n");
            return address;
        }
        while ( fgets(line, sizeof(line), fileptr) ) {
            ptr = strtok(line, delim);
            while ( ptr != NULL ) {
               if ( strcasecmp(ptr, Platform_t[i].pciDevice) == 0 ) {
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
                //On Palermo, need the BAR from the 2nd FPGA instance.  Skip the first instance found.
                if ((Platform_t[i].PlatformNumber == PALERMO) && (PALERMO && palermo_bar_cnt == 0)) {
                    palermo_bar_cnt++;
                    address=0;
                    continue;
                }
                if ( verbosity )
                    printf("PCIE BAR = 0x%llx\n", address);
                *bar = address;
                //Address for SPI Mailboxes on Palermo needs an offset to the bar
                if (Platform_t[i].PlatformNumber == PALERMO) {
                    *bar = *bar - 0x200000;   
                }
                *entry = i;
                fclose(fileptr);
                return address;
            }
        }
        fclose(fileptr);
    }

    return -1;
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
           if ( strcmp(ptr, "1dd8000a") == 0 ) {
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


/***************************************************************************************
Read: fpgar DPCB_REGS JTAG_ADDR_REG 0 0 <DPU slot#> <0 or 1 for ADDR0 or ADDR1>
Wrtie: fpgaw DPCB_REGS JTAG_ADDR_REG 0 <value> <DPU slot#> <0 or 1 for ADDR0 or ADDR1>

Read: fpgar DPCB_REGS <register> 0 0 <DPU slot#> 0
Wrtie: fpgaw DPCB_REGS <register> 0 <value> <DPU slot#> 0
•	DPU Slot: 1-6
•	register
o	JTAG_CMD_REG
o	JTAG_STAT_REG
o	JTAG_ADDR_REG
o	JTAG_TX_DATA_REG
o	JTAG_RX_DATA_REG
o	JTAG_LOCK_REG
o	JTAG_MAGIC_REG
o	JTAG_CONF_REG
o	JTAG_RST_REG
o	JTAG_MUX_SEL_REG 
/**************************************************************************************/
int PalermoRegTranslation(uint32_t reg, char * regString, uint32_t * addrarg) 
{
    switch(reg) {
        case J2C_0_CMD_REG:
            strcpy(regString,"JTAG_CMD_REG");
            *addrarg = 0;
            break;
        case J2C_0_STAT_REG:
            strcpy(regString,"JTAG_STAT_REG");
            *addrarg = 0;
            break;
        case J2C_0_ADDR0_REG:
            strcpy(regString,"JTAG_ADDR_REG");
            *addrarg = 0;
            break;
        case J2C_0_ADDR1_REG:
            strcpy(regString,"JTAG_ADDR_REG");
            *addrarg = 1;
            break;
        case J2C_0_TXDATA_REG:
            strcpy(regString,"JTAG_TX_DATA_REG");
            *addrarg = 0;
            break;
        case J2C_0_RXDATA_REG:
            strcpy(regString,"JTAG_RX_DATA_REG");
            *addrarg = 0;
            break;
        case J2C_0_SEM_REG:
            strcpy(regString,"JTAG_LOCK_REG");
            *addrarg = 0;
            break;
        case J2C_0_MAGIC_REG:
            strcpy(regString,"JTAG_MAGIC_REG");
            *addrarg = 0;
            break;
        case J2C_0_CONF_REG:
            strcpy(regString,"JTAG_CONF_REG");
            *addrarg = 0;
            break;
        case J2C_0_RST_REG:
            strcpy(regString,"JTAG_RST_REG");
            *addrarg = 0;
            break;
        case J2C_0_MUX_REG:
            strcpy(regString,"JTAG_MUX_SEL_REG");
            *addrarg = 0;
            break;
    }
    return 0;
}


/***************************************************************************************
Perform a SPI Write to the FPGA hooked to ELBA. 
This will be used to access the J2C Mailbox. 
Path:  Palmero FPGA -> (SPI) -> Capaci FPGA (J2C Mailbox) 
 
address --> Address FPGA hooked to Elba to access.  This will be a j2c mailbox address 
data --> Data to write 
****************************************************************************************/
int PalermoWriteJ2Creg(uint32_t address, uint32_t data)
{

    uint32_t rdData = 0;
    int rc = 0;
    int spiStatusCheckCount=50;
    int spiNotBusyCount=10000;
    int i=0;
    //int retry=0;
    //int MaxRetry=3;

//writej2cretry:
    //Check the mailbox is not busy.  Want to see 0x10y where y is don't care
    for(i=0;i<spiNotBusyCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if ((rdData & 0xFF0) == 0x100) {
            break;
        }
    }
    if(i==spiNotBusyCount) {
        printf("ERROR: %s line-%d SPI MAILBOX IS BUSY FOR %d READS.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, spiNotBusyCount, rdData);
        return -1;
    }

    //Set Address to access on FPGA hooked to Elba
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, ftHandle + address);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__);
        return -1;
    }

    //Set data to write to Capaci FPGA
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_WR_OFFSET, data);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    //Issue a write to SPI CTRL REG
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, 0x105);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    //Check our address is still in the spi mailbox.  If it isn't our transaction was over-written by another
    /*
    rc = read_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, &rdData);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }
    if ((rdData != (ftHandle + address)) && (retry<MaxRetry)) {
        printf("WARN WARN WARN:  RETRY SPI WR ACCESS TO SLOT\n");
        retry++;
        goto writej2cretry;
    } 
    */ 

    //Check for transaction complete 0x104.
    for(i=0;i<spiStatusCheckCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if (rdData == 0x104) {
            break;
        }
    }
    if(i==spiStatusCheckCount) {
        printf("ERROR: %s line-%d did not receive spi good status from palermo fpga to capaci fpga.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, rdData);
        return -1;
    }
    return rc; 

    //Alt method trying to use their binary.  Found binary was too slow and j2c was failing
    /*
    int rc = 0;
    char line[BUFSIZ];
    unsigned long data64 = 0;
    FILE *pipe;
    char command[BUFSIZ];
    char regString[16];
    uint32_t addrArg = 0;
    uint32_t data32 = 0;

    PalermoRegTranslation(address, &regString[0], &addrArg); 
    sprintf(command, "fpgaw DPCB_REGS %s 0 0x%x %d %d | grep VALUE | awk '{print $5}'", regString, data, portNumber, addrArg);
    //printf("COMMAND=%s\n", command);
    
    // Get a pipe where the output from the scripts comes in 
    pipe = popen(command, "r");
    if (pipe == NULL) {  
        printf(" fpgar error\n");
        return -1;        
    }

    if (fgets(line, BUFSIZ, pipe) != NULL) {
        data32 = strtoul(line, NULL, 16);
        if(data32 != data) {
            printf("ERROR: popen fpgaw did not see valid data output\n");
        }
    } else {
        printf("ERROR: popen of fpgar returned no data\n");
        rc = -1;
    }

    pclose(pipe);
    return rc; 
    */ 
}


/***********************************************************************************************
Perform a SPI Read to the FPGA hooked to ELBA. 
This will be used to access the J2C Mailbox. 
Path:  Palmero FPGA -> (SPI) -> Capaci FPGA (J2C Mailbox) 
 
address --> Address FPGA hooked to Elba to access.  This will be a j2c mailbox address to read
data --> data that is read back 
************************************************************************************************/
int PalermoReadJ2Creg(uint32_t address, uint32_t * data)
{
    uint32_t rdData = 0;
    int rc = 0;
    int spiStatusCheckCount=200;
    int spiNotBusyCount=10000;
    int i=0;
    //int retry=0;
    //int MaxRetry=0;

//readj2cretry:
    //Check the mailbox is not busy.  Want to see 0x10y where y is don't care
    for(i=0;i<spiNotBusyCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if ((rdData & 0xFF0) == 0x100) {
            break;
        }
    }
    if(i==spiNotBusyCount) {
        printf("ERROR: %s line-%d SPI MAILBOX IS BUSY FOR %d READS.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, spiNotBusyCount, rdData);
        return -1;
    }

    //Set Address to access on FPGA hooked to Elba
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, ftHandle + address);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    //Issue a read to SPI CTRL REG
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, 0x103);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }
    //Check for transaction complete 0x104.  If this does not happen there 
    //is a high chance you will read stale (old) data from the read register.
    for(i=0;i<spiStatusCheckCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if (rdData == 0x102) {
            break;
        }
    }
    if(i==spiStatusCheckCount) {
        /*
        if(retry < MaxRetry) {
            retry++;
            printf("WARN WARN WARN:  RETRY-%d SPI RD ACCESS TO SLOT\n", retry);
            goto readj2cretry;
        } 
        */ 
        printf("ERROR: %s line-%d did not receive spi good status from palermo fpga to capaci fpga.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, rdData);
        read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, data);
        printf("[0x00]=%x\n", *data);
        read_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, data);
        printf("[0x04]=%x\n", *data);
        read_fpga_mem32(0, PALMERO_SPI_MB_WR_OFFSET, data);
        printf("[0x08]=%x\n", *data);
        read_fpga_mem32(0, PALMERO_SPI_MB_RD_OFFSET, data);
        printf("[0x0C]=%x\n", *data);      
        *data == 0xdeadbeef;
        return -1;
    }
    
    //Read data 
    rc = read_fpga_mem32(0, PALMERO_SPI_MB_RD_OFFSET, data);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    //Check our address is still in the spi mailbox.  If it isn't our transaction was over-written by another
    /*
    rc = read_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, &rdData);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }
    if ((rdData != (ftHandle + address)) && (retry<MaxRetry)) {
        retry++;
        printf("WARN WARN WARN:  RETRY-%d SPI RD* ACCESS TO SLOT\n", retry);        
        goto readj2cretry;
    } 
    */ 


    return(rc); 

    //Alt method trying to use their binary.  Found binary was too slow and j2c was failing
    /*
    int rc = 0;
    char line[BUFSIZ];
    unsigned long data64 = 0;
    FILE *pipe;
    char command[BUFSIZ];
    char regString[16];
    uint32_t addrArg = 0;

    PalermoRegTranslation(address, &regString[0], &addrArg); 
    sprintf(command, "fpgar DPCB_REGS %s 0 0 %d %d | grep VALUE | awk '{print $3}'", regString, portNumber, addrArg);
    //printf("COMMAND=%s\n", command);
    
    // Get a pipe where the output from the scripts comes in 
    pipe = popen(command, "r");
    if (pipe == NULL) {  
        printf(" fpgar error\n");
        return -1;        
    }

    if (fgets(line, BUFSIZ, pipe) != NULL) {
        *data = strtoul(line, NULL, 16);
    } else {
        printf("ERROR: popen of fpgar returned no data\n");
        rc = -1;
    }

    pclose(pipe);
    return rc;
    */
}

/***********************************************************************************************
Perform a SPI Read to the FPGA hooked to ELBA. 
This will be used to access the J2C Mailbox. 
Path:  Palmero FPGA -> (SPI) -> Capaci FPGA (J2C Mailbox) 
 
address --> Address FPGA hooked to Elba to access.  This will be a j2c mailbox address to read
data --> data that is read back 
************************************************************************************************/
int PalermoVspiMBPoll(uint32_t address, uint32_t * data, uint32_t iterations)
{
    uint32_t rdData = 0;
    int rc = 0;
    int spiStatusCheckCount=200;
    int spiNotBusyCount=10000;
    int i=0;
    uint32_t ctrl, addr, wroff, rdoff;
    uint32_t rdctrl, rdaddr, rdwroff, rdrdoff;

    //Check the mailbox is not busy.  Want to see 0x10y where y is don't care
    for(i=0;i<spiNotBusyCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if ((rdData & 0xFF0) == 0x100) {
            break;
        }
    }
    if(i==spiNotBusyCount) {
        printf("ERROR: %s line-%d SPI MAILBOX IS BUSY FOR %d READS.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, spiNotBusyCount, rdData);
        return -1;
    }

    //Set Address to access on FPGA hooked to Elba
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, ftHandle + address);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    //Issue a read to SPI CTRL REG
    rc = write_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, 0x103);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }
    //Check for transaction complete 0x104.  If this does not happen there 
    //is a high chance you will read stale (old) data from the read register.
    for(i=0;i<spiStatusCheckCount;i++) {
        rc = read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdData);
        if ( rc ) {
            printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
            return -1;
        }
        if (rdData == 0x102) {
            break;
        }
    }
    if(i==spiStatusCheckCount) {
        printf("ERROR: %s line-%d did not receive spi good status from palermo fpga to capaci fpga.  Expect 0x104.  Read 0x%x\n", __FUNCTION__, __LINE__, rdData);
        *data == 0xdeadbeef;
        return -1;
    }
    
    //Read data 
    rc = read_fpga_mem32(0, PALMERO_SPI_MB_RD_OFFSET, data);
    if ( rc ) {
        printf("%s line-%d failed write_fpga_mem32\n", __FUNCTION__, __LINE__); 
        return -1;
    }

    read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &ctrl);
    printf("[0x00]=%x\n", ctrl);
    read_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, &addr);
    printf("[0x04]=%x\n", addr);
    read_fpga_mem32(0, PALMERO_SPI_MB_WR_OFFSET, &wroff);
    printf("[0x08]=%x\n", wroff);
    read_fpga_mem32(0, PALMERO_SPI_MB_RD_OFFSET, &rdoff);
    printf("[0x0C]=%x\n", rdoff);

    for(i=0;i<iterations;i++) {
        read_fpga_mem32(0, PALMERO_SPI_MB_CTRL_OFFSET, &rdctrl);
        read_fpga_mem32(0, PALMERO_SPI_MB_ADDR_OFFSET, &rdaddr);
        read_fpga_mem32(0, PALMERO_SPI_MB_WR_OFFSET, &rdwroff);
        read_fpga_mem32(0, PALMERO_SPI_MB_RD_OFFSET, &rdrdoff);

        if ((ctrl != rdctrl) || (addr != rdaddr) || (wroff != rdwroff) || (rdoff != rdrdoff)) {
            printf("[0x00]=%x\n", ctrl);
            printf("[0x04]=%x\n", addr);
            printf("[0x08]=%x\n", wroff);
            printf("[0x0C]=%x\n", rdoff);

            printf("[0x00]=%x\n", rdctrl);
            printf("[0x04]=%x\n", rdaddr);
            printf("[0x08]=%x\n", rdwroff);
            printf("[0x0C]=%x\n", rdrdoff);
            return 0;
        }
    }


    return(rc); 

}


int platform_j2c_mailbox_register_read(ULONGLONG inst_offset, DWORD reg, DWORD *data)
{
    if(platform == PALERMO) {
        return(PalermoReadJ2Creg(reg, data));
    } else {
        return(read_fpga_mem32(inst_offset, reg, data));
    }
}

int platform_j2c_mailbox_register_write(ULONGLONG inst_offset, DWORD reg, ULONG value)
{
    if(platform == PALERMO) {
        return(PalermoWriteJ2Creg(reg, value));
    } else {
        return(write_fpga_mem32(inst_offset, reg, value));
    }
    return FT_OK;
}

FT_STATUS jtag_wr(DWORD inst, ULONGLONG address, DWORD data, DWORD flag)
{
    FT_STATUS rc = FT_OK;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;;
    DWORD cmd;
    DWORD resp;
    DWORD dummy = inst;
    int wait_cnt = WAIT_CNT;
    int i;

    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & 0x1F) | (size << 8) | ((flag & 0x1) << 10); 
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_TXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring data\n");
        return -1;
    }
 
    cmd = J2C_WRITE_COMMAND;
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte write command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_STAT_REG, &resp);
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
    return rc;
}

FT_STATUS jtag_wg(ULONGLONG address, DWORD data)
{
    FT_STATUS rc = FT_OK;

    rc = platform_j2c_mailbox_register_write(ftHandle, (DWORD)address, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write register\n");
        return -1;
    }
    return rc;
}

FT_STATUS jtag_rg(ULONGLONG address, DWORD *data)
{
    FT_STATUS rc = FT_OK;

    rc = platform_j2c_mailbox_register_read(ftHandle, (DWORD)address, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read register\n");
        return -1;
    }
    return rc;
}

FT_STATUS palermo_platform_spi_write(ULONGLONG address, DWORD data)
{
    FT_STATUS rc = FT_OK;
    FT_HANDLE temp = ftHandle;

    //ftHandle on Palermo holds the j2c mailbox offset on Capaci's fpga
    //For RAW SPI access, neeed to set it to 0 
    ftHandle = 0;
    rc = platform_j2c_mailbox_register_write(ftHandle, (DWORD)address, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write register\n");
        return -1;
    }
    ftHandle = temp;
    return rc;
}

FT_STATUS palermo_platform_spi_read(ULONGLONG address, DWORD *data)
{
    FT_STATUS rc = FT_OK;
    FT_HANDLE temp = ftHandle;

    //ftHandle on Palermo holds the j2c mailbox offset on Capaci's fpga
    //For RAW SPI access, neeed to set it to 0 
    ftHandle = 0;
    rc = platform_j2c_mailbox_register_read(ftHandle, (DWORD)address, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read register\n");
        return -1;
    }
    ftHandle = temp;
    return rc;
}

FT_STATUS jtag_rd(DWORD inst, ULONGLONG address, DWORD* data, DWORD flag)
{
    FT_STATUS rc = FT_OK;
    DWORD cmd;
    DWORD resp;
    DWORD size = ((flag >> 1) & 0x1) ? 0x2 : 0x0;
    DWORD dummy = inst;
    int wait_cnt = WAIT_CNT;
    int i = 0;
 
    inst = dummy;

    if ( ftHandle == 0 ) {
        if ( verbosity != 0 )
            printf("j2c port is not opened\n");
        return -1;
    }

    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_ADDR0_REG, address & 0xffffffff);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address lower 32 bit\n");
        return -1;
    }
    address = ((address >> 32) & 0x1F) | (size << 8) | ((flag & 0x1) << 10); 
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_ADDR1_REG, address);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wring address higher 32 bit\n");
        return -1;
    }

    cmd = J2C_READ_COMMAND;
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to wrte read command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_STAT_REG, &resp);
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
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write response command\n");
        return -1;
    }
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_STAT_REG, &resp);
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
            printf("invalid ID\n");
        return FT_ERROR_ID;
    } 
    rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_RXDATA_REG, data);
    if ( rc ) {
        if ( verbosity )
            printf("failed to read data\n");
        *data = 0xdeadbeef;
        return -1;
    }
    if ( verbosity == 2 )
        printf("FINISH READ\n");
    return rc;
}

FT_STATUS jtag_init(DWORD portNum)
{
    time_t rawtime;
    struct tm *timeinfo;
    ULONGLONG j2c_mem_addr;
    ULONGLONG pcie_bar;
    DWORD magic;
    int entry;
    int rc;

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    //pcie_bar = get_bar_from_proc();
    //if ( pcie_bar != 0 ) {
    //    bar_addr = pcie_bar;
    //}
    rc = FindPlatform(&pcie_bar, &entry);
    if (rc == 0) {
        printf(" jtag_init ERROR: Failed to find a valid platform\n");
        printf(" jtag_init ERROR: Failed to find a valid platform\n");
        return -1;
    }
    bar_addr = pcie_bar;
    portNumber = portNum;

    if (portNum > Platform_t[entry].MaxJtagDevices || portNum == 0) {
        printf(" jtag_init ERROR: Jtag port range is 1 - %d.  You Passed %d\n", Platform_t[entry].MaxJtagDevices, portNum);
        printf(" jtag_init ERROR: Jtag port range is 1 - %d.  You Passed %d\n", Platform_t[entry].MaxJtagDevices, portNum);
        return -1;
    }

    if (Platform_t[entry].PlatformNumber == LIPARI) {
        j2c_mem_addr = J2C_0_OFFSET + ((portNum - 1) * 32);
        platform = LIPARI;
    } else if (Platform_t[entry].PlatformNumber == MTFUJI) {
        j2c_mem_addr = MTFUJI_JTAG0_BASE + ((portNum - 1) * MTFUJI_JTAG_STRIDE);
        platform = MTFUJI;
    } else if (Platform_t[entry].PlatformNumber == PALERMO) {
        j2c_mem_addr = PALERMO_JTAG0_BASE;
        bar_addr = bar_addr + (PALMERO_SLOT0_SPI_MB + (PALMERO_SPI_MB_STRIDE * (portNum-1)));
        platform = PALERMO;
    } else {
        printf(" jtag_init ERROR: Platform Type not found.  Entry = %d.  NOTE THIS SHOULD NOT HAPPEN\n", entry);
        printf(" jtag_init ERROR: Platform Type not found.  Entry = %d.  NOTE THIS SHOULD NOT HAPPEN\n", entry);
        return -1;
    }

   
    printf("07-16-2025 -- port number = 0x%x timeinfo %d:%d:%d\n", portNum, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
    printf("bar address is set with  0x%llx  fpga mem offset = %llx  platform=%s\n", bar_addr, j2c_mem_addr, Platform_t[entry].Name);
    
    ftHandle = (DWORD)j2c_mem_addr & 0xffffffff;
    if(platform != PALERMO) {
        rc = platform_j2c_mailbox_register_write(j2c_mem_addr, J2C_0_MAGIC_REG, ftHandle);
        if ( rc )
            ftHandle = 0;
    }
    if ( verbosity == 2 )
        printf("FINISH INIT\n");
    return rc;
}

void jtag_close()
{
    if ( verbosity )
        printf("closing jtag\n");
    platform_j2c_mailbox_register_write(ftHandle, J2C_0_MAGIC_REG, 0);
    platform_j2c_mailbox_register_write(ftHandle, J2C_0_SEM_REG, 0);
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
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write reset command\n");
        return FT_WRITE_FAILURE;
    }
    sleep(1);
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_STAT_REG, &resp);
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
    rc = platform_j2c_mailbox_register_write(ftHandle, J2C_0_CMD_REG, cmd);
    if ( rc ) {
        if ( verbosity )
            printf("failed to write enable command\n");
        return FT_WRITE_FAILURE;
    }
    sleep(1);
    for ( i = 0; i < wait_cnt; i++ ) {
        rc = platform_j2c_mailbox_register_read(ftHandle, J2C_0_STAT_REG, &resp);
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
    address = 0;
    data = 0;

    return FT_OK;
}

FT_STATUS spi_rd(BYTE address, BYTE* data)
{
    BYTE dummy;

    dummy = *data;
    dummy = 0;

    return FT_OK;
}

void ftHandle_close()
{
    return;
}

