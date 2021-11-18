
/*
4 * Copyright (c) 2018, Pensando Systems Inc.
 */

#include <linux/gpio.h>
#include <linux/spi/spidev.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdint.h>
#include <unistd.h>

// Important instructions for Read and Write from Flash.
//
// Flash Write Enable must go first before Erase or Program of Chip.
// Program command should be given only when bit 0 (WIP) of Flash Status Register is 0.
// Every Program or Erase command results in Write Disable. So Enable it next time Program or Erase command is issued.


static const char spidev_path0[] = "/dev/spidev0.0";
static const char spidev_path1[] = "/dev/spidev0.3";

typedef struct {
    uint32_t size;
    uint32_t *p_opt;
} SERDES_TEST_OPTIONS;

#define SPI_GLOBAL_INT_REG              0x1C
#define SPI_INT_STATUS_REG              0x20
#define SPI_INT_ENABLE_REG              0x28
#define SPI_SOFT_RESET_REG              0x40
#define SPI_CONTROL_REG                 0x60
#define SPI_STATUS_REG                  0x64
#define SPI_DATA_TRANSMIT_REG           0x68
#define SPI_DATA_RECEIVE_REG            0x6C
#define SPI_SLAVE_SEL_REG               0x70
// SPI commands
#define FLASH_WRITE_STATUS_REG          0x01
#define FLASH_PAGE_PROG                 0x02
#define FLASH_READ_DATA_BYTES           0x03
#define FLASH_WRITE_DISABLE             0x04
#define FLASH_READ_STATUS_REG           0x05
#define FLASH_WRITE_ENABLE              0x06
#define FLASH_SOFT_RESET                0x0A
#define FLASH_READ_ADDR4B               0x13
#define FLASH_READ_CFG_REG              0x15
#define FLASH_SECTOR_ERASE              0x20
#define FLASH_BLOCK_ERASE_32K           0x52
#define FLASH_BLOCK_ERASE_64K           0xD8
#define FLASH_CHIP_ERASE                0x60
#define FLASH_READ_ID                   0x9F
#define FLASH_ENTER_4_BYTE_MODE         0xB7

#define FLASH_OFFSET_GOLD               0x0000000
#define FLASH_OFFSET_MAIN               0x1000000
#define FLASH_OFFSET_TEST               0x1FF0000

#define FLASH_IMG_TYPE_MAIN             0
#define FLASH_IMG_TYPE_GOLD             1
#define FLASH_IMG_TYPE_TEST             2

#define FLASH_AND_SWITCH_PAGE_CONFIG    0
#define NCSI_AND_BMC_PAGE_CONFIG        1
#define PC_AND_SERDES_PAGE_CONFIG       2

#define PAGE_ID_FLASH                   0
#define PAGE_ID_SWITCH                  1
#define PAGE_ID_PC                      2
#define PAGE_ID_SERDES                  3

#define SWITCH_CORE_VERSION_REG         0x00
#define SWITCH_MAC_LOW_REG              0x04
#define SWITCH_MAC_HIGH_REG             0x08

#define FPGA_BASE_ADDR_QSPI_CTRL        0x2000000
#define FPGA_BASE_ADDR_MES_REG          0x1001000
#define FPGA_BASE_ADDR_PC               0x100C000
#define FPGA_BASE_ADDR_SERDES           0x1008000

#define PS48_FRAME_SIZE                 6
#define FLASH_PAGE_SIZE                 128
#define FLASH_TRANSFER_WIDTH_B          1
#define PS48_PIPELINE_SIZE              32

#define MDIO_CRTL_LO_REG                0x6
#define MDIO_CRTL_HI_REG                0x7
#define MDIO_DATA_LO_REG                0x8
#define MDIO_DATA_HI_REG                0x9

#define MDIO_ACC_ENA                    0x1
#define MDIO_RD_ENA                     0x2
#define MDIO_WR_ENA                     0x4


//PHY pages
#define PHY_PAGE_0                                 0
#define PHY_PAGE_1                                 1
#define PHY_PAGE_6                                 6
#define PHY_PAGE_18                                18

//PHY registers
#define PHY_PAGE_REG                               22

//PHY page 0
#define PHY_COPPER_CTRL_REG                        0
//PHY page 1
#define PHY_FIBER_CTRL_REG                         0
#define PHY_FIBER_STATUS_REG                       1
#define PHY_AN_ADV_REG                             4
#define PHY_LINK_PARTNER_ABILITY_REG               5
#define PHY_AN_EXPANSION_REG                       6
#define PHY_SPECIFIC_CTRL_REG                      16
#define PHY_SPECIFIC_STATUS_REG                    17
#define PHY_PRBS_CTRL_REG                          23
#define PHY_PRBS_ERROR_COUNTER_LSB_REG             24
#define PHY_PRBS_ERROR_COUNTER_MSB_REG             25
#define PHY_SPECIFIC_CTRL2_REG                     26
//PHY page 6
#define PHY_COPPER_CHECKER_CTRL_REG                18
//PHY page 18
#define PHY_PKT_GENERATOR_REG                      16
#define PHY_CRC_COUNTERS_REG                       17
#define PHY_CHECKER_CTRL_REG                       18
#define PHY_GEN_CTRL_REG                           20

//fields in PHY_COPPER_CTRL_REG
#define PHY_SYS_INTF_LOOPBACK_SHIFT                14

//fields in PHY_FIBER_CTRL_REG
#define PHY_SOFTWARE_RESET_SHIFT                   15
#define PHY_SOFTWARE_RESET_MASK                    0x1
#define PHY_SPEED_SELECT_LSB_SHIFT                 13
#define PHY_SPEED_SELECT_MSB_SHIFT                 6
#define PHY_AN_ENABLE_SHIFT                        12
#define PHY_AN_ENABLE_MASK                         0x1
#define PHY_DUPLEX_SHIFT                           8
#define PHY_DUPLEX_MASK                            0x1
#define PHY_DUPLEX_FULL                            0x1
#define PHY_AN_RESTART_SHIFT                       9
#define PHY_AN_RESTART_MASK                        0x1

//fields in PHY_FIBER_STATUS_REG
#define PHY_AN_COMPLETE_SHIFT                      5
#define PHY_AN_COMPLETE_MASK                       0x1
#define PHY_LINK_STATUS_SHIFT                      2
#define PHY_LINK_STATUS_MASK                       0x1

//fields in PHY_SPECIFIC_CTRL_REG
#define PHY_SPECIFIC_PHY_MODE_SHIFT                0
#define PHY_SPECIFIC_PHY_MODE_MASK                 0x3

//fields in PHY_SPECIFIC_STATUS_REG
#define PHY_SPECIFIC_SPEED_SHIFT                   14
#define PHY_SPECIFIC_SPEED_MASK                    0x3
#define PHY_SPECIFIC_DUPLEX_SHIFT                  13
#define PHY_SPECIFIC_DUPLEX_MASK                   0x1
#define PHY_SPECIFIC_SPEED_DUPLEX_RESOLVED_SHIFT   11
#define PHY_SPECIFIC_SPEED_DUPLEX_RESOLVED_MASK    0x1
#define PHY_SPECIFIC_LINK_RT_SHIFT                 10
#define PHY_SPECIFIC_LINK_RT_MASK                  0x1
#define PHY_SPECIFIC_RMT_FAULT_RCVD_SHIFT          6
#define PHY_SPECIFIC_RMT_FAULT_RCVD_MASK           0x3
#define PHY_SPECIFIC_SYNC_STATUS_SHIFT             5
#define PHY_SPECIFIC_SYNC_STATUS_MASK              0x1

//fields in PHY_PRBS_CTRL_REG
#define PHY_PRBS_PATTERN_MASK                      0x3
#define PHY_PRBS_PATTERN_SHIFT                     2
#define PHY_PRBS_PATTERN_7                         0x0
#define PHY_PRBS_PATTERN_23                        0x1
#define PHY_PRBS_PATTERN_31                        0x2
#define PHY_PRBS_CHECKER_EN                        0x2
#define PHY_PRBS_GENERATOR_EN                      0x1
#define PHY_PRBS_CLEAR_COUNTER_SHIFT               4
#define PHY_PRBS_TX_POLARITY_MASK                  0x1
#define PHY_PRBS_TX_POLARITY_SHIFT                 6
#define PHY_PRBS_RX_POLARITY_MASK                  0x1
#define PHY_PRBS_RX_POLARITY_SHIFT                 7
#define PHY_PRBS_LOCK_MASK                         0x1
#define PHY_PRBS_LOCK_SHIFT                        5

//fields in PHY_SPECIFIC_CTRL2_REG
#define PHY_AN_BYPASS_ENALBE_SHIFT                 6
#define PHY_AN_BYPASS_ENALBE_MASK                  0x1
#define PHY_AN_BYPASS_STATUS_SHIFT                 5
#define PHY_AN_BYPASS_STATUS_MASK                  0x1

#define PHY_AN_ADV_SPEED_SHIFT                     10
#define PHY_AN_ADV_SPEED_MASK                      0x3
#define PHY_AN_ADV_DUPLEX_SHIFT                    12
#define PHY_AN_ADV_DUPLEX_MASK                     0x1

//fields in PHY_COPPER_CHECKER_CTRL_REG
#define PHY_ENABLE_STUB_TEST_SHIFT                 3

//fields in PHY_CHECKER_CTRL_REG
#define CHECK_DATA_FROM_COPPER_INTERFACE           0x2
#define CRC_COUNTER_RESET_SHIFT                    4

//fields in PHY_CRC_COUNTERS_REG
#define PACKET_COUNTER_MASK                        0xFF
#define PACKET_COUNTER_SHIFT                       8
#define ERROR_COUNTER_MASK                         0xFF
#define ERROR_COUNTER_SHIFT                        0

//fields in PHY_PKT_GENERATOR_REG
#define GEN_PKT_FROM_COPPER_INTERFACE              (0x2 << 5 | 0x1 << 3)
#define PKT_BURST_MASK                             0xFF
#define PKT_BURST_SHIFT                            8
#define PKT_WITH_ERROR                             0x1
#define PKT_PAYLOAD_MASK                           0x1
#define PKT_PAYLOAD_SHIFT                          2
#define PKT_LENGTH_MASK                            0x1
#define PKT_LENGTH_SHIFT                           1

//fields in PHY_GEN_CTRL_REG
#define SERDES_MODE_MASK                           0x7
#define SGMII_TO_COPPER_MODE                       0x1

//xcvr registers
#define XCVR_CFG_CTRL_OFFSET                       0x14
#define XCVR_CFG_DBG_OFFSET                        0x28
#define XCVR_STA_OFFSET                            0x44
#define XCVR_CFG_DBG2_OFFSET                       0x2C
#define XCVR_STA_DBG_OFFSET                        0x68
#define XCVR_STA_DBG2_OFFSET                       0x6C

//fields in XCVR_CFG_DBG_OFFSET reg
#define RXBUF_RESET_MASK                           0x1
#define RXBUF_RESET_SHIFT                          5
#define RXPCS_RESET_MASK                           0x1
#define RXPCS_RESET_SHIFT                          11
#define RXPMA_RESET_MASK                           0x1
#define RXPMA_RESET_SHIFT                          12
#define RXPOLARITY_MASK                            0x1
#define RXPOLARITY_SHIFT                           13
#define RXPRBSCNT_RESET_MASK                       0x1
#define RXPRBSCNT_RESET_SHIFT                      14
#define RXPRBSSEL_MASK                             0x7
#define RXPRBSSEL_SHIFT                            15
#define XCVR_LOOPBACK_MASK                         0x7
#define XCVR_LOOPBACK_SHIFT                        2
#define XCVR_LOOPBACK_NEAREND_PMA                  0x2
#define TXPMA_RESET_MASK                           0x1
#define TXPMA_RESET_SHIFT                          24
#define TXPOLARITY_MASK                            0x1
#define TXPOLARITY_SHIFT                           25
#define TXPRBSFORCEERR_MASK                        0x1
#define TXPRBSFORCEERR_SHIFT                       31

