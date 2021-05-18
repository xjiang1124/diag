package taorfpga


/*
 * Registers offset
 */


type TAOR_FPGA_REGISTERS struct {
    Name     string
    Address  uint64
}

const DEV0_BAR int64 = 0x183fff400000
const DEV1_BAR int64 = 0x183fff300000
const DEV2_BAR int64 = 0x183fff200000
const DEV3_BAR int64 = 0x183fff100000
const MAP_SIZE int = 1048576

const D0_FPGA_REV_ID_REG           uint64 = 0x0
const D0_FPGA_DATECODE_REG         uint64 = 0x4
const D0_BOARD_REV_ID_REG          uint64 = 0x8
const D0_FUNC_CAP_0_REG            uint64 = 0xc
const D0_FUNC_CAP_1_REG            uint64 = 0x10
const D0_FUNC_CAP_2_REG            uint64 = 0x14
const D0_FUNC_CAP_3_REG            uint64 = 0x18
const D0_FUNC_CAP_4_REG            uint64 = 0x1c
const D0_FUNC_CAP_5_REG            uint64 = 0x20
const D0_FUNC_CAP_6_REG            uint64 = 0x24
const D0_FUNC_CAP_7_REG            uint64 = 0x28
const D0_SCRTCH_0_REG              uint64 = 0x80
const D0_SCRTCH_1_REG              uint64 = 0x84
const D0_SCRTCH_2_REG              uint64 = 0x88
const D0_SCRTCH_3_REG              uint64 = 0x8c
const D0_LED_DEBUG_0_REG           uint64 = 0xc0
const D0_LED_DEBUG_1_REG           uint64 = 0xc4
const D0_LED_DEBUG_2_REG           uint64 = 0xc8
const D0_LED_DEBUG_3_REG           uint64 = 0xcc
const D0_DEBUG_0_REG               uint64 = 0xd0
const D0_DEBUG_1_REG               uint64 = 0xd4
const D0_DEBUG_2_REG               uint64 = 0xd8
const D0_DEBUG_3_REG               uint64 = 0xdc
const D0_RESET_CAUSE_0_REG         uint64 = 0x100
const D0_RESET_CAUSE_1_REG         uint64 = 0x104
const D0_RESET_CAUSE_2_REG         uint64 = 0x108
const D0_RESET_CAUSE_3_REG         uint64 = 0x10c
const D0_DEV_MSI_0_PEND_REG        uint64 = 0x300
const D0_DEV_MSI_0_INT_EN_REG      uint64 = 0x304
const D0_DEV_MSI_1_PEND_REG        uint64 = 0x308
const D0_DEV_MSI_1_INT_EN_REG      uint64 = 0x30c
const D0_DEV_MSI_2_PEND_REG        uint64 = 0x310
const D0_DEV_MSI_2_INT_EN_REG      uint64 = 0x314
const D0_DEV_MSI_3_PEND_REG        uint64 = 0x318
const D0_DEV_MSI_3_INT_EN_REG      uint64 = 0x31c
const D0_DEV_MSI_4_PEND_REG        uint64 = 0x320
const D0_DEV_MSI_4_INT_EN_REG      uint64 = 0x324
const D0_DEV_MSI_5_PEND_REG        uint64 = 0x328
const D0_DEV_MSI_5_INT_EN_REG      uint64 = 0x32c
const D0_DEV_MSI_6_PEND_REG        uint64 = 0x330
const D0_DEV_MSI_6_INT_EN_REG      uint64 = 0x334
const D0_DEV_MSI_7_PEND_REG        uint64 = 0x338
const D0_DEV_MSI_7_INT_EN_REG      uint64 = 0x33c
const D0_MBOX_STAT_REG             uint64 = 0x400
const D0_MBOX_STAT_PLRTY_REG       uint64 = 0x404
const D0_MBOX_STAT_EDG_LVL_REG     uint64 = 0x408
const D0_MBOX_STAT_INT_EN_REG      uint64 = 0x40c
const D0_MBOX_STAT_INT_STAT_REG    uint64 = 0x410
const D0_MBOX_STAT_INT_CLR_REG     uint64 = 0x414
const D0_MBOX_0_DATA_REG           uint64 = 0x418
const D0_MBOX_1_DATA_REG           uint64 = 0x41c
const D0_MBOX_2_DATA_REG           uint64 = 0x420
const D0_MBOX_3_DATA_REG           uint64 = 0x424
const D0_U2U_CTRL_REG              uint64 = 0x500
const D0_U2U_STAT_REG              uint64 = 0x504
const D0_FLSH_CTRL_REG             uint64 = 0x508
const D0_LED_CONFIG_REG            uint64 = 0x1000
const D0_LED_SYSTEM_REG            uint64 = 0x1004
const D0_LED_FAN_0_REG             uint64 = 0x1008
const D0_LED_FAN_1_REG             uint64 = 0x100c
const D0_LED_CTRL_3_0_REG          uint64 = 0x2000
const D0_LED_CTRL_7_4_REG          uint64 = 0x2004
const D0_LED_CTRL_11_8_REG         uint64 = 0x2008
const D0_LED_CTRL_15_12_REG        uint64 = 0x200c
const D0_LED_CTRL_19_16_REG        uint64 = 0x2010
const D0_LED_CTRL_23_20_REG        uint64 = 0x2014
const D0_LED_CTRL_27_24_REG        uint64 = 0x2018
const D0_LED_CTRL_31_28_REG        uint64 = 0x201c
const D0_LED_CTRL_35_32_REG        uint64 = 0x2020
const D0_LED_CTRL_39_36_REG        uint64 = 0x2024
const D0_LED_CTRL_43_40_REG        uint64 = 0x2028
const D0_LED_CTRL_47_44_REG        uint64 = 0x202c
const D0_LED_CTRL_51_48_REG        uint64 = 0x2030
const D0_LED_CTRL_55_52_REG        uint64 = 0x2034
const D0_FP_SFP_CTRL_3_0_REG       uint64 = 0x3000
const D0_FP_SFP_CTRL_7_4_REG       uint64 = 0x3004
const D0_FP_SFP_CTRL_11_8_REG      uint64 = 0x3008
const D0_FP_SFP_CTRL_15_12_REG     uint64 = 0x300c
const D0_FP_SFP_CTRL_19_16_REG     uint64 = 0x3010
const D0_FP_SFP_CTRL_23_20_REG     uint64 = 0x3014
const D0_FP_SFP_CTRL_27_24_REG     uint64 = 0x3018
const D0_FP_SFP_CTRL_31_28_REG     uint64 = 0x301c
const D0_FP_SFP_CTRL_35_32_REG     uint64 = 0x3020
const D0_FP_SFP_CTRL_39_36_REG     uint64 = 0x3024
const D0_FP_SFP_CTRL_43_40_REG     uint64 = 0x3028
const D0_FP_SFP_CTRL_47_44_REG     uint64 = 0x302c
const D0_FP_SFP_STAT_3_0_REG       uint64 = 0x4000
const D0_FP_SFP_STAT_7_4_REG       uint64 = 0x4004
const D0_FP_SFP_STAT_11_8_REG      uint64 = 0x4008
const D0_FP_SFP_STAT_15_12_REG     uint64 = 0x400c
const D0_FP_SFP_STAT_19_16_REG     uint64 = 0x4010
const D0_FP_SFP_STAT_23_20_REG     uint64 = 0x4014
const D0_FP_SFP_STAT_27_24_REG     uint64 = 0x4018
const D0_FP_SFP_STAT_31_28_REG     uint64 = 0x401c
const D0_FP_SFP_STAT_35_32_REG     uint64 = 0x4020
const D0_FP_SFP_STAT_39_36_REG     uint64 = 0x4024
const D0_FP_SFP_STAT_43_40_REG     uint64 = 0x4028
const D0_FP_SFP_STAT_47_44_REG     uint64 = 0x402c
const D0_FP_QSFP_CTRL_51_48_REG    uint64 = 0x5000
const D0_FP_QSFP_CTRL_55_52_REG    uint64 = 0x5004
const D0_FP_QSFP_STAT_51_48_REG    uint64 = 0x6000
const D0_FP_QSFP_STAT_55_52_REG    uint64 = 0x6004

