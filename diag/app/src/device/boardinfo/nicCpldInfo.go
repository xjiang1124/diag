package boardinfo

//import (
//    "fmt"
//    "gopkg.in/yaml.v2"
//)

type NicCpld_T struct {
    REV					uint
    CTRL				uint
    CTRL_STS			uint
    INTR_STS			uint
    LED_CTRL			uint
    LED_RATE			uint
    ESW_MDIO_CTRL_LOW	uint
    ESW_MDIO_CTRL_HIGH	uint
    ESW_MDIO_DATA_LOW	uint
    ESW_MDIO_DATA_HIGH	uint
    SLOT_ID				uint
    SMB_WR_SPI_RD_0		uint
    SMB_WR_SPI_RD_1		uint
    SPI_WR_SMB_RD_0		uint
    SPI_WR_SMB_RD_1		uint
    ASIC_CTRL_0			uint
    ASIC_CTRL_1			uint
    ASIC_CTRL_2			uint
    ASIC_GPIO_0			uint
    ASIC_GPIO_1			uint
    ASIC_PSST			uint
    POWER_COST			uint
    ID					uint
}

var NicCpld = `
    REV                : 0x00
    CTRL               : 0x01
    CTRL_STS           : 0x02
    INTR_STS           : 0x03
    0LED_CTRL           : 0x04
    LED_RATE           : 0x05
    ESW_MDIO_CTRL_LOW  : 0x06
    ESW_MDIO_CTRL_HIGH : 0x07
    ESW_MDIO_DATA_LOW  : 0x08
    ESW_MDIO_DATA_HIGH : 0x09
    SLOT_ID            : 0x0A
    SMB_WR_SPI_RD_0    : 0x0B
    SMB_WR_SPI_RD_1    : 0x0C
    SPI_WR_SMB_RD_0    : 0x0D
    SPI_WR_SMB_RD_1    : 0x0E
    ASIC_CTRL_0        : 0x10
    ASIC_CTRL_1        : 0x11
    ASIC_CTRL_2        : 0x12
    ASIC_GPIO_0        : 0x13
    ASIC_GPIO_1        : 0x14
    ASIC_PSST          : 0x20
    POWER_COST         : 0x30
    ID                 : 0x80
`