#define XCVR_PRBS_7                                0x1
#define XCVR_PRBS_15                               0x2
#define XCVR_PRBS_23                               0x3
#define XCVR_PRBS_31                               0x4
#define RXPRBSSEL_MASK                             0x7
#define RXPRBSSEL_SHIFT                            15

#define XCVR_NEAR_END_PMA_LOOPBACK                 0x2
#define XCVR_FAR_END_PMA_LOOPBACK                  0x4

//fields in XCVR_CFG_DBG2_OFFSET reg
#define TXPRBSSEL_MASK                             0x7
#define TXPRBSSEL_SHIFT                            0

//fields in XCVR_CFG_CTRL_OFFSET reg
#define SW_RESET_SHIFT                             0
#define SW_RESET_MASK                              0x1
#define CFG_VECTOR_SHIFT                           1
#define CFG_VECTOR_MASK                            0x1f
#define SIG_DETECT_SHIFT                           6
#define SIG_DETECT_MASK                            0x1
#define AN_ADV_CONFIG_VECTOR_SHIFT                 7
#define AN_ADV_CONFIG_VECTOR_MASK                  0xFFFF
#define AN_RESTART_CONFIG_SHIFT                    23
#define AN_RESTART_CONFIG_MASK                     0x1

#define AN_ENABLE_SHIFT                            (4 + CFG_VECTOR_SHIFT)
#define AN_ENABLE_MASK                             0x1
#define AN_SPEED_SHIFT                             (10 + AN_ADV_CONFIG_VECTOR_SHIFT)
#define AN_SPEED_MASK                              0x3
#define AN_SPEED_1000M                             0x2
#define AN_DUPLEX_SHIFT                            (12 + AN_ADV_CONFIG_VECTOR_SHIFT)
#define AN_DUPLEX_MASK                             0x1
#define AN_DUPLEX_FULL                             0x1
#define AN_ACK_SHIFT                               (14 + AN_ADV_CONFIG_VECTOR_SHIFT)
#define AN_ACK_MASK                                0x1
#define AN_LINK_STATUS_SHIFT                       (15 + AN_ADV_CONFIG_VECTOR_SHIFT)
#define AN_LINK_STATUS_MASK                        0x1

//fields in XCVR_STA_OFFSET reg
#define STATUS_VECTOR_SHIFT                        5
#define STATUS_VECTOR_MASK                         0xFFFF
#define LINK_STATUS_SHIFT                          (0 + STATUS_VECTOR_SHIFT)
#define LINK_STATUS_MASK                           0x1
#define LINK_SYNC_SHIFT                            (1 + STATUS_VECTOR_SHIFT)
#define LINK_SYNC_MASK                             0x1
#define SGMII_PHY_LINK_STATUS_SHIFT                (7 + STATUS_VECTOR_SHIFT)
#define SGMII_PHY_LINK_STATUS_MASK                 0x1
#define SPEED_SHIFT                                (10 + STATUS_VECTOR_SHIFT)
#define SPEED_MASK                                 0x3
#define DUPLEX_MODE_SHIFT                          (12 + STATUS_VECTOR_SHIFT)
#define DUPLEX_MODE_MASK                           0x1

//fields in XCVR_STA_DBG2_OFFSET
#define RX_RESET_DONE_MASK                         0x1

//PRBS cmd options
#define PRBS_GEN_START                             1
#define PRBS_GEN_STOP                              2
#define PRBS_CHECKER_START                         3
#define PRBS_CHECKER_STOP                          4
#define PRBS_ERR_READ                              5
#define PRBS_ERR_CLEAR                             6
#define AN_ENABLE                                  7
#define AN_DISABLE                                 8
#define DUMP_STATUS_ONLY                           9
#define CONFIG_PHY_SYS_INTF_LOOPBACK               10
#define CONFIG_PHY_STUB_TEST                       11
#define CONFIG_NEAREND_PMA_LOOPBACK                12
#define CONFIG_FAREND_PMA_LOOPBACK                 13
#define CONFIG_PHY_PKT_CHECKER                     14
#define CONFIG_PHY_PKT_GENERATOR                   15
#define PHY_PKT_CHECKER_READ_COUNTER               16
#define AN_ON_PHY_COPPER_ENABLE                    17
#define CONFIG_PHY_MODE                            18

#define PRBS_DEV_XCVR                              0
#define PRBS_DEV_PHY                               1

#define ENABLE                          1
#define DISABLE                         0

#define DEBUG                           DISABLE
//#define DEBUG                           ENABLE

// 5MHz
#define ELBA_SPI_CLK                    5000000

#define MIN(a,b)                        ((a>b)? b : a)

static int ps48_write_pipeline_test(uint32_t fd, uint32_t numByte);
static int flash_write_page_test(uint32_t fd, uint32_t addr);

static int _e_ioctl(int fd, const char *name, unsigned long req, void *arg)
{
    int r = ioctl(fd, req, arg);
    if (r < 0) {
        perror(name);
        exit(1);
    }
    return r;
}
#define e_ioctl(fd, req, arg)       _e_ioctl(fd, #req, req, arg)

static int e_open(const char *path, int flags, int mode)
{
    int fd = open(path, flags, mode);
    if (fd < 0) {
        perror(path);
        exit(1);
    }
    return fd;
}


void disp_buf(char *buf, uint32_t numByte) {
    for (int i = 0; i < numByte; i++) {
        printf("%02x ", *(buf+i));
        if (((i+1) % 16) == 0) {
            printf("\n");
        }
    }
    printf("\n");
}

// copied from xo3dcpld.c: fpga_cs0_read() and fpga_cs0_write()
static int fpga_cs0_read(uint8_t addr)
{
    struct spi_ioc_transfer msg[2];
    uint8_t txbuf[4];
    uint8_t rxbuf[1];
    int fd;

    txbuf[0] = 0x0b;
    txbuf[1] = addr;
    txbuf[2] = 0x00;
    rxbuf[0] = 0x00;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 3;
    /* msg[0].speed_hz = 12000000; */
    msg[0].speed_hz = 5000000;
    msg[1].rx_buf = (intptr_t)rxbuf;
    msg[1].len = 1;

    fd = e_open(spidev_path0, O_RDWR, 0);
    e_ioctl(fd, SPI_IOC_MESSAGE(2), msg);
    close(fd);

    return rxbuf[0];
}

static int fpga_cs0_write(uint8_t addr, uint8_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[3];
    int fd, status;

    txbuf[0] = 0x02;
    txbuf[1] = addr;
    txbuf[2] = data;
    txbuf[3] = 0x00;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 4;
    /* msg[0].speed_hz = 12000000; */
    msg[0].speed_hz = 5000000;

    fd = e_open(spidev_path0, O_RDWR, 0);
    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    close(fd);
    return 0;
}

// copied from xo3dcpld.c: mdio_rd() and mdio_wr()
static int mdio_rd(uint8_t addr, uint16_t* data, uint8_t phy)
{
	uint8_t data_lo, data_hi;
	fpga_cs0_write(MDIO_CRTL_HI_REG, addr);
	fpga_cs0_write(MDIO_CRTL_LO_REG, (phy << 3) | MDIO_RD_ENA | MDIO_ACC_ENA);
	usleep(1000);
	fpga_cs0_write(MDIO_CRTL_LO_REG, 0);
	usleep(1000);
	data_lo = fpga_cs0_read(MDIO_DATA_LO_REG);
	data_hi = fpga_cs0_read(MDIO_DATA_HI_REG);
	*data = (data_hi << 8) | data_lo;

	return 0;
}

static int mdio_wr(uint8_t addr, uint16_t data, uint8_t phy)
{
	fpga_cs0_write(MDIO_CRTL_HI_REG, addr);
	fpga_cs0_write(MDIO_DATA_LO_REG, (data & 0xFF));
	fpga_cs0_write(MDIO_DATA_HI_REG, ((data >> 8) & 0xFF));
	fpga_cs0_write(MDIO_CRTL_LO_REG, (phy << 3) | MDIO_WR_ENA | MDIO_ACC_ENA);
	usleep(1000);
	fpga_cs0_write(MDIO_CRTL_LO_REG, 0);

	return 0;
}

// This function sends a sync command to PS-48 interface.

static int ps48_sync(uint32_t fd)
{ 
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];    
 
    txbuf[0] = 0x2a;
    txbuf[1] = 0x55;
    txbuf[2] = 0x95;
    txbuf[3] = 0xaa;
    txbuf[4] = 0x56;
    txbuf[5] = 0x94;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
 
    return 0;
}

// This function processes the response frame received from PS-48 interface.


// This function configure 4 pages in PS-48 interface.

static int ps48_page_config(uint32_t fd, uint8_t pageConfig)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6], val;
    //aid=0, bid=1, page 0 addr=0x2000000 (flash), page 1 addr=0x1001000 (switch)
    if(pageConfig == FLASH_AND_SWITCH_PAGE_CONFIG)
    {
        // Page 0: Flash
        // Page 1: MES Reg
        txbuf[0] = 0xc4;
        txbuf[1] = 0x02;
        txbuf[2] = 0x00;
        txbuf[3] = 0x00;
        txbuf[4] = 0x10;
        txbuf[5] = 0x01;
    }
    //aid=3, bid=2, page 3 addr=0x0 (NCSI), page 2 addr=0x1005000 (BMC)
    else if(pageConfig == NCSI_AND_BMC_PAGE_CONFIG)
    {
        // Page 2: MAC Reg
        // Page 3: NCSI
        txbuf[0] = 0xf8;
        txbuf[1] = 0x00;
        txbuf[2] = 0x00;
        txbuf[3] = 0x00;
        txbuf[4] = 0x10;
        txbuf[5] = 0x05;
    }
    //aid=2, bid=3, page 3 addr=0x1008000 (serdes xcvr), page 2 addr=0x100c000 (pc)
    else if(pageConfig == PC_AND_SERDES_PAGE_CONFIG)
    {
        // Page 2: PC/iCAPE
        // Page 3: Serdes
        txbuf[0] = 0xEC;
        txbuf[1] = 0x01;
        txbuf[2] = 0x00;
        txbuf[3] = 0xC0;
        txbuf[4] = 0x10;
        txbuf[5] = 0x08;
    }
    else 
    {
        txbuf[0] = 0xf8;
        txbuf[1] = 0x01;
        txbuf[2] = 0x00;
        txbuf[3] = 0x80;
        txbuf[4] = 0x10;
        txbuf[5] = 0x0c;
    }

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

    return 0;
}

static int ps48_init(uint32_t fd) {
    ps48_sync(fd);
    // 4 pages in total
    ps48_page_config(fd, FLASH_AND_SWITCH_PAGE_CONFIG);
    ps48_page_config(fd, PC_AND_SERDES_PAGE_CONFIG);

    return 0;
}