const D1_FPGA_REV_ID_REG           uint64 = 0x0
const D1_FPGA_DATECODE_REG         uint64 = 0x4
const D1_BOARD_REV_ID_REG          uint64 = 0x8
const D1_FUNC_CAP_0_REG            uint64 = 0xc
const D1_FUNC_CAP_1_REG            uint64 = 0x10
const D1_FUNC_CAP_2_REG            uint64 = 0x14
const D1_FUNC_CAP_3_REG            uint64 = 0x18
const D1_FUNC_CAP_4_REG            uint64 = 0x1c
const D1_FUNC_CAP_5_REG            uint64 = 0x20
const D1_FUNC_CAP_6_REG            uint64 = 0x24
const D1_FUNC_CAP_7_REG            uint64 = 0x28
const D1_SCRTCH_0_REG              uint64 = 0x80
const D1_SCRTCH_1_REG              uint64 = 0x84
const D1_SCRTCH_2_REG              uint64 = 0x88
const D1_SCRTCH_3_REG              uint64 = 0x8c
const D1_CFG_FLASH_CTRL_REG        uint64 = 0x200
const D1_CFG_FLASH_BAUD_RATE_REG   uint64 = 0x204
const D1_CFG_FLASH_CS_DELAY_REG    uint64 = 0x208
const D1_CFG_FLASH_READ_CAPTURE_REG uint64 = 0x20c
const D1_CFG_FLASH_PROTOCOL_REG    uint64 = 0x210
const D1_CFG_FLASH_READ_INST_REG   uint64 = 0x214
const D1_CFG_FLASH_WRITE_INST_REG  uint64 = 0x218
const D1_CFG_FLASH_CMD_SET_REG     uint64 = 0x21c
const D1_CFG_FLASH_CMD_CTRL_REG    uint64 = 0x220
const D1_CFG_FLASH_CMD_ADDR_REG    uint64 = 0x224
const D1_CFG_FLASH_WDATA0_REG      uint64 = 0x228
const D1_CFG_FLASH_WDATA1_REG      uint64 = 0x22c
const D1_CFG_FLASH_RDATA0_REG      uint64 = 0x230
const D1_CFG_FLASH_RDATA1_REG      uint64 = 0x234
const D1_DEV_MSI_0_PEND_REG        uint64 = 0x300
const D1_DEV_MSI_0_INT_EN_REG      uint64 = 0x304
const D1_DEV_MSI_1_PEND_REG        uint64 = 0x308
const D1_DEV_MSI_1_INT_EN_REG      uint64 = 0x30c
const D1_DEV_MSI_2_PEND_REG        uint64 = 0x310
const D1_DEV_MSI_2_INT_EN_REG      uint64 = 0x314
const D1_DEV_MSI_3_PEND_REG        uint64 = 0x318
const D1_DEV_MSI_3_INT_EN_REG      uint64 = 0x31c
const D1_DEV_MSI_4_PEND_REG        uint64 = 0x320
const D1_DEV_MSI_4_INT_EN_REG      uint64 = 0x324
const D1_DEV_MSI_5_PEND_REG        uint64 = 0x328
const D1_DEV_MSI_5_INT_EN_REG      uint64 = 0x32c
const D1_DEV_MSI_6_PEND_REG        uint64 = 0x330
const D1_DEV_MSI_6_INT_EN_REG      uint64 = 0x334
const D1_DEV_MSI_7_PEND_REG        uint64 = 0x338
const D1_DEV_MSI_7_INT_EN_REG      uint64 = 0x33c
const D1_PSU_CTRL_REG              uint64 = 0x400
const D1_PSU_STAT_REG              uint64 = 0x404
const D1_FAN_CTRL_REG              uint64 = 0x408
const D1_FAN_STAT_REG              uint64 = 0x40c
const D1_ELBA0_PWR_CTRL_REG        uint64 = 0x410
const D1_ELBA0_PWR_STAT_REG        uint64 = 0x414
const D1_ELBA1_PWR_CTRL_REG        uint64 = 0x418
const D1_ELBA1_PWR_STAT_REG        uint64 = 0x41c
const D1_TD3_PWR_CTRL_REG          uint64 = 0x420
const D1_TD3_PWR_STAT_REG          uint64 = 0x424
const D1_MISC_PWR_CTRL_REG         uint64 = 0x428
const D1_MISC_PWR_STAT_REG         uint64 = 0x42c
const D1_CPU_CTRL_REG              uint64 = 0x480
const D1_CPU_STAT_REG              uint64 = 0x484
const D1_ELBA_0_CTRL_REG           uint64 = 0x488
const D1_ELBA_0_STAT_REG           uint64 = 0x48c
const D1_ELBA_1_CTRL_REG           uint64 = 0x490
const D1_ELBA_1_STAT_REG           uint64 = 0x494
const D1_TD_CTRL_REG               uint64 = 0x498
const D1_TD_STAT_REG               uint64 = 0x49c
const D1_MISC_CTRL_REG             uint64 = 0x4a0
const D1_MISC_STAT_REG             uint64 = 0x4a4

const D2_FPGA_REV_ID_REG           uint64 = 0x0
const D2_FPGA_DATECODE_REG         uint64 = 0x4
const D2_BOARD_REV_ID_REG          uint64 = 0x8
const D2_FUNC_CAP_0_REG            uint64 = 0xc
const D2_FUNC_CAP_1_REG            uint64 = 0x10
const D2_FUNC_CAP_2_REG            uint64 = 0x14
const D2_FUNC_CAP_3_REG            uint64 = 0x18
const D2_FUNC_CAP_4_REG            uint64 = 0x1c
const D2_FUNC_CAP_5_REG            uint64 = 0x20
const D2_FUNC_CAP_6_REG            uint64 = 0x24
const D2_FUNC_CAP_7_REG            uint64 = 0x28
const D2_SCRTCH_0_REG              uint64 = 0x80
const D2_SCRTCH_1_REG              uint64 = 0x84
const D2_SCRTCH_2_REG              uint64 = 0x88
const D2_SCRTCH_3_REG              uint64 = 0x8c
const D2_DEV_MSI_0_PEND_REG        uint64 = 0x300
const D2_DEV_MSI_0_INT_EN_REG      uint64 = 0x304
const D2_DEV_MSI_1_PEND_REG        uint64 = 0x308
const D2_DEV_MSI_1_INT_EN_REG      uint64 = 0x30c
const D2_DEV_MSI_2_PEND_REG        uint64 = 0x310
const D2_DEV_MSI_2_INT_EN_REG      uint64 = 0x314
const D2_DEV_MSI_3_PEND_REG        uint64 = 0x318
const D2_DEV_MSI_3_INT_EN_REG      uint64 = 0x31c
const D2_DEV_MSI_4_PEND_REG        uint64 = 0x320
const D2_DEV_MSI_4_INT_EN_REG      uint64 = 0x324
const D2_DEV_MSI_5_PEND_REG        uint64 = 0x328
const D2_DEV_MSI_5_INT_EN_REG      uint64 = 0x32c
const D2_DEV_MSI_6_PEND_REG        uint64 = 0x330
const D2_DEV_MSI_6_INT_EN_REG      uint64 = 0x334
const D2_DEV_MSI_7_PEND_REG        uint64 = 0x338
const D2_DEV_MSI_7_INT_EN_REG      uint64 = 0x33c
const D2_SPI0_RXDATA_REG            uint64 = 0x400
const D2_SPI0_TXDATA_REG            uint64 = 0x404
const D2_SPI0_STATUS_REG            uint64 = 0x408
const D2_SPI0_CONTROL_REG           uint64 = 0x40c
const D2_SPI0_SEM_REG               uint64 = 0x410
const D2_SPI0_SLAVESEL_REG          uint64 = 0x414
const D2_SPI0_EOP_VALUE_REG         uint64 = 0x418
const D2_SPI0_MUXSEL_REG            uint64 = 0x41c
const D2_SPI1_RXDATA_REG            uint64 = 0x420
const D2_SPI1_TXDATA_REG            uint64 = 0x424
const D2_SPI1_STATUS_REG            uint64 = 0x428
const D2_SPI1_CONTROL_REG           uint64 = 0x42c
const D2_SPI1_SEM_REG               uint64 = 0x430
const D2_SPI1_SLAVESEL_REG          uint64 = 0x434
const D2_SPI1_EOP_VALUE_REG         uint64 = 0x438
const D2_SPI1_MUXSEL_REG            uint64 = 0x43c
const D2_SPI2_RXDATA_REG            uint64 = 0x440
const D2_SPI2_TXDATA_REG            uint64 = 0x444
const D2_SPI2_STATUS_REG            uint64 = 0x448
const D2_SPI2_CONTROL_REG           uint64 = 0x44c
const D2_SPI2_SEM_REG               uint64 = 0x450
const D2_SPI2_SLAVESEL_REG          uint64 = 0x454
const D2_SPI2_EOP_VALUE_REG         uint64 = 0x458
const D2_SPI2_MUXSEL_REG            uint64 = 0x45c
const D2_SPI3_RXDATA_REG            uint64 = 0x460
const D2_SPI3_TXDATA_REG            uint64 = 0x464
const D2_SPI3_STATUS_REG            uint64 = 0x468
const D2_SPI3_CONTROL_REG           uint64 = 0x46c
const D2_SPI3_SEM_REG               uint64 = 0x470
const D2_SPI3_SLAVESEL_REG          uint64 = 0x474
const D2_SPI3_EOP_VALUE_REG         uint64 = 0x478
const D2_SPI3_MUXSEL_REG            uint64 = 0x47c
const D2_SPI4_RXDATA_REG            uint64 = 0x480
const D2_SPI4_TXDATA_REG            uint64 = 0x484
const D2_SPI4_STATUS_REG            uint64 = 0x488
const D2_SPI4_CONTROL_REG           uint64 = 0x48c
const D2_SPI4_SEM_REG               uint64 = 0x490
const D2_SPI4_SLAVESEL_REG          uint64 = 0x494
const D2_SPI4_EOP_VALUE_REG         uint64 = 0x498
const D2_SPI4_MUXSEL_REG            uint64 = 0x49c
const D2_SPI5_RXDATA_REG            uint64 = 0x4a0
const D2_SPI5_TXDATA_REG            uint64 = 0x4a4
const D2_SPI5_STATUS_REG            uint64 = 0x4a8
const D2_SPI5_CONTROL_REG           uint64 = 0x4ac
const D2_SPI5_SEM_REG               uint64 = 0x4b0
const D2_SPI5_SLAVESEL_REG          uint64 = 0x4b4
const D2_SPI5_EOP_VALUE_REG         uint64 = 0x4b8
const D2_SPI5_MUXSEL_REG            uint64 = 0x4bc
const D2_SPI6_RXDATA_REG            uint64 = 0x4c0
const D2_SPI6_TXDATA_REG            uint64 = 0x4c4
const D2_SPI6_STATUS_REG            uint64 = 0x4c8
const D2_SPI6_CONTROL_REG           uint64 = 0x4cc
const D2_SPI6_SEM_REG               uint64 = 0x4d0
const D2_SPI6_SLAVESEL_REG          uint64 = 0x4d4
const D2_SPI6_EOP_VALUE_REG         uint64 = 0x4d8
const D2_SPI6_MUXSEL_REG            uint64 = 0x4dc
const D2_SPI7_RXDATA_REG            uint64 = 0x4e0
const D2_SPI7_TXDATA_REG            uint64 = 0x4e4
const D2_SPI7_STATUS_REG            uint64 = 0x4e8
const D2_SPI7_CONTROL_REG           uint64 = 0x4ec
const D2_SPI7_SEM_REG               uint64 = 0x4f0
const D2_SPI7_SLAVESEL_REG          uint64 = 0x4f4
const D2_SPI7_EOP_VALUE_REG         uint64 = 0x4f8
const D2_SPI7_MUXSEL_REG            uint64 = 0x4fc


