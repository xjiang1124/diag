package ortanoCpld

const (
    REG_REV                = 0x00
    REG_CTRL               = 0x01
    REG_CTRL_STS           = 0x02
    REG_INTR_ENA           = 0x03
    REG_INTR_STS           = 0x04
    REG_LED_PORT_CTRL      = 0x05
    REG_ESW_MDIO_CTRL_LOW  = 0x06
    REG_ESW_MDIO_CTRL_HIGH = 0x07
    REG_ESW_MDIO_DATA_LOW  = 0x08
    REG_ESW_MDIO_DATA_HIGH = 0x09
    REG_SLOT_ID            = 0x0A
    REG_SMB_WR_SPI_RD_0    = 0x0B
    REG_SMB_WR_SPI_RD_1    = 0x0C
    REG_SPI_WR_SMB_RD_0    = 0x0D
    REG_SPI_WR_SMB_RD_1    = 0x0E
    REG_LED_PORT_RATE      = 0x0F
    REG_ASIC_CTRL_0        = 0x10
    REG_ASIC_CTRL_1        = 0x11
    REG_ASIC_CTRL_2        = 0x12
    REG_ASIC_STS_0         = 0x14
    REG_LED_SYS_CTRL       = 0x15
    REG_ASIC_CORE_TEMP     = 0x16
    REG_BOARD_TEMP         = 0x18
    REG_SFP1_TEMP          = 0x19
    REG_SFP2_TEMP          = 0x1A
    REG_ASIC_WARN_TEMP     = 0x1B
    REG_ASIC_CRIT_TEMP     = 0x1C
    REG_ASIC_FATAL_TEMP    = 0x1D
    REG_CPLD_SUB_VER       = 0x1E
    REG_ASIC_PSST          = 0x20
    REG_POWER_STAT0        = 0x30
    REG_POWER_STAT1        = 0x31
    REG_POWER_STAT2        = 0x32
    REG_ID                 = 0x80
)

const (
    ID = 0x43
)