static int ps48_resp(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    uint8_t rxbuf[6];
    int ret;
    uint32_t val;
    int ite = 0;
    int num_ite = 5;


    while(1) {
        // Use NOOP on tx
        memset(txbuf, 0, 6);
        txbuf[5] = 0x7F;

        memset(rxbuf, 0, 6);
        memset(msg, 0, sizeof (msg));

        msg[0].tx_buf = (intptr_t)txbuf;
        msg[0].rx_buf = (intptr_t)rxbuf;
        msg[0].len = 6;
        msg[0].speed_hz = ELBA_SPI_CLK;

        ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

        if (ret < 1) {
            printf("ps48-resp: ioctl failed!\n");
            return -1;
        }

        if ((rxbuf[0] & 0xC0) != 0) {
            break;
        }

        ite++;
        if (ite >= num_ite) {
            printf("PS48-RESP: Buffer empty\n");
            return -1;
        }
    }

#if (DEBUG == ENABLE)    
    printf("ps48-resp: rxbuf\n");
    disp_buf(rxbuf, PS48_FRAME_SIZE);
#endif

    val = (rxbuf[2] << 24) | (rxbuf[3] << 16) | (rxbuf[4] << 8) | rxbuf[5];
    //printf("val: 0x%x\n", val);
    return val;
}

static int ps48_clean_resp(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    uint8_t rxbuf[6];
    int ret;
    uint32_t val;
    int max_try = 5;

    for (int i = 0; i < max_try; i++) {
        // Use NOOP on tx
        memset(txbuf, 0, 6);
        txbuf[5] = 0x7F;

        memset(rxbuf, 0, 6);
        memset(msg, 0, sizeof (msg));

        msg[0].tx_buf = (intptr_t)txbuf;
        msg[0].rx_buf = (intptr_t)rxbuf;
        msg[0].len = 6;
        msg[0].speed_hz = ELBA_SPI_CLK;

        ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);

        if (ret < 1) {
            return -1;
        }
    }

    printf("PS48 FIFO cleared\n");
    return ret;
}

static int ps48_write(uint32_t fd, uint32_t page_id, uint32_t addr, uint32_t data)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[18];    
    uint8_t rxbuf[18];    
    uint8_t *temp;
    int ret;

    temp = (uint8_t *)(&data);
    memset(rxbuf, 0, 18);

    txbuf[0] = 0x40 | ((page_id & 0x3) << 4) | ((addr & 0xF00) >> 8);//high 4 bits of addr
    txbuf[1] = addr & 0xFF;//lower 8 bits of addr
    txbuf[5] = *temp++;
    txbuf[4] = *temp++;
    txbuf[3] = *temp++;
    txbuf[2] = *temp;  
    // Noop 
    txbuf[6]  = 0x00;
    txbuf[7]  = 0x00;
    txbuf[8]  = 0x00;
    txbuf[9]  = 0x00;
    txbuf[10] = 0x00;
    txbuf[11] = 0x7F;

    txbuf[12]  = 0x00;
    txbuf[13]  = 0x00;
    txbuf[14]  = 0x00;
    txbuf[15]  = 0x00;
    txbuf[16] = 0x00;
    txbuf[17] = 0x7F;

#if (DEBUG == ENABLE)    
    printf("ps48-write: txbuf\n");
    disp_buf(txbuf, 18);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = 18;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    }    

#if (DEBUG == ENABLE)    
    printf("ps48-write: rxbuf\n");
    disp_buf(rxbuf, 18);
#endif

    // Check write response
    ret = -1;
    for (int i = 0; i < 3; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            ret = 0;
        }
    }

    // If no resp received, check one more time
    if (ret == -1) {
        ret = ps48_resp(fd);
    }
    return ret;

}

/*
 * Should only be used for Flash controller Data transmit register
 */
static int ps48_write_pipeline(uint32_t fd, uint32_t page_id, uint32_t addr, uint8_t *buf, uint32_t numByte)
{
    struct spi_ioc_transfer msg[1];
    int ret = 1;
    int f_trans_w = FLASH_TRANSFER_WIDTH_B;
    uint8_t *txbuf;
    uint8_t *txbuf_1;
    uint8_t *rxbuf;
    uint8_t *rxbuf_1;
    uint32_t ovHead = 2;
    uint32_t revByte = 0;
    int val = 0;

    if (f_trans_w == FLASH_TRANSFER_WIDTH_B) {
        txbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
        rxbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
    }

    memset(txbuf, 0, (numByte+ovHead)*6);
    memset(rxbuf, 0, (numByte+ovHead)*6);
 
    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        txbuf[i*6+5] = 0x7F;
        rxbuf[i*6+5] = 0x7F;
    }

    for (int i = 0; i < numByte; i++) {
        txbuf[i*6+0] = 0x40 | ((uint8_t)(page_id & 3));
        txbuf[i*6+1] = addr;
        txbuf[i*6+2] = 0x00;
        txbuf[i*6+3] = 0x00;
        txbuf[i*6+4] = 0x00;
        txbuf[i*6+5] = buf[i];
    } 
    
#if (DEBUG == ENABLE)    
    printf("ps48-write_pipeline: txbuf\n");
    disp_buf(txbuf, numByte * 6);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = (numByte+ovHead)*6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        ret = -1;
    } else {
        ret = 0;
    }
    
#if (DEBUG == ENABLE)    
    printf("ps48-write_pipeline: rxbuf\n");
    disp_buf(rxbuf, (numByte+ovHead) * 6);
#endif

    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            revByte += rxbuf[i*6+5];
        }
    }

    // If not all responses received, keep checking
    if (revByte != numByte) {
        printf("Checking more WR RESP\n");
        while(1) {
            val = ps48_resp(fd);
            if (val != -1) {
                revByte += val;
            }
            else {
                break;
            }
        }
    }

    if (revByte != numByte) {
        printf("ps48_write_pipeline failed: expect numbyte: %d; received numByte: %d\n", numByte, revByte);
        ret = -1;
    }

    free(txbuf);
    free(rxbuf);
    return ret;
}

static int ps48_read(uint32_t fd, uint32_t page_id, uint32_t addr)
{
    struct spi_ioc_transfer msg[1];
    int buf_size_in_frame = 3;
    int buf_size = PS48_FRAME_SIZE * buf_size_in_frame;
    uint8_t txbuf[18];
    uint8_t rxbuf[18];
    uint8_t *temp;
    int ret;
    uint32_t addr_base;
    uint32_t addr_f;

    page_id = page_id & 3;
    switch (page_id)
    {
        case 0x00:
            addr_base = FPGA_BASE_ADDR_QSPI_CTRL;
            break;
        case 0x01:
            addr_base = FPGA_BASE_ADDR_MES_REG;
            break;
        case 0x02:
            addr_base = FPGA_BASE_ADDR_PC;
            break;
        default:
            addr_base = FPGA_BASE_ADDR_SERDES;
            break;
    }
    addr_f = addr_base + addr;
    //printf("%s: addr_f=0x%x\n", __FUNCTION__, addr_f);

    temp = (uint8_t *)(&addr_f);

    txbuf[0] = 0x80 | ((uint8_t)(page_id & 3));
    txbuf[1] = 0x00;
    txbuf[5] = *temp++;
    txbuf[4] = *temp++;
    txbuf[3] = *temp++;
    txbuf[2] = *temp;
    // Noop 
    txbuf[6]  = 0x00;
    txbuf[7]  = 0x00;
    txbuf[8]  = 0x00;
    txbuf[9]  = 0x00;
    txbuf[10] = 0x00;
    txbuf[11] = 0x7F;

    txbuf[12]  = 0x00;
    txbuf[13]  = 0x00;
    txbuf[14]  = 0x00;
    txbuf[15]  = 0x00;
    txbuf[16] = 0x00;
    txbuf[17] = 0x7F;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = buf_size;
    msg[0].speed_hz = ELBA_SPI_CLK;

#if (DEBUG == ENABLE)    
    printf("ps48-read: txbuf\n");
    disp_buf(txbuf, buf_size);
#endif

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    }

#if (DEBUG == ENABLE)    
    printf("ps48-read: rxbuf\n");
    disp_buf(rxbuf, buf_size);
#endif

    // Check write response
    ret = -1;
    for (int i = 0; i < buf_size_in_frame; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            ret = (rxbuf[i*6+2] << 24) | (rxbuf[i*6+3] << 16) | (rxbuf[i*6+4] << 8) | rxbuf[i*6+5];
            break;
        }
    }

    // If no resp received, check one more time
    if (ret == -1) {
        ret = ps48_resp(fd);
    }
    return ret;

}

/*
 * Should only be used for Flash controller data receive register
 */
static int ps48_read_pipeline(uint32_t fd, uint32_t page_id, uint32_t addr, uint8_t *buf, uint32_t numByte)
{
    struct spi_ioc_transfer msg[1];
    int ret = 1;
    int f_trans_w = FLASH_TRANSFER_WIDTH_B;
    uint8_t *txbuf;
    uint8_t *txbuf_1;
    uint8_t *rxbuf;
    uint8_t *rxbuf_1;
    uint32_t ovHead = 3;
    uint32_t revByte = 0;
    int val = 0;
    uint32_t bufIdx = 0;
    uint8_t *tmpPtr;
    uint32_t addr_f;
    //addr_f = addr + FPGA_BASE_ADDR_QSPI_CTRL;

    //tmpPtr = (uint8_t *)(&addr_f);
    uint32_t addr_base;

    switch (page_id & 0x3)
    {
        case 0x00:
            addr_base = FPGA_BASE_ADDR_QSPI_CTRL;
            break;
        case 0x01:
            addr_base = FPGA_BASE_ADDR_MES_REG;
            break;
        case 0x02:
            addr_base = FPGA_BASE_ADDR_PC;
            break;
        default:
            addr_base = FPGA_BASE_ADDR_SERDES;
            break;
    }
    addr_f = addr_base + addr;
    //printf("%s: addr_f=0x%x\n", __FUNCTION__, addr_f);

    tmpPtr = (uint8_t *)(&addr_f);

    if (f_trans_w == FLASH_TRANSFER_WIDTH_B) {
        txbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
        rxbuf = (uint8_t *) malloc((numByte+ovHead) * 6);
    }
    memset(txbuf, 0, (numByte+ovHead)*6);
    memset(rxbuf, 0, (numByte+ovHead)*6);
 
    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        txbuf[i*6+5] = 0x7F;
        rxbuf[i*6+5] = 0x7F;
    }
   
#if (DEBUG == ENABLE)    
    printf("%s 00: txbuf\n", __func__);
    disp_buf(txbuf, (numByte+ovHead) * 6);
#endif

    for (int i = 0; i < numByte; i++) {
        txbuf[i*6+0] = 0x80 | ((uint8_t)(page_id & 3));
        txbuf[i*6+1] = 0;
        txbuf[i*6+2] = tmpPtr[3];
        txbuf[i*6+3] = tmpPtr[2];
        txbuf[i*6+4] = tmpPtr[1];
        txbuf[i*6+5] = tmpPtr[0];
    } 
    
#if (DEBUG == ENABLE)    
    printf("ps48_rx_pipeline: txbuf\n");
    disp_buf(txbuf, (numByte+ovHead) * 6);
#endif

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].rx_buf = (intptr_t)rxbuf;
    msg[0].len = (numByte+ovHead)*6;
    msg[0].speed_hz = ELBA_SPI_CLK;

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        ret = -1;
    } else {
        ret = 0;
    }
    
#if (DEBUG == ENABLE)    
    printf("ps48_rx_pipeline: rxbuf\n");
    disp_buf(rxbuf, (numByte+ovHead) * 6);
#endif

    // Check write response
    for (int i = 0; i < numByte+ovHead; i++) {
        if ((rxbuf[i*6] & 0xC0) != 0) {
            buf[bufIdx] = rxbuf[i*6+5];
            bufIdx++;
        }
    }

    // If not all responses received, keep checking
    while(bufIdx < numByte) {
        val = ps48_resp(fd);
        if (val != -1) {
            buf[bufIdx] = val & 0xFF;
        }
        else {
            break;
        }
        bufIdx++;
    }

    if (bufIdx != numByte) {
        printf("ps48_read_pipeline failed: expect numbyte: %d; received numByte: %d\n", numByte, bufIdx);
        ret = -1;
    }

    free(txbuf);
    free(rxbuf);
    return ret;
}