const D3_FPGA_REV_ID_REG           uint64 = 0x0
const D3_FPGA_DATECODE_REG         uint64 = 0x4
const D3_BOARD_REV_ID_REG          uint64 = 0x8
const D3_FUNC_CAP_0_REG            uint64 = 0xc
const D3_FUNC_CAP_1_REG            uint64 = 0x10
const D3_FUNC_CAP_2_REG            uint64 = 0x14
const D3_FUNC_CAP_3_REG            uint64 = 0x18
const D3_FUNC_CAP_4_REG            uint64 = 0x1c
const D3_FUNC_CAP_5_REG            uint64 = 0x20
const D3_FUNC_CAP_6_REG            uint64 = 0x24
const D3_FUNC_CAP_7_REG            uint64 = 0x28
const D3_RSVD                      uint64 = 0x2c
const D3_SCRTCH_0_REG              uint64 = 0x80
const D3_SCRTCH_1_REG              uint64 = 0x84
const D3_SCRTCH_2_REG              uint64 = 0x88
const D3_SCRTCH_3_REG              uint64 = 0x8c
const D3_DEV_MSI_0_PEND_REG        uint64 = 0x300
const D3_DEV_MSI_0_INT_EN_REG      uint64 = 0x304
const D3_DEV_MSI_1_PEND_REG        uint64 = 0x308
const D3_DEV_MSI_1_INT_EN_REG      uint64 = 0x30c
const D3_DEV_MSI_2_PEND_REG        uint64 = 0x310
const D3_DEV_MSI_2_INT_EN_REG      uint64 = 0x314
const D3_DEV_MSI_3_PEND_REG        uint64 = 0x318
const D3_DEV_MSI_3_INT_EN_REG      uint64 = 0x31c
const D3_DEV_MSI_4_PEND_REG        uint64 = 0x320
const D3_DEV_MSI_4_INT_EN_REG      uint64 = 0x324
const D3_DEV_MSI_5_PEND_REG        uint64 = 0x328
const D3_DEV_MSI_5_INT_EN_REG      uint64 = 0x32c
const D3_DEV_MSI_6_PEND_REG        uint64 = 0x330
const D3_DEV_MSI_6_INT_EN_REG      uint64 = 0x334
const D3_DEV_MSI_7_PEND_REG        uint64 = 0x338
const D3_DEV_MSI_7_INT_EN_REG      uint64 = 0x33c
const D3_I2C_CH0_PRSCL_LO_REG          uint64 = 0x1000
const D3_I2C_CH0_PRSCL_HI_REG          uint64 = 0x1004
const D3_I2C_CH0_CTRL_REG              uint64 = 0x1008
const D3_I2C_CH0_DATA_REG              uint64 = 0x100c
const D3_I2C_CH0_CMD_REG               uint64 = 0x1010
const D3_I2C_CH0_STAT_REG              uint64 = 0x1010
const D3_I2C_CH0_MUX_SEL_REG           uint64 = 0x1014
const D3_I2C_CH0_RST_REG               uint64 = 0x1018
const D3_I2C_CH0_SEM_REG               uint64 = 0x101c
const D3_I2C_CH1_PRSCL_LO_REG          uint64 = 0x1020
const D3_I2C_CH1_PRSCL_HI_REG          uint64 = 0x1024
const D3_I2C_CH1_CTRL_REG              uint64 = 0x1028
const D3_I2C_CH1_DATA_REG              uint64 = 0x102c
const D3_I2C_CH1_CMD_REG               uint64 = 0x1030
const D3_I2C_CH1_STAT_REG              uint64 = 0x1030
const D3_I2C_CH1_MUX_SEL_REG           uint64 = 0x1034
const D3_I2C_CH1_RST_REG               uint64 = 0x1038
const D3_I2C_CH1_SEM_REG               uint64 = 0x103c
const D3_I2C_CH2_PRSCL_LO_REG          uint64 = 0x1040
const D3_I2C_CH2_PRSCL_HI_REG          uint64 = 0x1044
const D3_I2C_CH2_CTRL_REG              uint64 = 0x1048
const D3_I2C_CH2_DATA_REG              uint64 = 0x104c
const D3_I2C_CH2_CMD_REG               uint64 = 0x1050
const D3_I2C_CH2_STAT_REG              uint64 = 0x1050
const D3_I2C_CH2_MUX_SEL_REG           uint64 = 0x1054
const D3_I2C_CH2_RST_REG               uint64 = 0x1058
const D3_I2C_CH2_SEM_REG               uint64 = 0x105c
const D3_I2C_CH3_PRSCL_LO_REG          uint64 = 0x1060
const D3_I2C_CH3_PRSCL_HI_REG          uint64 = 0x1064
const D3_I2C_CH3_STAT_REG              uint64 = 0x1068
const D3_I2C_CH3_DATA_REG              uint64 = 0x106C
const D3_I2C_CH3_CMD_REG               uint64 = 0x1070
const D3_I2C_CH3_CTRL_REG              uint64 = 0x1070
const D3_I2C_CH3_MUX_SEL_REG           uint64 = 0x1074
const D3_I2C_CH3_RST_REG               uint64 = 0x1078
const D3_I2C_CH3_SEM_REG               uint64 = 0x107C
const D3_I2C_CH4_PRSCL_LO_REG          uint64 = 0x1080
const D3_I2C_CH4_PRSCL_HI_REG          uint64 = 0x1084
const D3_I2C_CH4_CTRL_REG              uint64 = 0x1088
const D3_I2C_CH4_DATA_REG              uint64 = 0x108c
const D3_I2C_CH4_CMD_REG               uint64 = 0x1090
const D3_I2C_CH4_STAT_REG              uint64 = 0x1090
const D3_I2C_CH4_MUX_SEL_REG           uint64 = 0x1094
const D3_I2C_CH4_RST_REG               uint64 = 0x1098
const D3_I2C_CH4_SEM_REG               uint64 = 0x109c
const D3_I2C_CH5_PRSCL_LO_REG          uint64 = 0x10a0
const D3_I2C_CH5_PRSCL_HI_REG          uint64 = 0x10a4
const D3_I2C_CH5_CTRL_REG              uint64 = 0x10a8
const D3_I2C_CH5_DATA_REG              uint64 = 0x10ac
const D3_I2C_CH5_CMD_REG               uint64 = 0x10b0
const D3_I2C_CH5_STAT_REG              uint64 = 0x10b0
const D3_I2C_CH5_MUX_SEL_REG           uint64 = 0x10b4
const D3_I2C_CH5_RST_REG               uint64 = 0x10b8
const D3_I2C_CH5_SEM_REG               uint64 = 0x10bc
const D3_I2C_CH6_PRSCL_LO_REG          uint64 = 0x10c0
const D3_I2C_CH6_PRSCL_HI_REG          uint64 = 0x10c4
const D3_I2C_CH6_CTRL_REG              uint64 = 0x10c8
const D3_I2C_CH6_DATA_REG              uint64 = 0x10cc
const D3_I2C_CH6_CMD_REG               uint64 = 0x10d0
const D3_I2C_CH6_STAT_REG              uint64 = 0x10d0
const D3_I2C_CH6_MUX_SEL_REG           uint64 = 0x10d4
const D3_I2C_CH6_RST_REG               uint64 = 0x10d8
const D3_I2C_CH6_SEM_REG               uint64 = 0x10dc
const D3_I2C_CH7_PRSCL_LO_REG          uint64 = 0x10e0
const D3_I2C_CH7_PRSCL_HI_REG          uint64 = 0x10e4
const D3_I2C_CH7_CTRL_REG              uint64 = 0x10e8
const D3_I2C_CH7_DATA_REG              uint64 = 0x10ec
const D3_I2C_CH7_CMD_REG               uint64 = 0x10f0
const D3_I2C_CH7_STAT_REG              uint64 = 0x10f0
const D3_I2C_CH7_MUX_SEL_REG           uint64 = 0x10f4
const D3_I2C_CH7_RST_REG               uint64 = 0x10f8
const D3_I2C_CH7_SEM_REG               uint64 = 0x10fc
const D3_I2C_CH8_PRSCL_LO_REG          uint64 = 0x1100
const D3_I2C_CH8_PRSCL_HI_REG          uint64 = 0x1104
const D3_I2C_CH8_CTRL_REG              uint64 = 0x1108
const D3_I2C_CH8_DATA_REG              uint64 = 0x110c
const D3_I2C_CH8_CMD_REG               uint64 = 0x1110
const D3_I2C_CH8_STAT_REG              uint64 = 0x1110
const D3_I2C_CH8_MUX_SEL_REG           uint64 = 0x1114
const D3_I2C_CH8_RST_REG               uint64 = 0x1118
const D3_I2C_CH8_SEM_REG               uint64 = 0x111c
const D3_I2C_CH9_PRSCL_LO_REG          uint64 = 0x1120
const D3_I2C_CH9_PRSCL_HI_REG          uint64 = 0x1124
const D3_I2C_CH9_CTRL_REG              uint64 = 0x1128
const D3_I2C_CH9_DATA_REG              uint64 = 0x112c
const D3_I2C_CH9_RX_REG                uint64 = 0x112c
const D3_I2C_CH9_CMD_REG               uint64 = 0x1130
const D3_I2C_CH9_STAT_REG              uint64 = 0x1130
const D3_I2C_CH9_MUX_SEL_REG           uint64 = 0x1134
const D3_I2C_CH9_RST_REG               uint64 = 0x1138
const D3_I2C_CH9_SEM_REG               uint64 = 0x113c
const D3_I2C_CH10_PRSCL_LO_REG          uint64 = 0x1140
const D3_I2C_CH10_PRSCL_HI_REG          uint64 = 0x1144
const D3_I2C_CH10_CTRL_REG              uint64 = 0x1148
const D3_I2C_CH10_DATA_REG              uint64 = 0x114c
const D3_I2C_CH10_CMD_REG               uint64 = 0x1150
const D3_I2C_CH10_STAT_REG              uint64 = 0x1150
const D3_I2C_CH10_MUX_SEL_REG           uint64 = 0x1154
const D3_I2C_CH10_RST_REG               uint64 = 0x1158
const D3_I2C_CH10_SEM_REG               uint64 = 0x115c
const D3_I2C_CH11_PRSCL_LO_REG          uint64 = 0x1160
const D3_I2C_CH11_PRSCL_HI_REG          uint64 = 0x1164
const D3_I2C_CH11_CTRL_REG              uint64 = 0x1168
const D3_I2C_CH11_DATA_REG              uint64 = 0x116c
const D3_I2C_CH11_CMD_REG               uint64 = 0x1170
const D3_I2C_CH11_STAT_REG              uint64 = 0x1170
const D3_I2C_CH11_MUX_SEL_REG           uint64 = 0x1174
const D3_I2C_CH11_RST_REG               uint64 = 0x1178
const D3_I2C_CH11_SEM_REG               uint64 = 0x117c
const D3_I2C_CH12_PRSCL_LO_REG          uint64 = 0x1180
const D3_I2C_CH12_PRSCL_HI_REG          uint64 = 0x1184
const D3_I2C_CH12_CTRL_REG              uint64 = 0x1188
const D3_I2C_CH12_DATA_REG              uint64 = 0x118c
const D3_I2C_CH12_CMD_REG               uint64 = 0x1190
const D3_I2C_CH12_STAT_REG              uint64 = 0x1190
const D3_I2C_CH12_MUX_SEL_REG           uint64 = 0x1194
const D3_I2C_CH12_RST_REG               uint64 = 0x1198
const D3_I2C_CH12_SEM_REG               uint64 = 0x119c
const D3_I2C_CH13_PRSCL_LO_REG          uint64 = 0x11a0
const D3_I2C_CH13_PRSCL_HI_REG          uint64 = 0x11a4
const D3_I2C_CH13_CTRL_REG              uint64 = 0x11a8
const D3_I2C_CH13_DATA_REG              uint64 = 0x11ac
const D3_I2C_CH13_CMD_REG               uint64 = 0x11b0
const D3_I2C_CH13_STAT_REG              uint64 = 0x11b0
const D3_I2C_CH13_MUX_SEL_REG           uint64 = 0x11b4
const D3_I2C_CH13_RST_REG               uint64 = 0x11b8
const D3_I2C_CH13_SEM_REG               uint64 = 0x11bc
const D3_I2C_CH14_PRSCL_LO_REG          uint64 = 0x11c0
const D3_I2C_CH14_PRSCL_HI_REG          uint64 = 0x11c4
const D3_I2C_CH14_CTRL_REG              uint64 = 0x11c8
const D3_I2C_CH14_DATA_REG              uint64 = 0x11cc
const D3_I2C_CH14_CMD_REG               uint64 = 0x11d0
const D3_I2C_CH14_STAT_REG              uint64 = 0x11d0
const D3_I2C_CH14_MUX_SEL_REG           uint64 = 0x11d4
const D3_I2C_CH14_RST_REG               uint64 = 0x11d8
const D3_I2C_CH14_SEM_REG               uint64 = 0x11dc
const D3_I2C_CH15_PRSCL_LO_REG          uint64 = 0x11e0
const D3_I2C_CH15_PRSCL_HI_REG          uint64 = 0x11e4
const D3_I2C_CH15_CTRL_REG              uint64 = 0x11e8
const D3_I2C_CH15_DATA_REG              uint64 = 0x11ec
const D3_I2C_CH15_CMD_REG               uint64 = 0x11f0
const D3_I2C_CH15_STAT_REG              uint64 = 0x11f0
const D3_I2C_CH15_MUX_SEL_REG           uint64 = 0x11f4
const D3_I2C_CH15_RST_REG               uint64 = 0x11f8
const D3_I2C_CH15_SEM_REG               uint64 = 0x11fc
const D3_I2C_CH16_PRSCL_LO_REG          uint64 = 0x1200
const D3_I2C_CH16_PRSCL_HI_REG          uint64 = 0x1204
const D3_I2C_CH16_CTRL_REG              uint64 = 0x1208
const D3_I2C_CH16_DATA_REG              uint64 = 0x120c
const D3_I2C_CH16_CMD_REG               uint64 = 0x1210
const D3_I2C_CH16_STAT_REG              uint64 = 0x1210
const D3_I2C_CH16_MUX_SEL_REG           uint64 = 0x1214
const D3_I2C_CH16_RST_REG               uint64 = 0x1218
const D3_I2C_CH16_SEM_REG               uint64 = 0x121c