static int ps48_noop(uint32_t fd)
{
    struct spi_ioc_transfer msg[1];
    uint8_t txbuf[6];
    int ret;

    txbuf[0] = 0x00;
    txbuf[1] = 0x00;
    txbuf[2] = 0x00;
    txbuf[3] = 0x00;
    txbuf[4] = 0x00;
    txbuf[5] = 0x7F;

    memset(msg, 0, sizeof (msg));
    msg[0].tx_buf = (intptr_t)txbuf;
    msg[0].len = 6;
    msg[0].speed_hz = ELBA_SPI_CLK;

#if (DEBUG == ENABLE)    
    printf("ps48-noop: txbuf\n");
    disp_buf(txbuf, PS48_FRAME_SIZE);
#endif

    ret = e_ioctl(fd, SPI_IOC_MESSAGE(1), msg);
    if (ret < 1) {
        return -1;
    } else {
        return 0;
    }
}

static int ps48_qspi_ctrl_read(uint32_t fd, uint32_t addr)
{
    uint32_t addr_f;
    int ret;
    //addr_f = addr + FPGA_BASE_ADDR_QSPI_CTRL;
    ret = ps48_read(fd, PAGE_ID_FLASH, addr);
    if (ret == -1) {
        return ret;
    }

    //return ps48_resp(fd);
    return ret;
}

static int ps48_qspi_ctrl_write(uint32_t fd, uint32_t addr, uint32_t data)
{
    uint32_t addr_f;
    int ret;
    ret = ps48_write(fd, PAGE_ID_FLASH, addr, data);
    if (ret == -1) {
        return ret;
    }
    return ret;

    //ret = ps48_noop(fd);
    //if (ret == -1) {
    //    return ret;
    //}

    //return ps48_resp(fd);
}

/*
 * flash_write uses 4B address. Make sure 4B mode is enabled
 */ 
static int flash_write(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_PAGE_PROG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    for (int i = 0; i < numByte; i++) {
        ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(buf+i));
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    return ret;
}

/*
 * flash_write uses 4B address. Make sure 4B mode is enabled
 */ 
static int flash_write_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);
    uint32_t remainByte = numByte;
    uint32_t transByte;
    uint8_t *transBuf = buf;

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_PAGE_PROG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        ps48_write_pipeline(fd, PAGE_ID_FLASH, SPI_DATA_TRANSMIT_REG, transBuf, transByte);
        //ps48_clean_resp(fd);

        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    return ret;
}

static int flash_read(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_ADDR4B);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    for (int i = 0; i < numByte; i++) {
        ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, 0);
    }

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    for (int i = 0; i < (numByte+5); i++) {
        *(buf+i) = ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);
    }

    return ret;
}

static int flash_read_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf, uint32_t numByte) {
    uint8_t ret = 0;
    uint8_t *temp;
    uint8_t *transBufBase;
    uint8_t *transBuf;
    uint32_t transByte;
    uint32_t rdOvHead = 5;
    uint32_t remainByte = numByte;

    temp = (uint8_t *)(&addr);
    transBufBase = (uint8_t *) malloc(numByte);
    transBuf = transBufBase;

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    //printf("Writing flash read command\n");
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_ADDR4B);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    //printf("Flushing 0s' to pop read data\n");
    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        ps48_write_pipeline(fd, PAGE_ID_FLASH, SPI_DATA_TRANSMIT_REG, transBuf, transByte);
        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    }
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
    free(transBufBase);

    transBufBase = (uint8_t *) malloc(numByte + rdOvHead);
    transBuf = transBufBase;
    remainByte = numByte + rdOvHead;
    //printf("Reading flash data\n");
    while(1) { 
        transByte = MIN(remainByte, PS48_PIPELINE_SIZE);
        //printf("transByte: 0x%x\n", transByte);
        ps48_read_pipeline(fd, PAGE_ID_FLASH, SPI_DATA_RECEIVE_REG, transBuf, transByte);
        if (remainByte <= PS48_PIPELINE_SIZE) {
            break;
        }
        transBuf += transByte;
        remainByte -= transByte;
    
        //ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
        //ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
    }

    memcpy(buf, transBufBase+rdOvHead, numByte); 
    free(transBufBase);

    return ret;
}

/*
 * This API is only to read one page. it will be slow to read actual image
 */
static int flash_read_page(uint32_t fd, uint32_t addr) {
    uint8_t ret = 0;
    uint8_t *buf = (uint8_t *)malloc(FLASH_PAGE_SIZE+5);

    ret = flash_read(fd, addr, buf, FLASH_PAGE_SIZE);
    disp_buf(buf+5, FLASH_PAGE_SIZE);

    free(buf);
    return ret;

}

static int flash_read_page_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf) {
    uint8_t ret = 0;

    ret = flash_read_pipeline(fd, addr, buf, FLASH_PAGE_SIZE);

    return ret;
}

/*
 * Read Status Register 
 */
static uint8_t flash_rdsr(uint32_t fd) {
    uint8_t val; 

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_READ_STATUS_REG);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, 0);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);
    val = ps48_qspi_ctrl_read(fd, SPI_DATA_RECEIVE_REG);

    return val;
}

static int flash_wr_ena(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_WRITE_ENABLE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

static int flash_wr_dis(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_WRITE_DISABLE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

static int flash_ena_4B_addr(uint32_t fd) {
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_ENTER_4_BYTE_MODE);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);
}

/*
 * Block erase uses 4B addressing. Make sure 4B addr is enabled
 */
static int flash_block_erase(uint32_t fd, uint32_t addr) {
    uint8_t *temp;
    temp = (uint8_t *)(&addr);

    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);
    
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, FLASH_BLOCK_ERASE_64K);
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+3));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+2));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *(temp+1));
    ps48_qspi_ctrl_write(fd, SPI_DATA_TRANSMIT_REG, *temp);

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x86);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

}

static int flash_block_erase_top(uint32_t fd, uint32_t addr) {
    uint8_t val;
    int retry = 0;
    flash_block_erase(fd, addr);

    // 2s max from spec
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(200*1000);
        retry++;
    }

    if (retry == 20) {
        printf("Block erase timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);
    return 0;
}

/*
 * flash_write_page
 * buf should have FLASH_PAGE_SIZE allocated
 */
static int flash_write_page(uint32_t fd, uint32_t addr, uint8_t *buf) {
    int retry;
    uint8_t val;

    flash_write(fd, addr, buf, FLASH_PAGE_SIZE);

    // 0.25-0.75 ms program time
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(100);
        retry++;
    }

    if (retry == 20) {
        printf("Write page timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);

    return 0;

}

static int flash_write_page_pipeline(uint32_t fd, uint32_t addr, uint8_t *buf) {
    int retry;
    uint8_t val;

    flash_write_pipeline(fd, addr, buf, FLASH_PAGE_SIZE);

    // 0.25-0.75 ms program time
    while(retry < 20) {
        val = flash_rdsr(fd);
        if ( (val & 1) == 0 ) {
            break;
        }
        usleep(100);
        retry++;
    }

    if (retry == 20) {
        printf("Write page timeout!\n");
        return -1;
    }
    //printf("retry: %d\n", retry);

    return 0;

}

static int flash_erase(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t blockSize = 0x10000;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    // Read image data to buffer
    fp = fopen(fn, "rb");
    if ( fp == NULL )
    {
        printf("Fail to open file %s\n", fn);
        return -1;
    }
    fseek(fp, 0L, SEEK_END);
    fileSize = ftell(fp);

    bufSize = ((fileSize + (FLASH_PAGE_SIZE -1)) / FLASH_PAGE_SIZE) * FLASH_PAGE_SIZE;
    fclose(fp);


    fd = e_open(spidev_path1, O_RDWR, 0);

    //ps48_init(fd);
    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    close(fd);

    fd = e_open(spidev_path1, O_RDWR, 0);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    flash_ena_4B_addr(fd);

    // Block erase
    printf("Erasing blocks\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Erasing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Erasing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_block_erase_top(fd, cur_addr);
        cur_addr += blockSize;
        if (cur_addr >= end_addr) {
            break;
        }
    }
    flash_wr_dis(fd);

    close(fd);
}


static int flash_prog(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t blockSize = 0x10000;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    // Read image data to buffer
    fp = fopen(fn, "rb");
    if ( fp == NULL )
    {
        printf("Fail to open file %s\n", fn);
        return -1;
    }
    fseek(fp, 0L, SEEK_END);
    fileSize = ftell(fp);
    fseek(fp, 0L, SEEK_SET);

    bufSize = ((fileSize + (FLASH_PAGE_SIZE -1)) / FLASH_PAGE_SIZE) * FLASH_PAGE_SIZE;
    printf("fileSize = 0x%x, bufSize = 0x%x\n", fileSize, bufSize);
    buf = (uint8_t *) malloc(bufSize);
    memset(buf, 0xff, bufSize);

    if (fread(buf, sizeof(*buf), fileSize, fp) != fileSize) {
        printf("Failed to read file\n");
        free(buf);
        fclose(fp);
        return -1;
    }
    fclose(fp);

    // Some wired WA. Otherwise first erase will not happen
    fd = e_open(spidev_path1, O_RDWR, 0);
    ps48_init(fd);
    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    close(fd);

    fd = e_open(spidev_path1, O_RDWR, 0);
    flash_wr_ena(fd);
    flash_wr_dis(fd);
    flash_ena_4B_addr(fd);

    // Block erase
    printf("Erasing blocks\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Erasing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Erasing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_block_erase_top(fd, cur_addr);
        cur_addr += blockSize;
        if (cur_addr >= end_addr) {
            break;
        }
    }

    // Write date to flash
    printf("Programming image\n");
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    buf_index = 0;

    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Writing 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Writing 0x%x\n", cur_addr);
        }

        flash_wr_ena(fd);
        ret = flash_write_page_pipeline(fd, cur_addr, (buf+buf_index));
        cur_addr += FLASH_PAGE_SIZE;
        buf_index += FLASH_PAGE_SIZE;
        if (cur_addr >= end_addr) {
            break;
        }
    }
    flash_wr_dis(fd);

    free(buf);
    close(fd);
}

static int flash_read_to_file(char* fn, char* imageType) {
    FILE* fp;
    int fileSize;

    uint32_t fd;

    uint32_t flash_base_addr;
    uint32_t cur_addr;
    uint32_t end_addr;

    int bufSize;
    uint8_t *buf;
    int buf_index;

    int ret;

    printf("fn: %s, imageType: %s\n", fn, imageType);

    if (strcmp(imageType, "main") == 0) {
        printf("main image; base: 0x%x\n", FLASH_OFFSET_MAIN);
        flash_base_addr = FLASH_OFFSET_MAIN;
        bufSize = 0x1000000;
        bufSize = 0x300000;
    }
    else if (strcmp(imageType, "gold") == 0) {
        printf("gold image; base: 0x%x\n", FLASH_OFFSET_GOLD);
        flash_base_addr = FLASH_OFFSET_GOLD;
        bufSize = 0x1000000;
        //bufSize = 0x3B0000;
    }
    else if (strcmp(imageType, "test") == 0) {
        printf("test image; base: 0x%x\n", FLASH_OFFSET_TEST);
        flash_base_addr = FLASH_OFFSET_TEST;
        bufSize = 0x200;
    } 
    else {
        printf("Invalid image type: %s\n", imageType);
        return -1;
    }

    buf = (uint8_t *) malloc(bufSize);

    fd = e_open(spidev_path1, O_RDWR, 0);

    ps48_init(fd);
    flash_ena_4B_addr(fd);

    // Read data from flash
    printf("Reading flash data from offset 0x%x of 0x%x number of bytes\n", flash_base_addr, bufSize);
    cur_addr = flash_base_addr;
    end_addr = flash_base_addr + bufSize;
    buf_index = 0;

    while(1) {
        if (flash_base_addr != FLASH_OFFSET_TEST) {
            if ( (cur_addr % 0x100000) == 0 ) {
                printf("Reading 0x%x\n", cur_addr);
            }
        }
        else {
            printf("Reading 0x%x\n", cur_addr);
        }

        ret = flash_read_page_pipeline(fd, cur_addr, (buf+buf_index));
        cur_addr += FLASH_PAGE_SIZE;
        buf_index += FLASH_PAGE_SIZE;
        if (cur_addr >= end_addr) {
            break;
        }
    }

    //printf("flash_read buf: \n");
    //disp_buf(buf, bufSize);

    // Write to file
    FILE *write_ptr;
    fp = fopen(fn,"wb");
    fwrite(buf, bufSize, 1, fp);
    fclose(fp);

    free(buf);
    close(fd);
}

static int flash_write_page_test(uint32_t fd, uint32_t addr) {
    uint8_t * buf;
    uint8_t val_sr;

    buf = (uint8_t *)malloc(FLASH_PAGE_SIZE);

    for (int i = 0; i < FLASH_PAGE_SIZE; i++) {
        *(buf+i) = (uint8_t) i;
    }

    flash_ena_4B_addr(fd);
    flash_wr_ena(fd);

    val_sr = flash_rdsr(fd);
    printf("SR: 0x%x\n", val_sr);

    flash_write_page_pipeline(fd, addr, buf);
    flash_wr_dis(fd);

    printf("Write Bufer:\n");
    disp_buf(buf, FLASH_PAGE_SIZE);

    free(buf);
    return 0;
}

static int ps48_write_pipeline_test(uint32_t fd, uint32_t numByte) {
    uint8_t *buf;

    buf = (uint8_t *)malloc(numByte);
    for (int i = 0; i < numByte; i++) {
        *(buf+i) = (uint8_t) i;
    }
    disp_buf(buf, numByte);

    // Reset FIFO pointer    
    ps48_qspi_ctrl_write(fd, SPI_SOFT_RESET_REG, 0xa);
    ps48_qspi_ctrl_write(fd, SPI_SLAVE_SEL_REG, 0x0);

    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x1E6);
    ps48_qspi_ctrl_write(fd, SPI_CONTROL_REG, 0x186);

    ps48_write_pipeline(fd, PAGE_ID_FLASH, SPI_DATA_TRANSMIT_REG, buf, numByte);

    free(buf);
    return 0;

}

static int flash_read_pipeline_test(uint32_t fd, uint32_t addr, uint32_t numByte) {
    uint8_t *buf;

    buf = (uint8_t *)malloc(numByte);

    flash_read_pipeline(fd, addr, buf, numByte);

    disp_buf(buf, numByte);

    free(buf);
    return 0;
}

uint8_t bit_swap_byte(uint8_t input_byte) {
    uint8_t output_byte = 0;
    for(int i = 0; i < 8; i++) {
        output_byte |= ((input_byte >> i) & 1) << (7-i);
        //printf("i=%d; input_byte=0x%x; output_byte=0x%x\n", i, input_byte, output_byte);
    }
    return output_byte;

}

void fpga_reload(void) {
    uint32_t fd;
    uint8_t *buf;
    uint32_t data;

    // FPGA reload sequence
    //uint8_t reload_dummy[]        = {0xFF, 0xFF, 0xFF, 0xFF};
    //uint8_t reload_sync[]         = {0xAA, 0x99, 0x55, 0x66};
    //uint8_t reload_t1_noop[]      = {0x20, 0x00, 0x00, 0x00};
    //uint8_t reload_t1_w1_wbstar[] = {0x30, 0x02, 0x00, 0x01};
    //uint8_t reload_boot_addr[]    = {0x00, 0x00, 0x00, 0x00};
    //uint8_t reload_w1_cmd[]       = {0x30, 0x00, 0x80, 0x01};
    //uint8_t reload_iprog[]        = {0x00, 0x00, 0x00, 0x0F};
    //uint8_t reload_t1_noop[]      = {0x20, 0x00, 0x00, 0x00};
    uint8_t reload_seq[] = { 
    0xFF, 0xFF, 0xFF, 0xFF,
    0xAA, 0x99, 0x55, 0x66,
    0x20, 0x00, 0x00, 0x00,
    0x30, 0x02, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x00,
    0x30, 0x00, 0x80, 0x01,
    0x00, 0x00, 0x00, 0x0F,
    0x20, 0x00, 0x00, 0x00,
    };

    uint8_t *bit_swap_buf = malloc(sizeof(reload_seq));
    for(int i = 0; i < sizeof(reload_seq); i++) {
        bit_swap_buf[i] = bit_swap_byte(reload_seq[i]);
    }
    disp_buf(bit_swap_buf, sizeof(reload_seq));

    fd = e_open(spidev_path1, O_RDWR, 0);
    ps48_init(fd);

    for (int i = 0; i < 8; i++) {
        buf = bit_swap_buf + i * 4;
        data = buf[0] << 24 | buf[1] << 16 | buf[2] << 8 | buf[3];
        ps48_write(fd, 2, 0x70, data);
    }
    free(bit_swap_buf);
}


static void usage(void)
{
    char *usage_ptr = 
        "   -r addr\n"
        "       Read flash controller register\n"
        "   -w addr data\n"
        "       Write flash controler register\n"
        "   -prog file_name main/gold\n"
        "       Program FPGA image to main or gold partition\n"
        "   -file file_name main/gold\n"
        "       Read flash partition (main/gold) to file. Entire 16MB of each partition will be read out\n"
        "";
    printf("%s", usage_ptr);
    exit(0);
}

static void usage_full (void) {
    char *usage_ptr = 
        "============================================\n"
        "QSPI flash\n"
        "   -r addr\n"
        "       Read flash controller register\n"
        "   -w addr data\n"
        "       Write flash contorller register\n"
        "   -prog file_name main/gold\n"
        "       Program FPGA image to main or gold partition\n"
        "   -file file_name main/gold\n"
        "       Read flash partition (main/gold) to file. Entire 16MB of each partition will be read out\n"
        "   -reload\n"
        "       Reload FPGA"
        "------------------\n"
        "Debug commands\n"
        "   -init\n"
        "       PS48 initialization: sync and page confguration\n"
        "   -noop\n"
        "       Send noop command\n"
        "   -resp\n"
        "       Retrive resp packet\n"
        "   -frdsr\n"
        "       Read flash status register\n"
        "   -frpage addr\n"
        "       Read one page data from flash at specified address\n"
        "   -fberase addr\n"
        "       Erase one block at specified address\n"
        "   -fwpage addr\n"
        "       Complie one page binary data and write to specified address of flash\n"
        "   -wp numBytes\n"
        "       PS48 write pipeline test with specified number of bytes\n"
        "   -frp addr numBytes\n"
        "       Flash read pipeline test: read certain number of bytes at specified flash address\n"
        "   -xcvrrd addr\n"
        "       Read transceiver register\n"
        "   -xcvrwr addr value\n"
        "       Write transceiver register\n"
        "   -mdiord addr\n"
        "       Read PHY register\n"
        "   -mdiowr addr value\n"
        "       Write PHY register\n"
        "   -serdes cmd_num [options]\n"
        "       Debugging commands for the transceiver<->PHY interface\n"
        "";

    printf("%s", usage_ptr);
}


void util_ps48_read(char* id, uint32_t addr) {
    uint32_t page;
    uint32_t fd;

    ps48_sync(fd);
    uint32_t data;
    if (strcmp(id, "fc") == 0) {
        printf("Read flash controller\n");
        ps48_page_config(fd, FLASH_AND_SWITCH_PAGE_CONFIG);
        page = 0;
    } else if (strcmp(id, "pc") == 0) {
        printf("Read power controller\n");
        ps48_page_config(fd, PC_AND_SERDES_PAGE_CONFIG);
        page = 2;
    } 
}

static uint32_t ps48_xcvr_read(uint32_t fd, uint32_t offset)
{
    uint32_t ret;
    uint32_t addr_f;
    ret = (uint32_t)ps48_read(fd, PAGE_ID_SERDES, offset);
    if (ret == -1) {
        printf("ps48_read() failed\n");
        return ret;
    }
    return ret;
}

static int ps48_xcvr_write(uint32_t fd, uint32_t addr, uint32_t data)
{
    int ret;
    ret = ps48_write(fd, PAGE_ID_SERDES, addr, data);
    if (ret == -1) {
        printf("ps48_write() failed\n");
        return ret;
    }
    return ret;

    //ret = ps48_noop(fd);
    //if (ret == -1) {
    //    return ret;
    //}

    //return ps48_resp(fd);
}

void decode_xcvr_cfg_ctrl_reg(uint32_t data)
{
    printf("xcvr cfg ctrl reg: 0x%x\n", data);
    printf("    sw_reset: 0x%x\n", (data >> SW_RESET_SHIFT) & SW_RESET_MASK);
    printf("    cfg_vector: 0x%x\n", (data >> CFG_VECTOR_SHIFT) & CFG_VECTOR_MASK);
    printf("        an_enable: 0x%x\n", (data >> AN_ENABLE_SHIFT) & AN_ENABLE_MASK);
    printf("    sig_detect: 0x%x\n", (data >> SIG_DETECT_SHIFT) & SIG_DETECT_MASK);
    printf("    an_adv_config_vector: 0x%x\n", (data >> AN_ADV_CONFIG_VECTOR_SHIFT) & AN_ADV_CONFIG_VECTOR_MASK);
    printf("        speed: 0x%x\n", (data >> AN_SPEED_SHIFT) & AN_SPEED_MASK);
    printf("        duplex: 0x%x\n", (data >> AN_DUPLEX_SHIFT) & AN_DUPLEX_MASK);
    printf("        ack: 0x%x\n", (data >> AN_ACK_SHIFT) & AN_ACK_MASK);
    printf("        link status: 0x%x\n", (data >> AN_LINK_STATUS_SHIFT) & AN_LINK_STATUS_MASK);
    printf("    an_restart_config: 0x%x\n", (data >> AN_RESTART_CONFIG_SHIFT) & AN_RESTART_CONFIG_MASK);
}
void decode_xcvr_sta_reg(uint32_t data)
{
    printf("xcvr sta reg: 0x%x\n", data);
    printf("    status_vector: 0x%x\n", (data >> STATUS_VECTOR_SHIFT) & STATUS_VECTOR_MASK);
    printf("        link status: 0x%x\n", (data >> LINK_STATUS_SHIFT) & LINK_STATUS_MASK);
    printf("        link sync: 0x%x\n", (data >> LINK_SYNC_SHIFT) & LINK_SYNC_MASK);
    printf("        SGMII phy link status: 0x%x\n", (data >> SGMII_PHY_LINK_STATUS_SHIFT) & SGMII_PHY_LINK_STATUS_MASK);
    printf("        speed: 0x%x\n", (data >> SPEED_SHIFT) & SPEED_MASK);
    printf("        duplex: 0x%x\n", (data >> DUPLEX_MODE_SHIFT) & DUPLEX_MODE_MASK);
}

void decode_phy_fiber_ctrl_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_FIBER_CTRL_REG, &data, 0x0);
    printf("PHY fiber ctrl reg (%d): 0x%x\n", PHY_FIBER_CTRL_REG, data);
    printf("    speed select: 0x%x\n", (data >> (PHY_SPEED_SELECT_MSB_SHIFT - 1) & 0x2)  |
     ((data >> PHY_SPEED_SELECT_LSB_SHIFT) & 0x1));
    printf("    AN enable: 0x%x\n", (data >> PHY_AN_ENABLE_SHIFT) & PHY_AN_ENABLE_MASK);
    printf("    duplex mode: 0x%x\n", (data >> PHY_DUPLEX_SHIFT) & PHY_DUPLEX_MASK);
}