//awk '{print "D3_" $0}' reg3.txt
//awk '{ printf "const %-28s uint64 = 0x%x\n", $1, $2 }' ./reg3_.txt
//awk '{ printf "    TAOR_FPGA_REGISTERS{\"D3_%-22s\",             D3_%s},\n", $1, $1 }' ./reg3_.txt
var TAOR_DEV0_REGISTERS = []TAOR_FPGA_REGISTERS {
    TAOR_FPGA_REGISTERS{"D0_FPGA_REV_ID_REG       ",             D0_FPGA_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D0_FPGA_DATECODE_REG     ",             D0_FPGA_DATECODE_REG},
    TAOR_FPGA_REGISTERS{"D0_BOARD_REV_ID_REG      ",             D0_BOARD_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_0_REG        ",             D0_FUNC_CAP_0_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_1_REG        ",             D0_FUNC_CAP_1_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_2_REG        ",             D0_FUNC_CAP_2_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_3_REG        ",             D0_FUNC_CAP_3_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_4_REG        ",             D0_FUNC_CAP_4_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_5_REG        ",             D0_FUNC_CAP_5_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_6_REG        ",             D0_FUNC_CAP_6_REG},
    TAOR_FPGA_REGISTERS{"D0_FUNC_CAP_7_REG        ",             D0_FUNC_CAP_7_REG},
    TAOR_FPGA_REGISTERS{"D0_SCRTCH_0_REG          ",             D0_SCRTCH_0_REG},
    TAOR_FPGA_REGISTERS{"D0_SCRTCH_1_REG          ",             D0_SCRTCH_1_REG},
    TAOR_FPGA_REGISTERS{"D0_SCRTCH_2_REG          ",             D0_SCRTCH_2_REG},
    TAOR_FPGA_REGISTERS{"D0_SCRTCH_3_REG          ",             D0_SCRTCH_3_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_DEBUG_0_REG       ",             D0_LED_DEBUG_0_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_DEBUG_1_REG       ",             D0_LED_DEBUG_1_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_DEBUG_2_REG       ",             D0_LED_DEBUG_2_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_DEBUG_3_REG       ",             D0_LED_DEBUG_3_REG},
    TAOR_FPGA_REGISTERS{"D0_DEBUG_0_REG           ",             D0_DEBUG_0_REG},
    TAOR_FPGA_REGISTERS{"D0_DEBUG_1_REG           ",             D0_DEBUG_1_REG},
    TAOR_FPGA_REGISTERS{"D0_DEBUG_2_REG           ",             D0_DEBUG_2_REG},
    TAOR_FPGA_REGISTERS{"D0_DEBUG_3_REG           ",             D0_DEBUG_3_REG},
    TAOR_FPGA_REGISTERS{"D0_RESET_CAUSE_0_REG     ",             D0_RESET_CAUSE_0_REG},
    TAOR_FPGA_REGISTERS{"D0_RESET_CAUSE_1_REG     ",             D0_RESET_CAUSE_1_REG},
    TAOR_FPGA_REGISTERS{"D0_RESET_CAUSE_2_REG     ",             D0_RESET_CAUSE_2_REG},
    TAOR_FPGA_REGISTERS{"D0_RESET_CAUSE_3_REG     ",             D0_RESET_CAUSE_3_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_0_PEND_REG    ",             D0_DEV_MSI_0_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_0_INT_EN_REG  ",             D0_DEV_MSI_0_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_1_PEND_REG    ",             D0_DEV_MSI_1_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_1_INT_EN_REG  ",             D0_DEV_MSI_1_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_2_PEND_REG    ",             D0_DEV_MSI_2_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_2_INT_EN_REG  ",             D0_DEV_MSI_2_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_3_PEND_REG    ",             D0_DEV_MSI_3_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_3_INT_EN_REG  ",             D0_DEV_MSI_3_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_4_PEND_REG    ",             D0_DEV_MSI_4_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_4_INT_EN_REG  ",             D0_DEV_MSI_4_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_5_PEND_REG    ",             D0_DEV_MSI_5_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_5_INT_EN_REG  ",             D0_DEV_MSI_5_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_6_PEND_REG    ",             D0_DEV_MSI_6_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_6_INT_EN_REG  ",             D0_DEV_MSI_6_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_7_PEND_REG    ",             D0_DEV_MSI_7_PEND_REG},
    TAOR_FPGA_REGISTERS{"D0_DEV_MSI_7_INT_EN_REG  ",             D0_DEV_MSI_7_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_REG         ",             D0_MBOX_STAT_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_PLRTY_REG   ",             D0_MBOX_STAT_PLRTY_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_EDG_LVL_REG ",             D0_MBOX_STAT_EDG_LVL_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_INT_EN_REG  ",             D0_MBOX_STAT_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_INT_STAT_REG",             D0_MBOX_STAT_INT_STAT_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_STAT_INT_CLR_REG ",             D0_MBOX_STAT_INT_CLR_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_0_DATA_REG       ",             D0_MBOX_0_DATA_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_1_DATA_REG       ",             D0_MBOX_1_DATA_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_2_DATA_REG       ",             D0_MBOX_2_DATA_REG},
    TAOR_FPGA_REGISTERS{"D0_MBOX_3_DATA_REG       ",             D0_MBOX_3_DATA_REG},
    TAOR_FPGA_REGISTERS{"D0_U2U_CTRL_REG          ",             D0_U2U_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D0_U2U_STAT_REG          ",             D0_U2U_STAT_REG},
    TAOR_FPGA_REGISTERS{"D0_FLSH_CTRL_REG         ",             D0_FLSH_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CONFIG_REG        ",             D0_LED_CONFIG_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_SYSTEM_REG        ",             D0_LED_SYSTEM_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_FAN_0_REG         ",             D0_LED_FAN_0_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_FAN_1_REG         ",             D0_LED_FAN_1_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_3_0_REG      ",             D0_LED_CTRL_3_0_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_7_4_REG      ",             D0_LED_CTRL_7_4_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_11_8_REG     ",             D0_LED_CTRL_11_8_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_15_12_REG    ",             D0_LED_CTRL_15_12_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_19_16_REG    ",             D0_LED_CTRL_19_16_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_23_20_REG    ",             D0_LED_CTRL_23_20_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_27_24_REG    ",             D0_LED_CTRL_27_24_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_31_28_REG    ",             D0_LED_CTRL_31_28_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_35_32_REG    ",             D0_LED_CTRL_35_32_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_39_36_REG    ",             D0_LED_CTRL_39_36_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_43_40_REG    ",             D0_LED_CTRL_43_40_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_47_44_REG    ",             D0_LED_CTRL_47_44_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_51_48_REG    ",             D0_LED_CTRL_51_48_REG},
    TAOR_FPGA_REGISTERS{"D0_LED_CTRL_55_52_REG    ",             D0_LED_CTRL_55_52_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_3_0_REG   ",             D0_FP_SFP_CTRL_3_0_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_7_4_REG   ",             D0_FP_SFP_CTRL_7_4_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_11_8_REG  ",             D0_FP_SFP_CTRL_11_8_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_15_12_REG ",             D0_FP_SFP_CTRL_15_12_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_19_16_REG ",             D0_FP_SFP_CTRL_19_16_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_23_20_REG ",             D0_FP_SFP_CTRL_23_20_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_27_24_REG ",             D0_FP_SFP_CTRL_27_24_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_31_28_REG ",             D0_FP_SFP_CTRL_31_28_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_35_32_REG ",             D0_FP_SFP_CTRL_35_32_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_39_36_REG ",             D0_FP_SFP_CTRL_39_36_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_43_40_REG ",             D0_FP_SFP_CTRL_43_40_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_CTRL_47_44_REG ",             D0_FP_SFP_CTRL_47_44_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_3_0_REG   ",             D0_FP_SFP_STAT_3_0_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_7_4_REG   ",             D0_FP_SFP_STAT_7_4_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_11_8_REG  ",             D0_FP_SFP_STAT_11_8_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_15_12_REG ",             D0_FP_SFP_STAT_15_12_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_19_16_REG ",             D0_FP_SFP_STAT_19_16_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_23_20_REG ",             D0_FP_SFP_STAT_23_20_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_27_24_REG ",             D0_FP_SFP_STAT_27_24_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_31_28_REG ",             D0_FP_SFP_STAT_31_28_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_35_32_REG ",             D0_FP_SFP_STAT_35_32_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_39_36_REG ",             D0_FP_SFP_STAT_39_36_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_43_40_REG ",             D0_FP_SFP_STAT_43_40_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_SFP_STAT_47_44_REG ",             D0_FP_SFP_STAT_47_44_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_QSFP_CTRL_51_48_REG",             D0_FP_QSFP_CTRL_51_48_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_QSFP_CTRL_55_52_REG",             D0_FP_QSFP_CTRL_55_52_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_QSFP_STAT_51_48_REG",             D0_FP_QSFP_STAT_51_48_REG},
    TAOR_FPGA_REGISTERS{"D0_FP_QSFP_STAT_55_52_REG",             D0_FP_QSFP_STAT_55_52_REG},
} 



var TAOR_DEV1_REGISTERS = []TAOR_FPGA_REGISTERS {
    TAOR_FPGA_REGISTERS{"D1_FPGA_REV_ID_REG       ",             D1_FPGA_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D1_FPGA_DATECODE_REG     ",             D1_FPGA_DATECODE_REG},
    TAOR_FPGA_REGISTERS{"D1_BOARD_REV_ID_REG      ",             D1_BOARD_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_0_REG        ",             D1_FUNC_CAP_0_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_1_REG        ",             D1_FUNC_CAP_1_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_2_REG        ",             D1_FUNC_CAP_2_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_3_REG        ",             D1_FUNC_CAP_3_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_4_REG        ",             D1_FUNC_CAP_4_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_5_REG        ",             D1_FUNC_CAP_5_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_6_REG        ",             D1_FUNC_CAP_6_REG},
    TAOR_FPGA_REGISTERS{"D1_FUNC_CAP_7_REG        ",             D1_FUNC_CAP_7_REG},
    TAOR_FPGA_REGISTERS{"D1_SCRTCH_0_REG          ",             D1_SCRTCH_0_REG},
    TAOR_FPGA_REGISTERS{"D1_SCRTCH_1_REG          ",             D1_SCRTCH_1_REG},
    TAOR_FPGA_REGISTERS{"D1_SCRTCH_2_REG          ",             D1_SCRTCH_2_REG},
    TAOR_FPGA_REGISTERS{"D1_SCRTCH_3_REG          ",             D1_SCRTCH_3_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_CTRL_REG        ",             D1_CFG_FLASH_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_BAUD_RATE_REG   ",            D1_CFG_FLASH_BAUD_RATE_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_CS_DELAY_REG    ",             D1_CFG_FLASH_CS_DELAY_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_READ_CAPTURE_REG",          D1_CFG_FLASH_READ_CAPTURE_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_PROTOCOL_REG    ",             D1_CFG_FLASH_PROTOCOL_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_READ_INST_REG   ",            D1_CFG_FLASH_READ_INST_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_WRITE_INST_REG  ",           D1_CFG_FLASH_WRITE_INST_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_CMD_SET_REG     ",             D1_CFG_FLASH_CMD_SET_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_CMD_CTRL_REG    ",             D1_CFG_FLASH_CMD_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_CMD_ADDR_REG    ",             D1_CFG_FLASH_CMD_ADDR_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_WDATA0_REG      ",             D1_CFG_FLASH_WDATA0_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_WDATA1_REG      ",             D1_CFG_FLASH_WDATA1_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_RDATA0_REG      ",             D1_CFG_FLASH_RDATA0_REG},
    TAOR_FPGA_REGISTERS{"D1_CFG_FLASH_RDATA1_REG      ",             D1_CFG_FLASH_RDATA1_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_0_PEND_REG    ",             D1_DEV_MSI_0_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_0_INT_EN_REG  ",             D1_DEV_MSI_0_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_1_PEND_REG    ",             D1_DEV_MSI_1_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_1_INT_EN_REG  ",             D1_DEV_MSI_1_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_2_PEND_REG    ",             D1_DEV_MSI_2_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_2_INT_EN_REG  ",             D1_DEV_MSI_2_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_3_PEND_REG    ",             D1_DEV_MSI_3_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_3_INT_EN_REG  ",             D1_DEV_MSI_3_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_4_PEND_REG    ",             D1_DEV_MSI_4_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_4_INT_EN_REG  ",             D1_DEV_MSI_4_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_5_PEND_REG    ",             D1_DEV_MSI_5_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_5_INT_EN_REG  ",             D1_DEV_MSI_5_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_6_PEND_REG    ",             D1_DEV_MSI_6_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_6_INT_EN_REG  ",             D1_DEV_MSI_6_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_7_PEND_REG    ",             D1_DEV_MSI_7_PEND_REG},
    TAOR_FPGA_REGISTERS{"D1_DEV_MSI_7_INT_EN_REG  ",             D1_DEV_MSI_7_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D1_PSU_CTRL_REG          ",             D1_PSU_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_PSU_STAT_REG          ",             D1_PSU_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_FAN_CTRL_REG          ",             D1_FAN_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_FAN_STAT_REG          ",             D1_FAN_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA0_PWR_CTRL_REG    ",             D1_ELBA0_PWR_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA0_PWR_STAT_REG    ",             D1_ELBA0_PWR_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA1_PWR_CTRL_REG    ",             D1_ELBA1_PWR_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA1_PWR_STAT_REG    ",             D1_ELBA1_PWR_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_TD3_PWR_CTRL_REG      ",             D1_TD3_PWR_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_TD3_PWR_STAT_REG      ",             D1_TD3_PWR_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_MISC_PWR_CTRL_REG     ",             D1_MISC_PWR_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_MISC_PWR_STAT_REG     ",             D1_MISC_PWR_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_CPU_CTRL_REG          ",             D1_CPU_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_CPU_STAT_REG          ",             D1_CPU_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA_0_CTRL_REG       ",             D1_ELBA_0_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA_0_STAT_REG       ",             D1_ELBA_0_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA_1_CTRL_REG       ",             D1_ELBA_1_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_ELBA_1_STAT_REG       ",             D1_ELBA_1_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_TD_CTRL_REG           ",             D1_TD_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_TD_STAT_REG           ",             D1_TD_STAT_REG},
    TAOR_FPGA_REGISTERS{"D1_MISC_CTRL_REG         ",             D1_MISC_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D1_MISC_STAT_REG         ",             D1_MISC_STAT_REG},
}



var TAOR_DEV2_REGISTERS = []TAOR_FPGA_REGISTERS {
    TAOR_FPGA_REGISTERS{"D2_FPGA_REV_ID_REG       ",             D2_FPGA_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D2_FPGA_DATECODE_REG     ",             D2_FPGA_DATECODE_REG},
    TAOR_FPGA_REGISTERS{"D2_BOARD_REV_ID_REG      ",             D2_BOARD_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_0_REG        ",             D2_FUNC_CAP_0_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_1_REG        ",             D2_FUNC_CAP_1_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_2_REG        ",             D2_FUNC_CAP_2_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_3_REG        ",             D2_FUNC_CAP_3_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_4_REG        ",             D2_FUNC_CAP_4_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_5_REG        ",             D2_FUNC_CAP_5_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_6_REG        ",             D2_FUNC_CAP_6_REG},
    TAOR_FPGA_REGISTERS{"D2_FUNC_CAP_7_REG        ",             D2_FUNC_CAP_7_REG},
    TAOR_FPGA_REGISTERS{"D2_SCRTCH_0_REG          ",             D2_SCRTCH_0_REG},
    TAOR_FPGA_REGISTERS{"D2_SCRTCH_1_REG          ",             D2_SCRTCH_1_REG},
    TAOR_FPGA_REGISTERS{"D2_SCRTCH_2_REG          ",             D2_SCRTCH_2_REG},
    TAOR_FPGA_REGISTERS{"D2_SCRTCH_3_REG          ",             D2_SCRTCH_3_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_0_PEND_REG    ",             D2_DEV_MSI_0_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_0_INT_EN_REG  ",             D2_DEV_MSI_0_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_1_PEND_REG    ",             D2_DEV_MSI_1_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_1_INT_EN_REG  ",             D2_DEV_MSI_1_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_2_PEND_REG    ",             D2_DEV_MSI_2_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_2_INT_EN_REG  ",             D2_DEV_MSI_2_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_3_PEND_REG    ",             D2_DEV_MSI_3_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_3_INT_EN_REG  ",             D2_DEV_MSI_3_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_4_PEND_REG    ",             D2_DEV_MSI_4_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_4_INT_EN_REG  ",             D2_DEV_MSI_4_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_5_PEND_REG    ",             D2_DEV_MSI_5_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_5_INT_EN_REG  ",             D2_DEV_MSI_5_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_6_PEND_REG    ",             D2_DEV_MSI_6_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_6_INT_EN_REG  ",             D2_DEV_MSI_6_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_7_PEND_REG    ",             D2_DEV_MSI_7_PEND_REG},
    TAOR_FPGA_REGISTERS{"D2_DEV_MSI_7_INT_EN_REG  ",             D2_DEV_MSI_7_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_RXDATA_REG        ",             D2_SPI0_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_TXDATA_REG        ",             D2_SPI0_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_STATUS_REG        ",             D2_SPI0_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_CONTROL_REG       ",             D2_SPI0_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_SEM_REG           ",             D2_SPI0_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_SLAVESEL_REG      ",             D2_SPI0_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_EOP_VALUE_REG     ",             D2_SPI0_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI0_MUXSEL_REG        ",             D2_SPI0_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_RXDATA_REG        ",             D2_SPI1_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_TXDATA_REG        ",             D2_SPI1_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_STATUS_REG        ",             D2_SPI1_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_CONTROL_REG       ",             D2_SPI1_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_SEM_REG           ",             D2_SPI1_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_SLAVESEL_REG      ",             D2_SPI1_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_EOP_VALUE_REG     ",             D2_SPI1_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI1_MUXSEL_REG        ",             D2_SPI1_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_RXDATA_REG        ",             D2_SPI2_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_TXDATA_REG        ",             D2_SPI2_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_STATUS_REG        ",             D2_SPI2_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_CONTROL_REG       ",             D2_SPI2_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_SEM_REG           ",             D2_SPI2_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_SLAVESEL_REG      ",             D2_SPI2_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_EOP_VALUE_REG     ",             D2_SPI2_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI2_MUXSEL_REG        ",             D2_SPI2_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_RXDATA_REG        ",             D2_SPI3_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_TXDATA_REG        ",             D2_SPI3_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_STATUS_REG        ",             D2_SPI3_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_CONTROL_REG       ",             D2_SPI3_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_SEM_REG           ",             D2_SPI3_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_SLAVESEL_REG      ",             D2_SPI3_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_EOP_VALUE_REG     ",             D2_SPI3_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI3_MUXSEL_REG        ",             D2_SPI3_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_RXDATA_REG        ",             D2_SPI4_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_TXDATA_REG        ",             D2_SPI4_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_STATUS_REG        ",             D2_SPI4_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_CONTROL_REG       ",             D2_SPI4_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_SEM_REG           ",             D2_SPI4_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_SLAVESEL_REG      ",             D2_SPI4_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_EOP_VALUE_REG     ",             D2_SPI4_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI4_MUXSEL_REG        ",             D2_SPI4_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_RXDATA_REG        ",             D2_SPI5_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_TXDATA_REG        ",             D2_SPI5_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_STATUS_REG        ",             D2_SPI5_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_CONTROL_REG       ",             D2_SPI5_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_SEM_REG           ",             D2_SPI5_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_SLAVESEL_REG      ",             D2_SPI5_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_EOP_VALUE_REG     ",             D2_SPI5_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI5_MUXSEL_REG        ",             D2_SPI5_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_RXDATA_REG        ",             D2_SPI6_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_TXDATA_REG        ",             D2_SPI6_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_STATUS_REG        ",             D2_SPI6_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_CONTROL_REG       ",             D2_SPI6_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_SEM_REG           ",             D2_SPI6_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_SLAVESEL_REG      ",             D2_SPI6_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_EOP_VALUE_REG     ",             D2_SPI6_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI6_MUXSEL_REG        ",             D2_SPI6_MUXSEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_RXDATA_REG        ",             D2_SPI7_RXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_TXDATA_REG        ",             D2_SPI7_TXDATA_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_STATUS_REG        ",             D2_SPI7_STATUS_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_CONTROL_REG       ",             D2_SPI7_CONTROL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_SEM_REG           ",             D2_SPI7_SEM_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_SLAVESEL_REG      ",             D2_SPI7_SLAVESEL_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_EOP_VALUE_REG     ",             D2_SPI7_EOP_VALUE_REG},
    TAOR_FPGA_REGISTERS{"D2_SPI7_MUXSEL_REG        ",             D2_SPI7_MUXSEL_REG},
}



var TAOR_DEV3_REGISTERS = []TAOR_FPGA_REGISTERS {
    TAOR_FPGA_REGISTERS{"D3_FPGA_REV_ID_REG       ",             D3_FPGA_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D3_FPGA_DATECODE_REG     ",             D3_FPGA_DATECODE_REG},
    TAOR_FPGA_REGISTERS{"D3_BOARD_REV_ID_REG      ",             D3_BOARD_REV_ID_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_0_REG        ",             D3_FUNC_CAP_0_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_1_REG        ",             D3_FUNC_CAP_1_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_2_REG        ",             D3_FUNC_CAP_2_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_3_REG        ",             D3_FUNC_CAP_3_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_4_REG        ",             D3_FUNC_CAP_4_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_5_REG        ",             D3_FUNC_CAP_5_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_6_REG        ",             D3_FUNC_CAP_6_REG},
    TAOR_FPGA_REGISTERS{"D3_FUNC_CAP_7_REG        ",             D3_FUNC_CAP_7_REG},
    TAOR_FPGA_REGISTERS{"D3_SCRTCH_0_REG          ",             D3_SCRTCH_0_REG},
    TAOR_FPGA_REGISTERS{"D3_SCRTCH_1_REG          ",             D3_SCRTCH_1_REG},
    TAOR_FPGA_REGISTERS{"D3_SCRTCH_2_REG          ",             D3_SCRTCH_2_REG},
    TAOR_FPGA_REGISTERS{"D3_SCRTCH_3_REG          ",             D3_SCRTCH_3_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_0_PEND_REG    ",             D3_DEV_MSI_0_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_0_INT_EN_REG  ",             D3_DEV_MSI_0_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_1_PEND_REG    ",             D3_DEV_MSI_1_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_1_INT_EN_REG  ",             D3_DEV_MSI_1_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_2_PEND_REG    ",             D3_DEV_MSI_2_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_2_INT_EN_REG  ",             D3_DEV_MSI_2_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_3_PEND_REG    ",             D3_DEV_MSI_3_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_3_INT_EN_REG  ",             D3_DEV_MSI_3_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_4_PEND_REG    ",             D3_DEV_MSI_4_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_4_INT_EN_REG  ",             D3_DEV_MSI_4_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_5_PEND_REG    ",             D3_DEV_MSI_5_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_5_INT_EN_REG  ",             D3_DEV_MSI_5_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_6_PEND_REG    ",             D3_DEV_MSI_6_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_6_INT_EN_REG  ",             D3_DEV_MSI_6_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_7_PEND_REG    ",             D3_DEV_MSI_7_PEND_REG},
    TAOR_FPGA_REGISTERS{"D3_DEV_MSI_7_INT_EN_REG  ",             D3_DEV_MSI_7_INT_EN_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_PRSCL_LO_REG      ",             D3_I2C_CH0_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_PRSCL_HI_REG      ",             D3_I2C_CH0_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_CTRL_REG          ",             D3_I2C_CH0_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_DATA_REG          ",             D3_I2C_CH0_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_CMD_REG           ",             D3_I2C_CH0_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_MUX_SEL_REG       ",             D3_I2C_CH0_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_RST_REG           ",             D3_I2C_CH0_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH0_SEM_REG           ",             D3_I2C_CH0_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_PRSCL_LO_REG      ",             D3_I2C_CH1_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_PRSCL_HI_REG      ",             D3_I2C_CH1_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_CTRL_REG          ",             D3_I2C_CH1_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_DATA_REG          ",             D3_I2C_CH1_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_CMD_REG           ",             D3_I2C_CH1_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_MUX_SEL_REG       ",             D3_I2C_CH1_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_RST_REG           ",             D3_I2C_CH1_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH1_SEM_REG           ",             D3_I2C_CH1_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_PRSCL_LO_REG      ",             D3_I2C_CH2_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_PRSCL_HI_REG      ",             D3_I2C_CH2_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_CTRL_REG          ",             D3_I2C_CH2_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_DATA_REG          ",             D3_I2C_CH2_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_CMD_REG           ",             D3_I2C_CH2_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_MUX_SEL_REG       ",             D3_I2C_CH2_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_RST_REG           ",             D3_I2C_CH2_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH2_SEM_REG           ",             D3_I2C_CH2_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_PRSCL_LO_REG      ",             D3_I2C_CH3_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_PRSCL_HI_REG      ",             D3_I2C_CH3_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_CTRL_REG          ",             D3_I2C_CH3_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_DATA_REG          ",             D3_I2C_CH3_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_CMD_REG           ",             D3_I2C_CH3_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_MUX_SEL_REG       ",             D3_I2C_CH3_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_RST_REG           ",             D3_I2C_CH3_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH3_SEM_REG           ",             D3_I2C_CH3_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_PRSCL_LO_REG      ",             D3_I2C_CH4_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_PRSCL_HI_REG      ",             D3_I2C_CH4_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_CTRL_REG          ",             D3_I2C_CH4_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_DATA_REG          ",             D3_I2C_CH4_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_CMD_REG           ",             D3_I2C_CH4_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_MUX_SEL_REG       ",             D3_I2C_CH4_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_RST_REG           ",             D3_I2C_CH4_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH4_SEM_REG           ",             D3_I2C_CH4_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_PRSCL_LO_REG      ",             D3_I2C_CH5_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_PRSCL_HI_REG      ",             D3_I2C_CH5_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_CTRL_REG          ",             D3_I2C_CH5_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_DATA_REG          ",             D3_I2C_CH5_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_CMD_REG           ",             D3_I2C_CH5_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_MUX_SEL_REG       ",             D3_I2C_CH5_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_RST_REG           ",             D3_I2C_CH5_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH5_SEM_REG           ",             D3_I2C_CH5_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_PRSCL_LO_REG      ",             D3_I2C_CH6_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_PRSCL_HI_REG      ",             D3_I2C_CH6_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_CTRL_REG          ",             D3_I2C_CH6_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_DATA_REG          ",             D3_I2C_CH6_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_CMD_REG           ",             D3_I2C_CH6_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_MUX_SEL_REG       ",             D3_I2C_CH6_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_RST_REG           ",             D3_I2C_CH6_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH6_SEM_REG           ",             D3_I2C_CH6_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_PRSCL_LO_REG      ",             D3_I2C_CH7_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_PRSCL_HI_REG      ",             D3_I2C_CH7_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_CTRL_REG          ",             D3_I2C_CH7_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_DATA_REG          ",             D3_I2C_CH7_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_CMD_REG           ",             D3_I2C_CH7_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_MUX_SEL_REG       ",             D3_I2C_CH7_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_RST_REG           ",             D3_I2C_CH7_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH7_SEM_REG           ",             D3_I2C_CH7_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_PRSCL_LO_REG      ",             D3_I2C_CH8_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_PRSCL_HI_REG      ",             D3_I2C_CH8_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_CTRL_REG          ",             D3_I2C_CH8_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_DATA_REG          ",             D3_I2C_CH8_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_CMD_REG           ",             D3_I2C_CH8_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_MUX_SEL_REG       ",             D3_I2C_CH8_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_RST_REG           ",             D3_I2C_CH8_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH8_SEM_REG           ",             D3_I2C_CH8_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_PRSCL_LO_REG      ",             D3_I2C_CH9_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_PRSCL_HI_REG      ",             D3_I2C_CH9_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_CTRL_REG          ",             D3_I2C_CH9_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_DATA_REG          ",             D3_I2C_CH9_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_CMD_REG           ",             D3_I2C_CH9_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_MUX_SEL_REG       ",             D3_I2C_CH9_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_RST_REG           ",             D3_I2C_CH9_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH9_SEM_REG           ",             D3_I2C_CH9_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_PRSCL_LO_REG      ",             D3_I2C_CH10_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_PRSCL_HI_REG      ",             D3_I2C_CH10_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_CTRL_REG          ",             D3_I2C_CH10_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_DATA_REG          ",             D3_I2C_CH10_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_CMD_REG           ",             D3_I2C_CH10_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_MUX_SEL_REG       ",             D3_I2C_CH10_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_RST_REG           ",             D3_I2C_CH10_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH10_SEM_REG           ",             D3_I2C_CH10_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_PRSCL_LO_REG      ",             D3_I2C_CH11_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_PRSCL_HI_REG      ",             D3_I2C_CH11_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_CTRL_REG          ",             D3_I2C_CH11_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_DATA_REG          ",             D3_I2C_CH11_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_CMD_REG           ",             D3_I2C_CH11_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_MUX_SEL_REG       ",             D3_I2C_CH11_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_RST_REG           ",             D3_I2C_CH11_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH11_SEM_REG           ",             D3_I2C_CH11_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_PRSCL_LO_REG      ",             D3_I2C_CH12_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_PRSCL_HI_REG      ",             D3_I2C_CH12_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_CTRL_REG          ",             D3_I2C_CH12_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_DATA_REG          ",             D3_I2C_CH12_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_CMD_REG           ",             D3_I2C_CH12_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_MUX_SEL_REG       ",             D3_I2C_CH12_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_RST_REG           ",             D3_I2C_CH12_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH12_SEM_REG           ",             D3_I2C_CH12_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_PRSCL_LO_REG      ",             D3_I2C_CH13_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_PRSCL_HI_REG      ",             D3_I2C_CH13_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_CTRL_REG          ",             D3_I2C_CH13_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_DATA_REG          ",             D3_I2C_CH13_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_CMD_REG           ",             D3_I2C_CH13_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_MUX_SEL_REG       ",             D3_I2C_CH13_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_RST_REG           ",             D3_I2C_CH13_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH13_SEM_REG           ",             D3_I2C_CH13_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_PRSCL_LO_REG      ",             D3_I2C_CH14_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_PRSCL_HI_REG      ",             D3_I2C_CH14_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_CTRL_REG          ",             D3_I2C_CH14_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_DATA_REG          ",             D3_I2C_CH14_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_CMD_REG           ",             D3_I2C_CH14_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_MUX_SEL_REG       ",             D3_I2C_CH14_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_RST_REG           ",             D3_I2C_CH14_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH14_SEM_REG           ",             D3_I2C_CH14_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_PRSCL_LO_REG      ",             D3_I2C_CH15_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_PRSCL_HI_REG      ",             D3_I2C_CH15_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_CTRL_REG          ",             D3_I2C_CH15_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_DATA_REG          ",             D3_I2C_CH15_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_CMD_REG           ",             D3_I2C_CH15_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_MUX_SEL_REG       ",             D3_I2C_CH15_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_RST_REG           ",             D3_I2C_CH15_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH15_SEM_REG           ",             D3_I2C_CH15_SEM_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_PRSCL_LO_REG      ",             D3_I2C_CH16_PRSCL_LO_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_PRSCL_HI_REG      ",             D3_I2C_CH16_PRSCL_HI_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_CTRL_REG          ",             D3_I2C_CH16_CTRL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_DATA_REG          ",             D3_I2C_CH16_DATA_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_CMD_REG           ",             D3_I2C_CH16_CMD_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_MUX_SEL_REG       ",             D3_I2C_CH16_MUX_SEL_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_RST_REG           ",             D3_I2C_CH16_RST_REG},
    TAOR_FPGA_REGISTERS{"D3_I2C_CH16_SEM_REG           ",             D3_I2C_CH16_SEM_REG},
}