void decode_phy_fiber_status_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_FIBER_STATUS_REG, &data, 0x0);
    printf("PHY fiber status reg (%d): 0x%x\n", PHY_FIBER_STATUS_REG, data);
    printf("    AN complete: 0x%x\n", (data >> PHY_AN_COMPLETE_SHIFT) & PHY_AN_COMPLETE_MASK);
    printf("    link status: 0x%x\n", (data >> PHY_LINK_STATUS_SHIFT) & PHY_LINK_STATUS_MASK);
}

void decode_phy_an_adv_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_AN_ADV_REG, &data, 0x0);
    printf("PHY AN adv reg (%d): 0x%x\n", PHY_AN_ADV_REG, data);
    printf("    speed: 0x%x\n", (data >> PHY_AN_ADV_SPEED_SHIFT) & PHY_AN_ADV_SPEED_MASK);
    printf("    duplex: 0x%x\n", (data >> PHY_AN_ADV_DUPLEX_SHIFT) & PHY_AN_ADV_DUPLEX_MASK);
}

void decode_phy_link_partner_ability_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_LINK_PARTNER_ABILITY_REG, &data, 0x0);
    printf("PHY link partner ability reg (%d): 0x%x\n", PHY_LINK_PARTNER_ABILITY_REG, data);
}

void decode_phy_an_expansion_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_AN_EXPANSION_REG, &data, 0x0);
    printf("PHY AN expansion reg (%d): 0x%x\n", PHY_AN_EXPANSION_REG, data);
}

void decode_phy_specific_status_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_SPECIFIC_STATUS_REG, &data, 0x0);
    printf("PHY specific status reg (%d): 0x%x\n", PHY_SPECIFIC_STATUS_REG, data);
    printf("    speed: 0x%x\n", (data >> PHY_SPECIFIC_SPEED_SHIFT) & PHY_SPECIFIC_SPEED_MASK);
    printf("    duplex: 0x%x\n", (data >> PHY_SPECIFIC_DUPLEX_SHIFT) & PHY_SPECIFIC_DUPLEX_MASK);
    printf("    speed & duplex resolved: 0x%x\n", (data >> PHY_SPECIFIC_SPEED_DUPLEX_RESOLVED_SHIFT) & PHY_SPECIFIC_SPEED_DUPLEX_RESOLVED_MASK);
    printf("    link (real time): 0x%x\n", (data >> PHY_SPECIFIC_LINK_RT_SHIFT) & PHY_SPECIFIC_LINK_RT_MASK);
    printf("    remote fault received: 0x%x\n", (data >> PHY_SPECIFIC_RMT_FAULT_RCVD_SHIFT) & PHY_SPECIFIC_RMT_FAULT_RCVD_MASK);
    printf("    sync status: 0x%x\n", (data >> PHY_SPECIFIC_SYNC_STATUS_SHIFT) & PHY_SPECIFIC_SYNC_STATUS_MASK);
}

void decode_phy_specific_ctrl2_reg(void)
{
    uint16_t data;
    mdio_rd(PHY_SPECIFIC_CTRL2_REG, &data, 0x0);
    printf("PHY specific control 2 reg (%d): 0x%x\n", PHY_SPECIFIC_CTRL2_REG, data);
    printf("    AN bypass status: 0x%x\n", (data >> PHY_AN_BYPASS_STATUS_SHIFT) & PHY_AN_BYPASS_STATUS_MASK);
}

static void dump_status_on_xcrv(uint32_t fd)
{
    uint32_t result;
    uint16_t data;
    printf("read status on transceiver\n");
    result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
    decode_xcvr_cfg_ctrl_reg(result);
    result = ps48_xcvr_read(fd, XCVR_STA_OFFSET);
    decode_xcvr_sta_reg(result);
}

static void dump_status_on_phy(void)
{
    mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
    decode_phy_fiber_ctrl_reg();
    decode_phy_fiber_status_reg();
    decode_phy_an_adv_reg();
    decode_phy_link_partner_ability_reg();
    decode_phy_an_expansion_reg();
    decode_phy_specific_status_reg();
    decode_phy_specific_ctrl2_reg();
}

static uint8_t prbs_pattern_mapping(uint32_t prbs_pattern_sel, uint32_t dev)
{
    uint8_t pattern = 0;
    switch (prbs_pattern_sel) {
        case 7:
            if (dev == PRBS_DEV_XCVR) {
                pattern = XCVR_PRBS_7;
            } else {
                pattern = PHY_PRBS_PATTERN_7;
            }
            break;
        case 15:
            if (dev == PRBS_DEV_XCVR) {
                pattern = XCVR_PRBS_15;
            } else {
                printf("PRBS 15 not supported on PHY\n");
            }
            break;
        case 23:
            if (dev == PRBS_DEV_XCVR) {
                pattern = XCVR_PRBS_23;
            } else {
                pattern = PHY_PRBS_PATTERN_23;
            }
            break;
        case 31:
            if (dev == PRBS_DEV_XCVR) {
                pattern = XCVR_PRBS_31;
            } else {
                pattern = PHY_PRBS_PATTERN_31;
            }
            break;
        default:
            printf("Unsupported PRBS pattern %d\n", prbs_pattern_sel);
            break;
    }
    return pattern;
}

static void serdes_test_cmd(uint32_t fd, uint32_t command, SERDES_TEST_OPTIONS *p_options)
{
    uint32_t result;
    uint16_t data;
    uint8_t pattern;
    switch (command) {
        case CONFIG_PHY_PKT_CHECKER://opt #0: enable/disable
            if (p_options->size != 1) {
                usage_full();
                return;
            }
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_18, 0x0);
            //clear counters
            mdio_wr(PHY_CHECKER_CTRL_REG, 0x1 << CRC_COUNTER_RESET_SHIFT, 0x0);
#if (DEBUG == ENABLE)
            mdio_rd(PHY_CRC_COUNTERS_REG, &data, 0x0);
            printf("After clear, pkt counter: 0x%x, CRC error counter: 0x%x\n",
                   (data >> PACKET_COUNTER_SHIFT) & PACKET_COUNTER_MASK, data & ERROR_COUNTER_MASK);
#endif
            if (p_options->p_opt[0] == 1) {
                printf("Enable PHY packet checker\n");
                mdio_wr(PHY_CHECKER_CTRL_REG, CHECK_DATA_FROM_COPPER_INTERFACE, 0x0);
            } else {
                printf("Disable PHY packet checker\n");
                mdio_wr(PHY_CHECKER_CTRL_REG, 0, 0x0);
            }
            //read counter
            mdio_rd(PHY_CRC_COUNTERS_REG, &data, 0x0);
            printf("After checker enable/disable, pkt counter: %d, CRC error counter: %d\n",
                (data >> PACKET_COUNTER_SHIFT) & PACKET_COUNTER_MASK, data & ERROR_COUNTER_MASK);
            break;
        case CONFIG_PHY_PKT_GENERATOR://opt #0: enable/disable, opt #1: burst, opt #2: payload, opt #3: length, opt #4: error
            if (p_options->size == 0) {
                usage_full();
                return;
            }
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_18, 0x0);
            if (p_options->p_opt[0] == 1) {//enable
                if (p_options->size == 5) {
                    printf("Enable PHY packet generator\n");
                    data = GEN_PKT_FROM_COPPER_INTERFACE |
                            ((p_options->p_opt[1] & PKT_BURST_MASK) << PKT_BURST_SHIFT) |
                            ((p_options->p_opt[2] & PKT_PAYLOAD_MASK) << PKT_PAYLOAD_SHIFT) |
                            ((p_options->p_opt[3] & PKT_LENGTH_MASK) << PKT_LENGTH_SHIFT) |
                            (p_options->p_opt[4] & PKT_WITH_ERROR);
                } else {
                    usage_full();
                    return;
                }
            } else {//disable
                printf("Disable PHY packet generator\n");
                data = 0;
            }
            mdio_wr(PHY_PKT_GENERATOR_REG, data, 0x0);
            break;
        case PHY_PKT_CHECKER_READ_COUNTER://no additional options
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_18, 0x0);
            mdio_rd(PHY_CRC_COUNTERS_REG, &data, 0x0);
            printf("pkt counter: %d, CRC error counter: %d\n",
                   (data >> PACKET_COUNTER_SHIFT) & PACKET_COUNTER_MASK, data & ERROR_COUNTER_MASK);
            break;
        case CONFIG_PHY_SYS_INTF_LOOPBACK://opt #0: enable/disable
            if (p_options->size != 1) {
                usage_full();
                return;
            }
            /*  mdio_wr(PHY_PAGE_REG, 0x1, 0x0);// set page to 1
            mdio_rd(0, &data, 0x0);
            data |= 0x1 << 14;
            mdio_wr(0, data, 0x0);*/
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_0, 0x0);
            mdio_rd(PHY_COPPER_CTRL_REG, &data, 0x0);
            if (p_options->p_opt[0] == 1) {
                printf("Enable PHY system interface loopback\n");
                data |= 0x1 << PHY_SYS_INTF_LOOPBACK_SHIFT;
            } else {
                printf("Disable PHY system interface loopback\n");
                data &= ~(0x1 << PHY_SYS_INTF_LOOPBACK_SHIFT);
            }
            mdio_wr(PHY_COPPER_CTRL_REG, data, 0x0);
            break;
        case CONFIG_PHY_STUB_TEST://opt #0: enable/disable
            if (p_options->size != 1) {
                usage_full();
                return;
            }
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_6, 0x0);
            mdio_rd(PHY_COPPER_CHECKER_CTRL_REG, &data, 0x0);
            if (p_options->p_opt[0] == 1) {
                printf("Enable PHY external loopback\n");
                data |= 0x1 << PHY_ENABLE_STUB_TEST_SHIFT;
            } else {
                printf("Disable PHY external loopback\n");
                data &= ~(0x1 << PHY_ENABLE_STUB_TEST_SHIFT);
            }
            mdio_wr(PHY_COPPER_CHECKER_CTRL_REG, data, 0x0);
          /*  mdio_wr(PHY_PAGE_REG, 18, 0x0);
            mdio_rd(20, &data, 0x0);
            data |= 0x1 << 15;
            mdio_wr(20, data, 0x0);
            usleep(1000);
            mdio_rd(20, &data, 0x0);
            printf("register 20: 0x%x\n", data);*/
            break;
        case DUMP_STATUS_ONLY://no additional options
            /*ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, 0x6c00c1);
            mdio_rd(PHY_FIBER_CTRL_REG, &data, 0x0);
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, 0x6c00c0);*/
            dump_status_on_xcrv(fd);
            dump_status_on_phy();
            break;
        case AN_ON_PHY_COPPER_ENABLE://no additional options
            printf("\nEnable Auto-Negotiation on PHY copper\n");

            printf("step 1: set speed and duplex, enable AN\n");
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_0, 0x0);
            mdio_rd(PHY_COPPER_CTRL_REG, &data, 0x0);
            data &= ~(PHY_DUPLEX_MASK << PHY_DUPLEX_SHIFT);
            data &= ~((0x1 << PHY_SPEED_SELECT_LSB_SHIFT) | (0x1 << PHY_SPEED_SELECT_MSB_SHIFT));
            data |= 0x1 << PHY_SPEED_SELECT_MSB_SHIFT;//1000M
            data |= PHY_DUPLEX_FULL << PHY_DUPLEX_SHIFT;
            data |= PHY_AN_ENABLE_MASK << PHY_AN_ENABLE_SHIFT;
            mdio_wr(PHY_COPPER_CTRL_REG, data, 0x0);

            printf("step 2: do SW reset to force AN\n");
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            data |= PHY_AN_RESTART_MASK << PHY_AN_RESTART_SHIFT;//not necessary
            mdio_wr(PHY_COPPER_CTRL_REG, data, 0x0);

            printf("step 3: restart xcvr AN\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result |= AN_RESTART_CONFIG_MASK << AN_RESTART_CONFIG_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 4: sleep 1s and then dump status on both sides\n");
            sleep(1);
            dump_status_on_xcrv(fd);
            dump_status_on_phy();
            break;
        case CONFIG_PHY_MODE://no additional options
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_18, 0x0);
            mdio_rd(PHY_GEN_CTRL_REG, &data, 0x0);
            data &= ~SERDES_MODE_MASK;
            data |= SGMII_TO_COPPER_MODE;
            mdio_wr(PHY_GEN_CTRL_REG, data, 0x0);
            mdio_rd(PHY_GEN_CTRL_REG, &data, 0x0);
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            mdio_wr(PHY_GEN_CTRL_REG, data, 0x0);
            sleep(1);
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
            mdio_rd(PHY_SPECIFIC_CTRL_REG, &data, 0x0);
            printf("read PHY mode: 0x%x(0x2 means SGMII System mode)\n", (data >> PHY_SPECIFIC_PHY_MODE_SHIFT) & PHY_SPECIFIC_PHY_MODE_MASK);
            break;
        case AN_ENABLE://no additional options
            printf("\nEnable Auto-Negotiation on xcvr\n");

            printf("step 1: put xcvr in SW reset\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result |= SW_RESET_MASK << SW_RESET_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 2: set speed and duplex, enable AN\n");
            result &= ~((AN_SPEED_MASK << AN_SPEED_SHIFT) | (AN_DUPLEX_MASK << AN_DUPLEX_SHIFT));
            result |= (AN_SPEED_1000M << AN_SPEED_SHIFT) | (AN_DUPLEX_FULL << AN_DUPLEX_SHIFT);
            result |= AN_ENABLE_MASK << AN_ENABLE_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 3: get xcvr out of SW reset\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result &= ~(SW_RESET_MASK << SW_RESET_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 4: dump the xcvr cfg_ctrl register\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            decode_xcvr_cfg_ctrl_reg(result);

            printf("\nEnable AN on PHY\n");

            mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
            mdio_rd(PHY_SPECIFIC_CTRL_REG, &data, 0x0);
            printf("step 5: read PHY mode: 0x%x(0x2 means SGMII System mode)\n", (data >> PHY_SPECIFIC_PHY_MODE_SHIFT) & PHY_SPECIFIC_PHY_MODE_MASK);
            /*printf("step x: disable AN bypass\n");
            mdio_rd(PHY_SPECIFIC_CTRL2_REG, &data, 0x0);
            data &= ~(PHY_AN_BYPASS_MASK << PHY_AN_BYPASS_SHIFT);
            mdio_wr(PHY_SPECIFIC_CTRL2_REG, data, 0x0);*/

            printf("step 6: set speed and duplex, enable AN on page 0\n");
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_0, 0x0);
            mdio_rd(PHY_COPPER_CTRL_REG, &data, 0x0);
            data &= ~(PHY_DUPLEX_MASK << PHY_DUPLEX_SHIFT);
            data &= ~((0x1 << PHY_SPEED_SELECT_LSB_SHIFT) | (0x1 << PHY_SPEED_SELECT_MSB_SHIFT));
            data |= 0x1 << PHY_SPEED_SELECT_MSB_SHIFT;//1000M
            data |= PHY_DUPLEX_FULL << PHY_DUPLEX_SHIFT;
            data |= PHY_AN_ENABLE_MASK << PHY_AN_ENABLE_SHIFT;
            mdio_wr(PHY_COPPER_CTRL_REG, data, 0x0);

            printf("step 7: do SW reset to force AN on page 0\n");
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            data |= PHY_AN_RESTART_MASK << PHY_AN_RESTART_SHIFT;//not necessary
            mdio_wr(PHY_COPPER_CTRL_REG, data, 0x0);

            printf("step 8: set speed and duplex, enable AN on page 1\n");
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
            mdio_rd(PHY_FIBER_CTRL_REG, &data, 0x0);
            data &= ~(PHY_DUPLEX_MASK << PHY_DUPLEX_SHIFT);
            data &= ~((0x1 << PHY_SPEED_SELECT_LSB_SHIFT) | (0x1 << PHY_SPEED_SELECT_MSB_SHIFT));
            data |= 0x1 << PHY_SPEED_SELECT_MSB_SHIFT;//1000M
            data |= PHY_DUPLEX_FULL << PHY_DUPLEX_SHIFT;
            data |= PHY_AN_ENABLE_MASK << PHY_AN_ENABLE_SHIFT;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);

            printf("step 9: do SW reset to force AN on page 1\n");
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            data |= PHY_AN_RESTART_MASK << PHY_AN_RESTART_SHIFT;//not necessary
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);
            //sleep(1);

            printf("step 10: restart xcvr AN\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result |= AN_RESTART_CONFIG_MASK << AN_RESTART_CONFIG_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            /*printf("step 9: dump the xcvr cfg_ctrl register\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            decode_xcvr_cfg_ctrl_reg(result);*/

            /*mdio_rd(PHY_FIBER_CTRL_REG, &data, 0x0);
                        data |= 0x1 << 9;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);*/

            printf("step 11: sleep 1s and then dump status on both sides\n");
            sleep(1);
            dump_status_on_xcrv(fd);
            dump_status_on_phy();
            break;
        case AN_DISABLE://no additional options
            printf("\nDisable AN on xcvr\n");

            printf("step 1: put xcvr in SW reset\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result |= SW_RESET_MASK << SW_RESET_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 2: clear AN enable\n");
            result &= ~(AN_ENABLE_MASK << AN_ENABLE_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 3: set speed and duplex\n");
            result &= ~((AN_SPEED_MASK << AN_SPEED_SHIFT) | (AN_DUPLEX_MASK << AN_DUPLEX_SHIFT));
            result |= (AN_SPEED_1000M << AN_SPEED_SHIFT) | (AN_DUPLEX_FULL << AN_DUPLEX_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 4: get xcvr out of SW reset\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result &= ~(SW_RESET_MASK << SW_RESET_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);

            printf("step 5: dump the xcvr cfg_ctrl register\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            decode_xcvr_cfg_ctrl_reg(result);

            printf("\nDisable AN on PHY\n");
            mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
            mdio_rd(PHY_SPECIFIC_CTRL_REG, &data, 0x0);
            printf("step 6: PHY mode: 0x%x(0x2 means SGMII System mode)\n", (data >> PHY_SPECIFIC_PHY_MODE_SHIFT) & PHY_SPECIFIC_PHY_MODE_MASK);
            //mdio_rd(PHY_FIBER_CTRL_REG, &data, 0x0);
            //decode_phy_fiber_ctrl_reg(data);

            printf("step 7: clear AN enable\n");
            data  &= ~(PHY_AN_ENABLE_MASK << PHY_AN_ENABLE_SHIFT);
            //mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);
            /*printf("step 8: do SW reset\n");
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);
            printf("step 9: sleep 1s\n");
            sleep(1);*/
            printf("step 8: set speed and duplex\n");
            data &= ~(PHY_DUPLEX_MASK << PHY_DUPLEX_SHIFT);
            data &= ~((0x1 << PHY_SPEED_SELECT_LSB_SHIFT) | (0x1 << PHY_SPEED_SELECT_MSB_SHIFT));
            data |= 0x1 << PHY_SPEED_SELECT_MSB_SHIFT;//1000M
            data |= PHY_DUPLEX_FULL << PHY_DUPLEX_SHIFT;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);

            printf("step 9: do SW reset\n");
            data |= PHY_SOFTWARE_RESET_MASK << PHY_SOFTWARE_RESET_SHIFT;
            mdio_wr(PHY_FIBER_CTRL_REG, data, 0x0);

            printf("step 10: sleep 1s and then dump status on both sides\n");
            sleep(1);
            dump_status_on_xcrv(fd);
            dump_status_on_phy();
            break;
        case CONFIG_NEAREND_PMA_LOOPBACK://opt #0: enable/disable
            if (p_options->size != 1) {
                usage_full();
                return;
            }
            printf("step 1: get xcvr out of SW reset\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_CTRL_OFFSET);
            result &= ~(SW_RESET_MASK << SW_RESET_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_CTRL_OFFSET, result);
            printf("before setting PMA loopback:\n");
            result = ps48_xcvr_read(fd, XCVR_STA_OFFSET);
            printf("XCVR_STA_OFFSET: 0x%x\n", result);
            result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
            printf("XCVR_CFG_DBG_OFFSET: 0x%x\n", result);
            if (p_options->p_opt[0] == 1) {
                printf("\nEnable new-end PMA loopback on xcvr\n");
                result &= ~(XCVR_LOOPBACK_MASK << XCVR_LOOPBACK_SHIFT);
                result |= XCVR_NEAR_END_PMA_LOOPBACK << XCVR_LOOPBACK_SHIFT;
            } else {
                printf("\nDisable new-end PMA loopback on xcvr\n");
                result &= ~(XCVR_LOOPBACK_MASK << XCVR_LOOPBACK_SHIFT);
            }
            ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);
            //reset
            result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
            printf("XCVR_CFG_DBG_OFFSET: 0x%x\n", result);
            //result |= RXBUF_RESET_MASK << RXBUF_RESET_SHIFT;
            //result |= RXPCS_RESET_MASK << RXPCS_RESET_SHIFT;
            result |= RXPMA_RESET_MASK << RXPMA_RESET_SHIFT;
            //result |= RXPRBSCNT_RESET_MASK << RXPRBSCNT_RESET_SHIFT;
            ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);
            result = ps48_xcvr_read(fd, XCVR_STA_DBG2_OFFSET);
            printf("XCVR_STA_DBG2_OFFSET before reset: 0x%x\n", result);
            usleep(1000);
            result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
            result &= ~(RXPMA_RESET_MASK << RXPMA_RESET_SHIFT);
            ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);

            int retry;
            while(retry < 100) {
                result = ps48_xcvr_read(fd, XCVR_STA_DBG2_OFFSET);
                if ( (result & RX_RESET_DONE_MASK) == RX_RESET_DONE_MASK) {
                    printf("XCVR_STA_DBG2_OFFSET after reset: 0x%x\n", result);
                    break;
                }
                usleep(1000);
                retry++;
            }

            if (retry == 100) {
                printf("Timeout waiting for RX_RESET_DONE to be set after RX PMA reset!\n");
            }
#if (DEBUG == ENABLE)
            printf("after setting PMA loopback:\n");
            result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
            printf("CFG_DEBUG: 0x%x\n", result);
            result = ps48_xcvr_read(fd, XCVR_STA_OFFSET);
            printf("STA: 0x%x\n", result);
#endif
            break;
        case PRBS_GEN_START://opt #0: 0 for xcvr, 1 for PHY, opt #1: PRBS pattern, opt #2: tx polarity, opt #3: force error
            if (p_options->size < 3) {
                usage_full();
                return;
            }
            pattern = prbs_pattern_mapping(p_options->p_opt[1], p_options->p_opt[0]);
            printf("Starting PRBS generator on ");

            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
                if (p_options->p_opt[2] == 1) {
                    result |= TXPOLARITY_MASK << TXPOLARITY_SHIFT;
                } else {
                    result &= ~(TXPOLARITY_MASK << TXPOLARITY_SHIFT);
                }
                if (p_options->p_opt[3] == 1) {
                    result |= TXPRBSFORCEERR_MASK << TXPRBSFORCEERR_SHIFT;
                } else {
                    result &= ~(TXPRBSFORCEERR_MASK << TXPRBSFORCEERR_SHIFT);
                }
                ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);

                result = ps48_xcvr_read(fd, XCVR_CFG_DBG2_OFFSET);
                result &= ~(TXPRBSSEL_MASK << TXPRBSSEL_SHIFT);
                result |= (pattern & TXPRBSSEL_MASK) << TXPRBSSEL_SHIFT;
                ps48_xcvr_write(fd, XCVR_CFG_DBG2_OFFSET, result);
#if (DEBUG == ENABLE)
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG2_OFFSET);
                printf("XCVR_CFG_DBG2_OFFSET: 0x%x\n", result);
#endif
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                data = (pattern & PHY_PRBS_PATTERN_MASK) << PHY_PRBS_PATTERN_SHIFT;
                if (p_options->p_opt[2] == 1) {
                    data |= PHY_PRBS_TX_POLARITY_MASK << PHY_PRBS_TX_POLARITY_SHIFT;
                } else {
                    data &= ~(PHY_PRBS_TX_POLARITY_MASK << PHY_PRBS_TX_POLARITY_SHIFT);
                }
                data |= PHY_PRBS_GENERATOR_EN;
                mdio_wr(PHY_PRBS_CTRL_REG, data, 0x0);
            }
            break;
        case PRBS_GEN_STOP://opt #0: 0 for xcvr, 1 for PHY
            if (p_options->size != 1) {
                usage_full();
                break;
            }
            printf("Stopping PRBS generator on ");
            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG2_OFFSET);
                result &= ~(TXPRBSSEL_MASK << TXPRBSSEL_SHIFT);
                ps48_xcvr_write(fd, XCVR_CFG_DBG2_OFFSET, 0);
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                mdio_wr(PHY_PRBS_CTRL_REG, 0x0, 0x0);
            }
            break;
        case PRBS_CHECKER_START:
        //opt #0: 0 for xcvr, 1 for PHY, opt #1: PRBS pattern, opt #2: rx polarity, opt #3: start counting until PRBS locks
            if (p_options->size < 3) {
                usage_full();
                break;
            }
            pattern = prbs_pattern_mapping(p_options->p_opt[1], p_options->p_opt[0]);
            printf("Starting PRBS checker on ");
            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
                result &= ~(RXPRBSSEL_MASK << RXPRBSSEL_SHIFT);
                result |= (pattern & RXPRBSSEL_MASK) << RXPRBSSEL_SHIFT;
                if (p_options->p_opt[2] == 1) {
                    result |= RXPOLARITY_MASK << RXPOLARITY_SHIFT;
                } else {
                    result &= ~(RXPOLARITY_MASK << RXPOLARITY_SHIFT);
                }
                ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                data = (pattern & PHY_PRBS_PATTERN_MASK) << PHY_PRBS_PATTERN_SHIFT;
                if (p_options->p_opt[2] == 1) {
                    data |= PHY_PRBS_RX_POLARITY_MASK << PHY_PRBS_RX_POLARITY_SHIFT;
                } else {
                    data &= ~(PHY_PRBS_RX_POLARITY_MASK << PHY_PRBS_RX_POLARITY_SHIFT);
                }
                if (p_options->p_opt[3] == 1) {
                    data |= PHY_PRBS_LOCK_MASK << PHY_PRBS_LOCK_SHIFT;
                } else {
                    data &= ~(PHY_PRBS_LOCK_MASK << PHY_PRBS_LOCK_SHIFT);
                }
                data |= PHY_PRBS_CHECKER_EN;
                mdio_wr(PHY_PRBS_CTRL_REG, data, 0x0);
#if (DEBUG == ENABLE)
                mdio_rd(PHY_PRBS_CTRL_REG, &data, 0x0);
                printf("PHY_PRBS_CTRL_REG: 0x%x\n", data);
#endif
            }
            break;
        case PRBS_CHECKER_STOP://opt #0: 0 for xcvr, 1 for PHY
            if (p_options->size != 1) {
                usage_full();
                break;
            }
            printf("Stopping PRBS checker on ");
            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
                result &= ~(RXPRBSSEL_MASK << RXPRBSSEL_SHIFT);//0xFFFC7FFF;
                ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                mdio_wr(PHY_PRBS_CTRL_REG, 0x0, 0x0);
            }
            break;
        case PRBS_ERR_READ://opt #0: 0 for xcvr, 1 for PHY
            if (p_options->size != 1) {
                usage_full();
                break;
            }
            printf("Reading PRBS error on ");
            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_STA_DBG_OFFSET);
                printf("PRBS error bit (31) on transceiver: 0x%x\n", result);
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                uint16_t data_lo, data_hi;
                mdio_rd(PHY_PRBS_ERROR_COUNTER_LSB_REG, &data_lo, 0x0);
                mdio_rd(PHY_PRBS_ERROR_COUNTER_MSB_REG, &data_hi, 0x0);
                printf("MSB: 0x%x, LSB: 0x%x\n", data_hi, data_lo);
            }
            break;
        case PRBS_ERR_CLEAR://opt #0: 0 for xcvr, 1 for PHY
            if (p_options->size != 1) {
                usage_full();
                break;
            }
            printf("Clearing PRBS error on ");
            if (p_options->p_opt[0] == PRBS_DEV_XCVR) {
                printf("transceiver\n");
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
                result |= RXPRBSCNT_RESET_MASK << RXPRBSCNT_RESET_SHIFT;
                ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);
               /* sleep(1);
                result = ps48_xcvr_read(fd, XCVR_CFG_DBG_OFFSET);
                result &= ~(RXPRBSCNT_RESET_MASK << RXPRBSCNT_RESET_SHIFT);
                ps48_xcvr_write(fd, XCVR_CFG_DBG_OFFSET, result);*/
            } else {
                printf("PHY\n");
                mdio_wr(PHY_PAGE_REG, PHY_PAGE_1, 0x0);
                mdio_rd(PHY_PRBS_CTRL_REG, &data, 0x0);
                //printf("PHY_PRBS_CTRL_REG: 0x%x\n", data);

                data |= 0x1 << PHY_PRBS_CLEAR_COUNTER_SHIFT;
                mdio_wr(PHY_PRBS_CTRL_REG, data, 0x0);
            }
            break;
        default:
            usage_full();
            break;
    }
}

int main(int argc, char *argv[])
{
    uint8_t val, index;
    char *buf;
    uint32_t value, addr;

    if ( argc < 2 ) usage();

    if ( strcmp(argv[1], "-init") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        ps48_init(fd); 
        close(fd);
    } 
    else if ( strcmp(argv[1], "-r") == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        addr = strtoul(argv[2], NULL, 0);
        val = ps48_qspi_ctrl_read(fd, addr);

        close(fd);
    }  
    else if ( strcmp(argv[1], "-w" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);

        if ( argc < 4 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        value = strtoul(argv[3], NULL, 0);
        val = ps48_qspi_ctrl_write(fd, addr, value);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-noop" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = ps48_noop(fd);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-resp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = ps48_resp(fd);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frdsr" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        val = flash_rdsr(fd);
        printf("SR: 0x%x\n", val);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frpage" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        addr = strtoul(argv[2], NULL, 0);
        flash_read_page(fd, addr);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fberase" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        uint8_t val_sr;
        if ( argc < 3 ) usage();

        printf("Block Erase\n");

        addr = strtoul(argv[2], NULL, 0);
        flash_ena_4B_addr(fd);
        flash_wr_ena(fd);

        val_sr = flash_rdsr(fd);
        printf("SR: 0x%x\n", val_sr);

        flash_block_erase_top(fd, addr);
        flash_wr_dis(fd);

        close(fd);
    } 
    else if ( strcmp(argv[1], "-fwpage" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        printf("Write Page Test\n");

        addr = strtoul(argv[2], NULL, 0);

        flash_write_page_test(fd, addr);

        close(fd);
    } 
    else if ( (strcmp(argv[1], "-fprog") == 0)  || 
              (strcmp(argv[1], "-prog") == 0)
            ) 
    {
        if ( argc < 4 ) usage();
        printf("Program image\n");
        flash_prog(argv[2], argv[3]);
    } 
    else if ( (strcmp(argv[1], "-ffile" ) == 0) ||
              (strcmp(argv[1], "-file" ) == 0) ) 
    {
        if ( argc < 4 ) usage();
        printf("Reading flash data to file\n");
        flash_read_to_file(argv[2], argv[3]);
    } 
    else if ( strcmp(argv[1], "-erase" ) == 0 ) 
    {
        if ( argc < 4 ) usage();
        printf("Erasing flash data\n");
        flash_erase(argv[2], argv[3]);
    } 

    else if ( strcmp(argv[1], "-wp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 3 ) usage();

        uint32_t numByte = strtoul(argv[2], NULL, 0);
        printf("Write Pipeline test\n");
        ps48_write_pipeline_test(fd, numByte);
        close(fd);
    } 
    else if ( strcmp(argv[1], "-frp" ) == 0 ) 
    {
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        if ( argc < 4 ) usage();

        uint32_t addr = strtoul(argv[2], NULL, 0);
        uint32_t numByte = strtoul(argv[3], NULL, 0);
        printf("Read Pipeline test\n");
        flash_read_pipeline_test(fd, addr, numByte);
        close(fd);
    } 
    else if ( (strcmp(argv[1], "-reload" ) == 0) ) 
    {
        fpga_reload();
    } 
    else if (strcmp(argv[1], "-xcvrrd") == 0)
    {
        if ( argc < 3 ) usage();
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        uint32_t offset = strtoul(argv[2], NULL, 0);
        uint32_t result = ps48_xcvr_read(fd, offset);
        printf("0x%x\n", result);
        close(fd);
    }
    else if (strcmp(argv[1], "-xcvrwr") == 0)
    {
        if ( argc < 4 ) usage();
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        uint32_t offset = strtoul(argv[2], NULL, 0);
        uint32_t value = strtoul(argv[3], NULL, 0);
        uint32_t result = ps48_xcvr_write(fd, offset, value);
        printf("write offset=0x%x: result=0x%x\n", offset, result);
        close(fd);
    }
    else if (strcmp(argv[1], "-mdiord") == 0)
    {
        if ( argc < 3 ) usage();
        addr = strtoul(argv[2], NULL, 0);
        uint16_t data;
        mdio_rd(addr, &data, 0x0);
        printf("0x%x\n", data);
    }
    else if (strcmp(argv[1], "-mdiowr") == 0)
    {
        if ( argc < 4 ) usage();
        addr = strtoul(argv[2], NULL, 0);
        uint16_t data = strtoul(argv[3], NULL, 0);
        mdio_wr(addr, data, 0x0);
    }
    else if (strcmp(argv[1], "-serdes") == 0)
    {
        if ( argc < 3 ) usage();
        uint32_t fd = e_open(spidev_path1, O_RDWR, 0);
        uint32_t command = strtoul(argv[2], NULL, 0);
        SERDES_TEST_OPTIONS options;
        uint32_t *my_opt = NULL;
        if (argc > 3) {
            my_opt = malloc((argc - 3) * sizeof(uint32_t));
            for (int i = 0; i < argc - 3; i++) {
                my_opt[i] = strtoul(argv[3 + i], NULL, 0);
            }
            options.size = argc - 3;
            options.p_opt = my_opt;
        }
        serdes_test_cmd(fd, command, &options);
        if (my_opt) {
            free(my_opt);
        }
        close(fd);
    }
    else if ( strcmp(argv[1], "-help" ) == 0 ) 
    {
        usage_full();
    }

    else usage();

    return 0;
}
