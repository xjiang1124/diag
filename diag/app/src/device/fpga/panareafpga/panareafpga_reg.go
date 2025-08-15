package panareafpga


type FPGA_REGISTERS struct {
    Name     string
    Address  uint64
}



/*
 * Registers offset
 */



const FPGA_REV_ID_REG              uint64 = 0x0
const FPGA_DATECODE_REG            uint64 = 0x4
const FPGA_TIMECODE_REG            uint64 = 0x8
const FPGA_BOARD_REV_ID_REG        uint64 = 0xC
const FPGA_SCRATCH_0_REG           uint64 = 0x10
const FPGA_SCRATCH_1_REG           uint64 = 0x14
const FPGA_SCRATCH_2_REG           uint64 = 0x18
const FPGA_SCRATCH_3_REG           uint64 = 0x1C
const FPGA_DEBUG_0_REG             uint64 = 0x20
const FPGA_DEBUG_1_REG             uint64 = 0x24
const FPGA_DEBUG_2_REG             uint64 = 0x28
const FPGA_DEBUG_3_REG             uint64 = 0x2C
const FPGA_INT0_EN_REG             uint64 = 0x100
const FPGA_INT1_EN_REG             uint64 = 0x104
const FPGA_INT2_EN_REG             uint64 = 0x108
const FPGA_INT3_EN_REG             uint64 = 0x10C
const FPGA_INT0_PEND_REG           uint64 = 0x110
const FPGA_INT1_PEND_REG           uint64 = 0x114
const FPGA_INT2_PEND_REG           uint64 = 0x118
const FPGA_INT3_PEND_REG           uint64 = 0x11C
const FPGA_RESET_CAUSE_0_REG       uint64 = 0x120
const FPGA_RESET_CAUSE_1_REG       uint64 = 0x124
const FPGA_RESET_CAUSE_2_REG       uint64 = 0x128
const FPGA_RESET_CAUSE_3_REG       uint64 = 0x12C
const FPGA_SOFT_RESET_REG          uint64 = 0x130
const FPGA_FLSH_CTRL_REG           uint64 = 0x134
const FPGA_LED_CONFIG_REG          uint64 = 0x138
const FPGA_LED_SYSTEM_REG          uint64 = 0x13C
const FPGA_LED_FAN0_REG            uint64 = 0x140
const FPGA_LED_FAN1_REG            uint64 = 0x144
const FPGA_PSU_CTRL_REG            uint64 = 0x148
const FPGA_PSU_STAT_REG            uint64 = 0x14C
    const FPGA_PSU_STAT_PWROK1                 uint32 = (1<<10)
    const FPGA_PSU_STAT_ALERT1                 uint32 = (1<<9)
    const FPGA_PSU_STAT_PRSNT1                 uint32 = (1<<8)
    const FPGA_PSU_STAT_PWROK0                 uint32 = (1<<2)
    const FPGA_PSU_STAT_ALERT0                 uint32 = (1<<1)
    const FPGA_PSU_STAT_PRSNT0                 uint32 = (1<<0)
const FPGA_FAN_PWR_CTRL_REG        uint64 = 0x150
    const FPGA_FAN_PWR_CTRL_FAN0_EN            uint32 = (1<<0)
    const FPGA_FAN_PWR_CTRL_FAN1_EN            uint32 = (1<<1)
    const FPGA_FAN_PWR_CTRL_FAN2_EN            uint32 = (1<<2)
    const FPGA_FAN_PWR_CTRL_FAN3_EN            uint32 = (1<<3)
    const FPGA_FAN_PWR_CTRL_FAN4_EN            uint32 = (1<<4)
const FPGA_FAN_PWM_CTRL0_REG       uint64 = 0x154
    const FPGA_FAN_PWM_CTRL_FAN0_SHIFT         uint32 = 0
    const FPGA_FAN_PWM_CTRL_FAN0_MASK          uint32 = (0xFF<<FPGA_FAN_PWM_CTRL_FAN0_SHIFT)
    const FPGA_FAN_PWM_CTRL_FAN1_SHIFT         uint32 = 8
    const FPGA_FAN_PWM_CTRL_FAN1_MASK          uint32 = (0xFF<<FPGA_FAN_PWM_CTRL_FAN1_SHIFT)
    const FPGA_FAN_PWM_CTRL_FAN2_SHIFT         uint32 = 16
    const FPGA_FAN_PWM_CTRL_FAN2_MASK          uint32 = (0xFF<<FPGA_FAN_PWM_CTRL_FAN2_SHIFT)
    const FPGA_FAN_PWM_CTRL_FAN3_SHIFT         uint32 = 24
    const FPGA_FAN_PWM_CTRL_FAN3_MASK          uint32 = (0xFF<<FPGA_FAN_PWM_CTRL_FAN3_SHIFT)
const FPGA_FAN_PWM_CTRL1_REG       uint64 = 0x158
    const FPGA_FAN_PWM_CTRL1_FAN4_SHIFT        uint32 = 0
    const FPGA_FAN_PWM_CTRL1_FAN4_MASK         uint32 = (0xFF<<FPGA_FAN_PWM_CTRL_FAN0_SHIFT)
const FPGA_FAN_STAT_REG            uint64 = 0x15C
    const FPGA_FAN_STAT_REG_PRESENT0_BIT       uint32 = 0x01
    const FPGA_FAN_STAT_REG_PRESENT0_SHIFT     uint32 = 0x00
    const FPGA_FAN_STAT_REG_PRESENT0           uint32 = (FPGA_FAN_STAT_REG_PRESENT0_BIT<<FPGA_FAN_STAT_REG_PRESENT0_SHIFT)
    const FPGA_FAN_STAT_REG_NO_FAULT_FAN0      uint32 = (1<<16)
    const FPGA_FAN_STAT_REG_NO_FAULT_FAN1      uint32 = (1<<17)
    const FPGA_FAN_STAT_REG_NO_FAULT_FAN2      uint32 = (1<<18)
    const FPGA_FAN_STAT_REG_NO_FAULT_FAN3      uint32 = (1<<19)
    const FPGA_FAN_STAT_REG_NO_FAULT_FAN4      uint32 = (1<<20)
const FPGA_FAN0_TACH_REG           uint64 = 0x160
    const FPGA_FAN0_TACH_OUTLET_RPM_MASK       uint32 = 0xFFFF
    const FPGA_FAN0_TACH_OUTLET_RPM_SHIFT      uint32 = 0
    const FPGA_FAN0_TACH_INLET_RPM_MASK        uint32 = 0xFFFF0000
    const FPGA_FAN0_TACH_INLET_RPM_SHIFT       uint32 = 16
const FPGA_FAN1_TACH_REG           uint64 = 0x164
const FPGA_FAN2_TACH_REG           uint64 = 0x168
const FPGA_FAN3_TACH_REG           uint64 = 0x16C
const FPGA_FAN4_TACH_REG           uint64 = 0x170
const FPGA_S0_CONTROL_REG          uint64 = 0x180
const FPGA_S1_CONTROL_REG          uint64 = 0x184
const FPGA_S2_CONTROL_REG          uint64 = 0x188
const FPGA_S3_CONTROL_REG          uint64 = 0x18C
const FPGA_S4_CONTROL_REG          uint64 = 0x190
const FPGA_S5_CONTROL_REG          uint64 = 0x194
const FPGA_S6_CONTROL_REG          uint64 = 0x198
const FPGA_S7_CONTROL_REG          uint64 = 0x19C
const FPGA_S8_CONTROL_REG          uint64 = 0x1A0
const FPGA_S9_CONTROL_REG          uint64 = 0x1A4
const FPGA_MISC_CTRL_REG           uint64 = 0x300
const FPGA_MISC_STAT_REG           uint64 = 0x304
const FPGA_CPU_CTRL_REG            uint64 = 0x308
const FPGA_CPU_STAT_REG            uint64 = 0x30C
const FPGA_WDOG_CTRL_REG           uint64 = 0x310
const FPGA_WDOG_RESET_REG          uint64 = 0x314
const FPGA_E0_SMI_CMD_REG          uint64 = 0x318
const FPGA_E0_SMI_DATA_REG         uint64 = 0x31C
const FPGA_E1_SMI_CMD_REG          uint64 = 0x320
const FPGA_E1_SMI_DATA_REG         uint64 = 0x324
const FPGA_S0_I2C_PRSCL_LO_REG     uint64 = 0x400
const FPGA_S0_I2C_PRSCL_HI_REG     uint64 = 0x404
const FPGA_S0_I2C_CTRL_REG         uint64 = 0x408
const FPGA_S0_I2C_TX_REG           uint64 = 0x40C
const FPGA_S0_I2C_RX_REG           uint64 = 0x40C
const FPGA_S0_I2C_CMD_REG          uint64 = 0x410
const FPGA_S0_I2C_STAT_REG         uint64 = 0x410
const FPGA_S0_I2C_MUX_SEL_REG      uint64 = 0x414
const FPGA_S0_I2C_RST_REG          uint64 = 0x418
const FPGA_S0_I2C_SEM_REG          uint64 = 0x41C
const FPGA_S1_I2C_PRSCL_LO_REG     uint64 = 0x420
const FPGA_S1_I2C_PRSCL_HI_REG     uint64 = 0x424
const FPGA_S1_I2C_CTRL_REG         uint64 = 0x428
const FPGA_S1_I2C_TX_REG           uint64 = 0x42C
const FPGA_S1_I2C_RX_REG           uint64 = 0x42C
const FPGA_S1_I2C_CMD_REG          uint64 = 0x430
const FPGA_S1_I2C_STAT_REG         uint64 = 0x430
const FPGA_S1_I2C_MUX_SEL_REG      uint64 = 0x434
const FPGA_S1_I2C_RST_REG          uint64 = 0x438
const FPGA_S1_I2C_SEM_REG          uint64 = 0x43C
const FPGA_S2_I2C_PRSCL_LO_REG     uint64 = 0x440
const FPGA_S2_I2C_PRSCL_HI_REG     uint64 = 0x444
const FPGA_S2_I2C_CTRL_REG         uint64 = 0x448
const FPGA_S2_I2C_TX_REG           uint64 = 0x44C
const FPGA_S2_I2C_RX_REG           uint64 = 0x44C
const FPGA_S2_I2C_CMD_REG          uint64 = 0x450
const FPGA_S2_I2C_STAT_REG         uint64 = 0x450
const FPGA_S2_I2C_MUX_SEL_REG      uint64 = 0x454
const FPGA_S2_I2C_RST_REG          uint64 = 0x458
const FPGA_S2_I2C_SEM_REG          uint64 = 0x45C
const FPGA_S3_I2C_PRSCL_LO_REG     uint64 = 0x460
const FPGA_S3_I2C_PRSCL_HI_REG     uint64 = 0x464
const FPGA_S3_I2C_CTRL_REG         uint64 = 0x468
const FPGA_S3_I2C_TX_REG           uint64 = 0x46C
const FPGA_S3_I2C_RX_REG           uint64 = 0x46C
const FPGA_S3_I2C_CMD_REG          uint64 = 0x470
const FPGA_S3_I2C_STAT_REG         uint64 = 0x470
const FPGA_S3_I2C_MUX_SEL_REG      uint64 = 0x474
const FPGA_S3_I2C_RST_REG          uint64 = 0x478
const FPGA_S3_I2C_SEM_REG          uint64 = 0x47C
const FPGA_S4_I2C_PRSCL_LO_REG     uint64 = 0x480
const FPGA_S4_I2C_PRSCL_HI_REG     uint64 = 0x484
const FPGA_S4_I2C_CTRL_REG         uint64 = 0x488
const FPGA_S4_I2C_TX_REG           uint64 = 0x48C
const FPGA_S4_I2C_RX_REG           uint64 = 0x48C
const FPGA_S4_I2C_CMD_REG          uint64 = 0x490
const FPGA_S4_I2C_STAT_REG         uint64 = 0x490
const FPGA_S4_I2C_MUX_SEL_REG      uint64 = 0x494
const FPGA_S4_I2C_RST_REG          uint64 = 0x498
const FPGA_S4_I2C_SEM_REG          uint64 = 0x49C
const FPGA_S5_I2C_PRSCL_LO_REG     uint64 = 0x4A0
const FPGA_S5_I2C_PRSCL_HI_REG     uint64 = 0x4A4
const FPGA_S5_I2C_CTRL_REG         uint64 = 0x4A8
const FPGA_S5_I2C_TX_REG           uint64 = 0x4AC
const FPGA_S5_I2C_RX_REG           uint64 = 0x4AC
const FPGA_S5_I2C_CMD_REG          uint64 = 0x4B0
const FPGA_S5_I2C_STAT_REG         uint64 = 0x4B0
const FPGA_S5_I2C_MUX_SEL_REG      uint64 = 0x4B4
const FPGA_S5_I2C_RST_REG          uint64 = 0x4B8
const FPGA_S5_I2C_SEM_REG          uint64 = 0x4BC
const FPGA_S6_I2C_PRSCL_LO_REG     uint64 = 0x4C0
const FPGA_S6_I2C_PRSCL_HI_REG     uint64 = 0x4C4
const FPGA_S6_I2C_CTRL_REG         uint64 = 0x4C8
const FPGA_S6_I2C_TX_REG           uint64 = 0x4CC
const FPGA_S6_I2C_RX_REG           uint64 = 0x4CC
const FPGA_S6_I2C_CMD_REG          uint64 = 0x4D0
const FPGA_S6_I2C_STAT_REG         uint64 = 0x4D0
const FPGA_S6_I2C_MUX_SEL_REG      uint64 = 0x4D4
const FPGA_S6_I2C_RST_REG          uint64 = 0x4D8
const FPGA_S6_I2C_SEM_REG          uint64 = 0x4DC
const FPGA_S7_I2C_PRSCL_LO_REG     uint64 = 0x4E0
const FPGA_S7_I2C_PRSCL_HI_REG     uint64 = 0x4E4
const FPGA_S7_I2C_CTRL_REG         uint64 = 0x4E8
const FPGA_S7_I2C_TX_REG           uint64 = 0x4EC
const FPGA_S7_I2C_RX_REG           uint64 = 0x4EC
const FPGA_S7_I2C_CMD_REG          uint64 = 0x4F0
const FPGA_S7_I2C_STAT_REG         uint64 = 0x4F0
const FPGA_S7_I2C_MUX_SEL_REG      uint64 = 0x4F4
const FPGA_S7_I2C_RST_REG          uint64 = 0x4F8
const FPGA_S7_I2C_SEM_REG          uint64 = 0x4FC
const FPGA_S8_I2C_PRSCL_LO_REG     uint64 = 0x500
const FPGA_S8_I2C_PRSCL_HI_REG     uint64 = 0x504
const FPGA_S8_I2C_CTRL_REG         uint64 = 0x508
const FPGA_S8_I2C_TX_REG           uint64 = 0x50C
const FPGA_S8_I2C_RX_REG           uint64 = 0x50C
const FPGA_S8_I2C_CMD_REG          uint64 = 0x510
const FPGA_S8_I2C_STAT_REG         uint64 = 0x510
const FPGA_S8_I2C_MUX_SEL_REG      uint64 = 0x514
const FPGA_S8_I2C_RST_REG          uint64 = 0x518
const FPGA_S8_I2C_SEM_REG          uint64 = 0x51C
const FPGA_S9_I2C_PRSCL_LO_REG     uint64 = 0x520
const FPGA_S9_I2C_PRSCL_HI_REG     uint64 = 0x524
const FPGA_S9_I2C_CTRL_REG         uint64 = 0x528
const FPGA_S9_I2C_TX_REG           uint64 = 0x52C
const FPGA_S9_I2C_RX_REG           uint64 = 0x52C
const FPGA_S9_I2C_CMD_REG          uint64 = 0x530
const FPGA_S9_I2C_STAT_REG         uint64 = 0x530
const FPGA_S9_I2C_MUX_SEL_REG      uint64 = 0x534
const FPGA_S9_I2C_RST_REG          uint64 = 0x538
const FPGA_S9_I2C_SEM_REG          uint64 = 0x53C
const FPGA_DBG_I2C_PRSCL_LO_REG    uint64 = 0x540
const FPGA_DBG_I2C_PRSCL_HI_REG    uint64 = 0x544
const FPGA_DBG_I2C_CTRL_REG        uint64 = 0x548
const FPGA_DBG_I2C_TX_REG          uint64 = 0x54C
const FPGA_DBG_I2C_RX_REG          uint64 = 0x54C
const FPGA_DBG_I2C_CMD_REG         uint64 = 0x550
const FPGA_DBG_I2C_STAT_REG        uint64 = 0x550
const FPGA_DBG_I2C_MUX_SEL_REG     uint64 = 0x554
const FPGA_DBG_I2C_RST_REG         uint64 = 0x558
const FPGA_DBG_I2C_SEM_REG         uint64 = 0x55C
const FPGA_PSU0_I2C_PRSCL_LO_REG   uint64 = 0x560
const FPGA_PSU0_I2C_PRSCL_HI_REG   uint64 = 0x564
const FPGA_PSU0_I2C_CTRL_REG       uint64 = 0x568
const FPGA_PSU0_I2C_TX_REG         uint64 = 0x56C
const FPGA_PSU0_I2C_RX_REG         uint64 = 0x56C
const FPGA_PSU0_I2C_CMD_REG        uint64 = 0x570
const FPGA_PSU0_I2C_STAT_REG       uint64 = 0x570
const FPGA_PSU0_I2C_MUX_SEL_REG    uint64 = 0x574
const FPGA_PSU0_I2C_RST_REG        uint64 = 0x578
const FPGA_PSU0_I2C_SEM_REG        uint64 = 0x57C
const FPGA_PSU1_I2C_PRSCL_LO_REG   uint64 = 0x580
const FPGA_PSU1_I2C_PRSCL_HI_REG   uint64 = 0x584
const FPGA_PSU1_I2C_CTRL_REG       uint64 = 0x588
const FPGA_PSU1_I2C_TX_REG         uint64 = 0x58C
const FPGA_PSU1_I2C_RX_REG         uint64 = 0x58C
const FPGA_PSU1_I2C_CMD_REG        uint64 = 0x590
const FPGA_PSU1_I2C_STAT_REG       uint64 = 0x590
const FPGA_PSU1_I2C_MUX_SEL_REG    uint64 = 0x594
const FPGA_PSU1_I2C_RST_REG        uint64 = 0x598
const FPGA_PSU1_I2C_SEM_REG        uint64 = 0x59C
const FPGA_PMB_I2C_PRSCL_LO_REG    uint64 = 0x5A0
const FPGA_PMB_I2C_PRSCL_HI_REG    uint64 = 0x5A4
const FPGA_PMB_I2C_CTRL_REG        uint64 = 0x5A8
const FPGA_PMB_I2C_TX_REG          uint64 = 0x5AC
const FPGA_PMB_I2C_RX_REG          uint64 = 0x5AC
const FPGA_PMB_I2C_CMD_REG         uint64 = 0x5B0
const FPGA_PMB_I2C_STAT_REG        uint64 = 0x5B0
const FPGA_PMB_I2C_MUX_SEL_REG     uint64 = 0x5B4
const FPGA_PMB_I2C_RST_REG         uint64 = 0x5B8
const FPGA_PMB_I2C_SEM_REG         uint64 = 0x5BC
const FPGA_IOBR_I2C_PRSCL_LO_REG   uint64 = 0x5C0
const FPGA_IOBR_I2C_PRSCL_HI_REG   uint64 = 0x5C4
const FPGA_IOBR_I2C_CTRL_REG       uint64 = 0x5C8
const FPGA_IOBR_I2C_TX_REG         uint64 = 0x5CC
const FPGA_IOBR_I2C_RX_REG         uint64 = 0x5CC
const FPGA_IOBR_I2C_CMD_REG        uint64 = 0x5D0
const FPGA_IOBR_I2C_STAT_REG       uint64 = 0x5D0
const FPGA_IOBR_I2C_MUX_SEL_REG    uint64 = 0x5D4
const FPGA_IOBR_I2C_RST_REG        uint64 = 0x5D8
const FPGA_IOBR_I2C_SEM_REG        uint64 = 0x5DC
const FPGA_IOBL_I2C_PRSCL_LO_REG   uint64 = 0x5E0
const FPGA_IOBL_I2C_PRSCL_HI_REG   uint64 = 0x5E4
const FPGA_IOBL_I2C_CTRL_REG       uint64 = 0x5E8
const FPGA_IOBL_I2C_TX_REG         uint64 = 0x5EC
const FPGA_IOBL_I2C_RX_REG         uint64 = 0x5EC
const FPGA_IOBL_I2C_CMD_REG        uint64 = 0x5F0
const FPGA_IOBL_I2C_STAT_REG       uint64 = 0x5F0
const FPGA_IOBL_I2C_MUX_SEL_REG    uint64 = 0x5F4
const FPGA_IOBL_I2C_RST_REG        uint64 = 0x5F8
const FPGA_IOBL_I2C_SEM_REG        uint64 = 0x5FC
const FPGA_FPIC_I2C_PRSCL_LO_REG   uint64 = 0x600
const FPGA_FPIC_I2C_PRSCL_HI_REG   uint64 = 0x604
const FPGA_FPIC_I2C_CTRL_REG       uint64 = 0x608
const FPGA_FPIC_I2C_TX_REG         uint64 = 0x60C
const FPGA_FPIC_I2C_RX_REG         uint64 = 0x60C
const FPGA_FPIC_I2C_CMD_REG        uint64 = 0x610
const FPGA_FPIC_I2C_STAT_REG       uint64 = 0x610
const FPGA_FPIC_I2C_MUX_SEL_REG    uint64 = 0x614
const FPGA_FPIC_I2C_RST_REG        uint64 = 0x618
const FPGA_FPIC_I2C_SEM_REG        uint64 = 0x61C
const FPGA_ID_I2C_PRSCL_LO_REG     uint64 = 0x620
const FPGA_ID_I2C_PRSCL_HI_REG     uint64 = 0x624
const FPGA_ID_I2C_CTRL_REG         uint64 = 0x628
const FPGA_ID_I2C_TX_REG           uint64 = 0x62C
const FPGA_ID_I2C_RX_REG           uint64 = 0x62C
const FPGA_ID_I2C_CMD_REG          uint64 = 0x630
const FPGA_ID_I2C_STAT_REG         uint64 = 0x630
const FPGA_ID_I2C_MUX_SEL_REG      uint64 = 0x634
const FPGA_ID_I2C_RST_REG          uint64 = 0x638
const FPGA_ID_I2C_SEM_REG          uint64 = 0x63C
const FPGA_MCIO_I2C_PRSCL_LO_REG   uint64 = 0x640
const FPGA_MCIO_I2C_PRSCL_HI_REG   uint64 = 0x644
const FPGA_MCIO_I2C_CTRL_REG       uint64 = 0x648
const FPGA_MCIO_I2C_TX_REG         uint64 = 0x64C
const FPGA_MCIO_I2C_RX_REG         uint64 = 0x64C
const FPGA_MCIO_I2C_CMD_REG        uint64 = 0x650
const FPGA_MCIO_I2C_STAT_REG       uint64 = 0x650
const FPGA_MCIO_I2C_MUX_SEL_REG    uint64 = 0x654
const FPGA_MCIO_I2C_RST_REG        uint64 = 0x658
const FPGA_MCIO_I2C_SEM_REG        uint64 = 0x65C
const FPGA_S0_J2C_CMD_REG          uint64 = 0xA00
const FPGA_S0_J2C_STAT_REG         uint64 = 0xA04
const FPGA_S0_J2C_ADDR0_REG        uint64 = 0xA08
const FPGA_S0_J2C_ADDR1_REG        uint64 = 0xA0C
const FPGA_S0_J2C_TXDATA_REG       uint64 = 0xA10
const FPGA_S0_J2C_RXDATA_REG       uint64 = 0xA14
const FPGA_S0_J2C_SEM_REG          uint64 = 0xA18
const FPGA_S0_J2C_MAGIC_REG        uint64 = 0xA1C
const FPGA_S0_J2C_TXFIFO_REG       uint64 = 0xA20
const FPGA_S0_J2C_RXFIFO_REG       uint64 = 0xA24
const FPGA_S0_J2C_SIZE_REG         uint64 = 0xA28
const FPGA_S0_OW_INIT_REG          uint64 = 0xA40
const FPGA_S0_OW_CMD_REG           uint64 = 0xA44
const FPGA_S0_OW_STATUS_REG        uint64 = 0xA48
const FPGA_S0_OW_DATA_REG          uint64 = 0xA4C
const FPGA_S0_OW_ADDR0_REG         uint64 = 0xA50
const FPGA_S0_OW_ADDR1_REG         uint64 = 0xA54
const FPGA_S0_OW_EOM_WIDTH_REG     uint64 = 0xA58
const FPGA_S1_J2C_CMD_REG          uint64 = 0xB00
const FPGA_S1_J2C_STAT_REG         uint64 = 0xB04
const FPGA_S1_J2C_ADDR0_REG        uint64 = 0xB08
const FPGA_S1_J2C_ADDR1_REG        uint64 = 0xB0C
const FPGA_S1_J2C_TXDATA_REG       uint64 = 0xB10
const FPGA_S1_J2C_RXDATA_REG       uint64 = 0xB14
const FPGA_S1_J2C_SEM_REG          uint64 = 0xB18
const FPGA_S1_J2C_MAGIC_REG        uint64 = 0xB1C
const FPGA_S1_J2C_TXFIFO_REG       uint64 = 0xB20
const FPGA_S1_J2C_RXFIFO_REG       uint64 = 0xB24
const FPGA_S1_J2C_SIZE_REG         uint64 = 0xB28
const FPGA_S1_OW_INIT_REG          uint64 = 0xB40
const FPGA_S1_OW_CMD_REG           uint64 = 0xB44
const FPGA_S1_OW_STATUS_REG        uint64 = 0xB48
const FPGA_S1_OW_DATA_REG          uint64 = 0xB4C
const FPGA_S1_OW_ADDR0_REG         uint64 = 0xB50
const FPGA_S1_OW_ADDR1_REG         uint64 = 0xB54
const FPGA_S1_OW_EOM_WIDTH_REG     uint64 = 0xB58
const FPGA_S2_J2C_CMD_REG          uint64 = 0xC00
const FPGA_S2_J2C_STAT_REG         uint64 = 0xC04
const FPGA_S2_J2C_ADDR0_REG        uint64 = 0xC08
const FPGA_S2_J2C_ADDR1_REG        uint64 = 0xC0C
const FPGA_S2_J2C_TXDATA_REG       uint64 = 0xC10
const FPGA_S2_J2C_RXDATA_REG       uint64 = 0xC14
const FPGA_S2_J2C_SEM_REG          uint64 = 0xC18
const FPGA_S2_J2C_MAGIC_REG        uint64 = 0xC1C
const FPGA_S2_J2C_TXFIFO_REG       uint64 = 0xC20
const FPGA_S2_J2C_RXFIFO_REG       uint64 = 0xC24
const FPGA_S2_J2C_SIZE_REG         uint64 = 0xC28
const FPGA_S2_OW_INIT_REG          uint64 = 0xC40
const FPGA_S2_OW_CMD_REG           uint64 = 0xC44
const FPGA_S2_OW_STATUS_REG        uint64 = 0xC48
const FPGA_S2_OW_DATA_REG          uint64 = 0xC4C
const FPGA_S2_OW_ADDR0_REG         uint64 = 0xC50
const FPGA_S2_OW_ADDR1_REG         uint64 = 0xC54
const FPGA_S2_OW_EOM_WIDTH_REG     uint64 = 0xC58
const FPGA_S3_J2C_CMD_REG          uint64 = 0xD00
const FPGA_S3_J2C_STAT_REG         uint64 = 0xD04
const FPGA_S3_J2C_ADDR0_REG        uint64 = 0xD08
const FPGA_S3_J2C_ADDR1_REG        uint64 = 0xD0C
const FPGA_S3_J2C_TXDATA_REG       uint64 = 0xD10
const FPGA_S3_J2C_RXDATA_REG       uint64 = 0xD14
const FPGA_S3_J2C_SEM_REG          uint64 = 0xD18
const FPGA_S3_J2C_MAGIC_REG        uint64 = 0xD1C
const FPGA_S3_J2C_TXFIFO_REG       uint64 = 0xD20
const FPGA_S3_J2C_RXFIFO_REG       uint64 = 0xD24
const FPGA_S3_J2C_SIZE_REG         uint64 = 0xD28
const FPGA_S3_OW_INIT_REG          uint64 = 0xD40
const FPGA_S3_OW_CMD_REG           uint64 = 0xD44
const FPGA_S3_OW_STATUS_REG        uint64 = 0xD48
const FPGA_S3_OW_DATA_REG          uint64 = 0xD4C
const FPGA_S3_OW_ADDR0_REG         uint64 = 0xD50
const FPGA_S3_OW_ADDR1_REG         uint64 = 0xD54
const FPGA_S3_OW_EOM_WIDTH_REG     uint64 = 0xD58
const FPGA_S4_J2C_CMD_REG          uint64 = 0xE00
const FPGA_S4_J2C_STAT_REG         uint64 = 0xE04
const FPGA_S4_J2C_ADDR0_REG        uint64 = 0xE08
const FPGA_S4_J2C_ADDR1_REG        uint64 = 0xE0C
const FPGA_S4_J2C_TXDATA_REG       uint64 = 0xE10
const FPGA_S4_J2C_RXDATA_REG       uint64 = 0xE14
const FPGA_S4_J2C_SEM_REG          uint64 = 0xE18
const FPGA_S4_J2C_MAGIC_REG        uint64 = 0xE1C
const FPGA_S4_J2C_TXFIFO_REG       uint64 = 0xE20
const FPGA_S4_J2C_RXFIFO_REG       uint64 = 0xE24
const FPGA_S4_J2C_SIZE_REG         uint64 = 0xE28
const FPGA_S4_OW_INIT_REG          uint64 = 0xE40
const FPGA_S4_OW_CMD_REG           uint64 = 0xE44
const FPGA_S4_OW_STATUS_REG        uint64 = 0xE48
const FPGA_S4_OW_DATA_REG          uint64 = 0xE4C
const FPGA_S4_OW_ADDR0_REG         uint64 = 0xE50
const FPGA_S4_OW_ADDR1_REG         uint64 = 0xE54
const FPGA_S4_OW_EOM_WIDTH_REG     uint64 = 0xE58
const FPGA_S5_J2C_CMD_REG          uint64 = 0xF00
const FPGA_S5_J2C_STAT_REG         uint64 = 0xF04
const FPGA_S5_J2C_ADDR0_REG        uint64 = 0xF08
const FPGA_S5_J2C_ADDR1_REG        uint64 = 0xF0C
const FPGA_S5_J2C_TXDATA_REG       uint64 = 0xF10
const FPGA_S5_J2C_RXDATA_REG       uint64 = 0xF14
const FPGA_S5_J2C_SEM_REG          uint64 = 0xF18
const FPGA_S5_J2C_MAGIC_REG        uint64 = 0xF1C
const FPGA_S5_J2C_TXFIFO_REG       uint64 = 0xF20
const FPGA_S5_J2C_RXFIFO_REG       uint64 = 0xF24
const FPGA_S5_J2C_SIZE_REG         uint64 = 0xF28
const FPGA_S5_OW_INIT_REG          uint64 = 0xF40
const FPGA_S5_OW_CMD_REG           uint64 = 0xF44
const FPGA_S5_OW_STATUS_REG        uint64 = 0xF48
const FPGA_S5_OW_DATA_REG          uint64 = 0xF4C
const FPGA_S5_OW_ADDR0_REG         uint64 = 0xF50
const FPGA_S5_OW_ADDR1_REG         uint64 = 0xF54
const FPGA_S5_OW_EOM_WIDTH_REG     uint64 = 0xF58
const FPGA_S6_J2C_CMD_REG          uint64 = 0x1000
const FPGA_S6_J2C_STAT_REG         uint64 = 0x1004
const FPGA_S6_J2C_ADDR0_REG        uint64 = 0x1008
const FPGA_S6_J2C_ADDR1_REG        uint64 = 0x100C
const FPGA_S6_J2C_TXDATA_REG       uint64 = 0x1010
const FPGA_S6_J2C_RXDATA_REG       uint64 = 0x1014
const FPGA_S6_J2C_SEM_REG          uint64 = 0x1018
const FPGA_S6_J2C_MAGIC_REG        uint64 = 0x101C
const FPGA_S6_J2C_TXFIFO_REG       uint64 = 0x1020
const FPGA_S6_J2C_RXFIFO_REG       uint64 = 0x1024
const FPGA_S6_J2C_SIZE_REG         uint64 = 0x1028
const FPGA_S6_OW_INIT_REG          uint64 = 0x1040
const FPGA_S6_OW_CMD_REG           uint64 = 0x1044
const FPGA_S6_OW_STATUS_REG        uint64 = 0x1048
const FPGA_S6_OW_DATA_REG          uint64 = 0x104C
const FPGA_S6_OW_ADDR0_REG         uint64 = 0x1050
const FPGA_S6_OW_ADDR1_REG         uint64 = 0x1054
const FPGA_S6_OW_EOM_WIDTH_REG     uint64 = 0x1058
const FPGA_S7_J2C_CMD_REG          uint64 = 0x1100
const FPGA_S7_J2C_STAT_REG         uint64 = 0x1104
const FPGA_S7_J2C_ADDR0_REG        uint64 = 0x1108
const FPGA_S7_J2C_ADDR1_REG        uint64 = 0x110C
const FPGA_S7_J2C_TXDATA_REG       uint64 = 0x1110
const FPGA_S7_J2C_RXDATA_REG       uint64 = 0x1114
const FPGA_S7_J2C_SEM_REG          uint64 = 0x1118
const FPGA_S7_J2C_MAGIC_REG        uint64 = 0x111C
const FPGA_S7_J2C_TXFIFO_REG       uint64 = 0x1120
const FPGA_S7_J2C_RXFIFO_REG       uint64 = 0x1124
const FPGA_S7_J2C_SIZE_REG         uint64 = 0x1128
const FPGA_S7_OW_INIT_REG          uint64 = 0x1140
const FPGA_S7_OW_CMD_REG           uint64 = 0x1144
const FPGA_S7_OW_STATUS_REG        uint64 = 0x1148
const FPGA_S7_OW_DATA_REG          uint64 = 0x114C
const FPGA_S7_OW_ADDR0_REG         uint64 = 0x1150
const FPGA_S7_OW_ADDR1_REG         uint64 = 0x1154
const FPGA_S7_OW_EOM_WIDTH_REG     uint64 = 0x1158
const FPGA_S8_J2C_CMD_REG          uint64 = 0x1200
const FPGA_S8_J2C_STAT_REG         uint64 = 0x1204
const FPGA_S8_J2C_ADDR0_REG        uint64 = 0x1208
const FPGA_S8_J2C_ADDR1_REG        uint64 = 0x120C
const FPGA_S8_J2C_TXDATA_REG       uint64 = 0x1210
const FPGA_S8_J2C_RXDATA_REG       uint64 = 0x1214
const FPGA_S8_J2C_SEM_REG          uint64 = 0x1218
const FPGA_S8_J2C_MAGIC_REG        uint64 = 0x121C
const FPGA_S8_J2C_TXFIFO_REG       uint64 = 0x1220
const FPGA_S8_J2C_RXFIFO_REG       uint64 = 0x1224
const FPGA_S8_J2C_SIZE_REG         uint64 = 0x1228
const FPGA_S8_OW_INIT_REG          uint64 = 0x1240
const FPGA_S8_OW_CMD_REG           uint64 = 0x1244
const FPGA_S8_OW_STATUS_REG        uint64 = 0x1248
const FPGA_S8_OW_DATA_REG          uint64 = 0x124C
const FPGA_S8_OW_ADDR0_REG         uint64 = 0x1250
const FPGA_S8_OW_ADDR1_REG         uint64 = 0x1254
const FPGA_S8_OW_EOM_WIDTH_REG     uint64 = 0x1258
const FPGA_S9_J2C_CMD_REG          uint64 = 0x1300
const FPGA_S9_J2C_STAT_REG         uint64 = 0x1304
const FPGA_S9_J2C_ADDR0_REG        uint64 = 0x1308
const FPGA_S9_J2C_ADDR1_REG        uint64 = 0x130C
const FPGA_S9_J2C_TXDATA_REG       uint64 = 0x1310
const FPGA_S9_J2C_RXDATA_REG       uint64 = 0x1314
const FPGA_S9_J2C_SEM_REG          uint64 = 0x1318
const FPGA_S9_J2C_MAGIC_REG        uint64 = 0x131C
const FPGA_S9_J2C_TXFIFO_REG       uint64 = 0x1320
const FPGA_S9_J2C_RXFIFO_REG       uint64 = 0x1324
const FPGA_S9_J2C_SIZE_REG         uint64 = 0x1328
const FPGA_S9_OW_INIT_REG          uint64 = 0x1340
const FPGA_S9_OW_CMD_REG           uint64 = 0x1344
const FPGA_S9_OW_STATUS_REG        uint64 = 0x1348
const FPGA_S9_OW_DATA_REG          uint64 = 0x134C
const FPGA_S9_OW_ADDR0_REG         uint64 = 0x1350
const FPGA_S9_OW_ADDR1_REG         uint64 = 0x1354
const FPGA_S9_OW_EOM_WIDTH_REG     uint64 = 0x1358
const FPGA_DBG_J2C_CMD_REG         uint64 = 0x1400
const FPGA_DBG_J2C_STAT_REG        uint64 = 0x1404
const FPGA_DBG_J2C_ADDR0_REG       uint64 = 0x1408
const FPGA_DBG_J2C_ADDR1_REG       uint64 = 0x140C
const FPGA_DBG_J2C_TXDATA_REG      uint64 = 0x1410
const FPGA_DBG_J2C_RXDATA_REG      uint64 = 0x1414
const FPGA_DBG_J2C_SEM_REG         uint64 = 0x1418
const FPGA_DBG_J2C_MAGIC_REG       uint64 = 0x141C
const FPGA_DBG_J2C_TXFIFO_REG      uint64 = 0x1420
const FPGA_DBG_J2C_RXFIFO_REG      uint64 = 0x1424
const FPGA_DBG_J2C_SIZE_REG        uint64 = 0x1428
const FPGA_DBG_OW_INIT_REG         uint64 = 0x1440
const FPGA_DBG_OW_CMD_REG          uint64 = 0x1444
const FPGA_DBG_OW_STATUS_REG       uint64 = 0x1448
const FPGA_DBG_OW_DATA_REG         uint64 = 0x144C
const FPGA_DBG_OW_ADDR0_REG        uint64 = 0x1450
const FPGA_DBG_OW_ADDR1_REG        uint64 = 0x1454
const FPGA_DBG_OW_EOM_WIDTH_REG    uint64 = 0x1458
const FPGA_S0_SPI_RXDATA_REG       uint64 = 0x2000
const FPGA_S0_SPI_TXDATA4B_REG     uint64 = 0x2004
const FPGA_S0_SPI_TXDATA2B_REG     uint64 = 0x2008
const FPGA_S0_SPI_TXDATA1B_REG     uint64 = 0x200C
const FPGA_S0_SPI_STATUS_REG       uint64 = 0x2010
const FPGA_S0_SPI_CONTROL_REG      uint64 = 0x2014
const FPGA_S0_SPI_SEM_REG          uint64 = 0x2018
const FPGA_S0_SPI_SLAVESEL_REG     uint64 = 0x201C
const FPGA_S0_SPI_EOP_VALUE_REG    uint64 = 0x2020
const FPGA_S0_SPI_MUXSEL_REG       uint64 = 0x2024
const FPGA_S1_SPI_RXDATA_REG       uint64 = 0x2040
const FPGA_S1_SPI_TXDATA4B_REG     uint64 = 0x2044
const FPGA_S1_SPI_TXDATA2B_REG     uint64 = 0x2048
const FPGA_S1_SPI_TXDATA1B_REG     uint64 = 0x204C
const FPGA_S1_SPI_STATUS_REG       uint64 = 0x2050
const FPGA_S1_SPI_CONTROL_REG      uint64 = 0x2054
const FPGA_S1_SPI_SEM_REG          uint64 = 0x2058
const FPGA_S1_SPI_SLAVESEL_REG     uint64 = 0x205C
const FPGA_S1_SPI_EOP_VALUE_REG    uint64 = 0x2060
const FPGA_S1_SPI_MUXSEL_REG       uint64 = 0x2064
const FPGA_S2_SPI_RXDATA_REG       uint64 = 0x2080
const FPGA_S2_SPI_TXDATA4B_REG     uint64 = 0x2084
const FPGA_S2_SPI_TXDATA2B_REG     uint64 = 0x2088
const FPGA_S2_SPI_TXDATA1B_REG     uint64 = 0x208C
const FPGA_S2_SPI_STATUS_REG       uint64 = 0x2090
const FPGA_S2_SPI_CONTROL_REG      uint64 = 0x2094
const FPGA_S2_SPI_SEM_REG          uint64 = 0x2098
const FPGA_S2_SPI_SLAVESEL_REG     uint64 = 0x209C
const FPGA_S2_SPI_EOP_VALUE_REG    uint64 = 0x20A0
const FPGA_S2_SPI_MUXSEL_REG       uint64 = 0x20A4
const FPGA_S3_SPI_RXDATA_REG       uint64 = 0x20C0
const FPGA_S3_SPI_TXDATA4B_REG     uint64 = 0x20C4
const FPGA_S3_SPI_TXDATA2B_REG     uint64 = 0x20C8
const FPGA_S3_SPI_TXDATA1B_REG     uint64 = 0x20CC
const FPGA_S3_SPI_STATUS_REG       uint64 = 0x20D0
const FPGA_S3_SPI_CONTROL_REG      uint64 = 0x20D4
const FPGA_S3_SPI_SEM_REG          uint64 = 0x20D8
const FPGA_S3_SPI_SLAVESEL_REG     uint64 = 0x20DC
const FPGA_S3_SPI_EOP_VALUE_REG    uint64 = 0x20E0
const FPGA_S3_SPI_MUXSEL_REG       uint64 = 0x20E4
const FPGA_S4_SPI_RXDATA_REG       uint64 = 0x2100
const FPGA_S4_SPI_TXDATA4B_REG     uint64 = 0x2104
const FPGA_S4_SPI_TXDATA2B_REG     uint64 = 0x2108
const FPGA_S4_SPI_TXDATA1B_REG     uint64 = 0x210C
const FPGA_S4_SPI_STATUS_REG       uint64 = 0x2110
const FPGA_S4_SPI_CONTROL_REG      uint64 = 0x2114
const FPGA_S4_SPI_SEM_REG          uint64 = 0x2118
const FPGA_S4_SPI_SLAVESEL_REG     uint64 = 0x211C
const FPGA_S4_SPI_EOP_VALUE_REG    uint64 = 0x2120
const FPGA_S4_SPI_MUXSEL_REG       uint64 = 0x2124
const FPGA_S5_SPI_RXDATA_REG       uint64 = 0x2140
const FPGA_S5_SPI_TXDATA4B_REG     uint64 = 0x2144
const FPGA_S5_SPI_TXDATA2B_REG     uint64 = 0x2148
const FPGA_S5_SPI_TXDATA1B_REG     uint64 = 0x214C
const FPGA_S5_SPI_STATUS_REG       uint64 = 0x2150
const FPGA_S5_SPI_CONTROL_REG      uint64 = 0x2154
const FPGA_S5_SPI_SEM_REG          uint64 = 0x2158
const FPGA_S5_SPI_SLAVESEL_REG     uint64 = 0x215C
const FPGA_S5_SPI_EOP_VALUE_REG    uint64 = 0x2160
const FPGA_S5_SPI_MUXSEL_REG       uint64 = 0x2164
const FPGA_S6_SPI_RXDATA_REG       uint64 = 0x2180
const FPGA_S6_SPI_TXDATA4B_REG     uint64 = 0x2184
const FPGA_S6_SPI_TXDATA2B_REG     uint64 = 0x2188
const FPGA_S6_SPI_TXDATA1B_REG     uint64 = 0x218C
const FPGA_S6_SPI_STATUS_REG       uint64 = 0x2190
const FPGA_S6_SPI_CONTROL_REG      uint64 = 0x2194
const FPGA_S6_SPI_SEM_REG          uint64 = 0x2198
const FPGA_S6_SPI_SLAVESEL_REG     uint64 = 0x219C
const FPGA_S6_SPI_EOP_VALUE_REG    uint64 = 0x21A0
const FPGA_S6_SPI_MUXSEL_REG       uint64 = 0x21A4
const FPGA_S7_SPI_RXDATA_REG       uint64 = 0x21C0
const FPGA_S7_SPI_TXDATA4B_REG     uint64 = 0x21C4
const FPGA_S7_SPI_TXDATA2B_REG     uint64 = 0x21C8
const FPGA_S7_SPI_TXDATA1B_REG     uint64 = 0x21CC
const FPGA_S7_SPI_STATUS_REG       uint64 = 0x21D0
const FPGA_S7_SPI_CONTROL_REG      uint64 = 0x21D4
const FPGA_S7_SPI_SEM_REG          uint64 = 0x21D8
const FPGA_S7_SPI_SLAVESEL_REG     uint64 = 0x21DC
const FPGA_S7_SPI_EOP_VALUE_REG    uint64 = 0x21E0
const FPGA_S7_SPI_MUXSEL_REG       uint64 = 0x21E4
const FPGA_S8_SPI_RXDATA_REG       uint64 = 0x2200
const FPGA_S8_SPI_TXDATA4B_REG     uint64 = 0x2204
const FPGA_S8_SPI_TXDATA2B_REG     uint64 = 0x2208
const FPGA_S8_SPI_TXDATA1B_REG     uint64 = 0x220C
const FPGA_S8_SPI_STATUS_REG       uint64 = 0x2210
const FPGA_S8_SPI_CONTROL_REG      uint64 = 0x2214
const FPGA_S8_SPI_SEM_REG          uint64 = 0x2218
const FPGA_S8_SPI_SLAVESEL_REG     uint64 = 0x221C
const FPGA_S8_SPI_EOP_VALUE_REG    uint64 = 0x2220
const FPGA_S8_SPI_MUXSEL_REG       uint64 = 0x2224
const FPGA_S9_SPI_RXDATA_REG       uint64 = 0x2240
const FPGA_S9_SPI_TXDATA4B_REG     uint64 = 0x2244
const FPGA_S9_SPI_TXDATA2B_REG     uint64 = 0x2248
const FPGA_S9_SPI_TXDATA1B_REG     uint64 = 0x224C
const FPGA_S9_SPI_STATUS_REG       uint64 = 0x2250
const FPGA_S9_SPI_CONTROL_REG      uint64 = 0x2254
const FPGA_S9_SPI_SEM_REG          uint64 = 0x2258
const FPGA_S9_SPI_SLAVESEL_REG     uint64 = 0x225C
const FPGA_S9_SPI_EOP_VALUE_REG    uint64 = 0x2260
const FPGA_S9_SPI_MUXSEL_REG       uint64 = 0x2264
const FPGA_DBG_SPI_RXDATA_REG      uint64 = 0x2280
const FPGA_DBG_SPI_TXDATA4B_REG    uint64 = 0x2284
const FPGA_DBG_SPI_TXDATA2B_REG    uint64 = 0x2288
const FPGA_DBG_SPI_TXDATA1B_REG    uint64 = 0x228C
const FPGA_DBG_SPI_STATUS_REG      uint64 = 0x2290
const FPGA_DBG_SPI_CONTROL_REG     uint64 = 0x2294
const FPGA_DBG_SPI_SEM_REG         uint64 = 0x2298
const FPGA_DBG_SPI_SLAVESEL_REG    uint64 = 0x229C
const FPGA_DBG_SPI_EOP_VALUE_REG   uint64 = 0x22A0
const FPGA_DBG_SPI_MUXSEL_REG      uint64 = 0x22A4
const FPGA_FPGA_SPI_RXDATA_REG     uint64 = 0x22C0
const FPGA_FPGA_SPI_TXDATA4B_REG   uint64 = 0x22C4
const FPGA_FPGA_SPI_TXDATA2B_REG   uint64 = 0x22C8
const FPGA_FPGA_SPI_TXDATA1B_REG   uint64 = 0x22CC
const FPGA_FPGA_SPI_STATUS_REG     uint64 = 0x22D0
const FPGA_FPGA_SPI_CONTROL_REG    uint64 = 0x22D4
const FPGA_FPGA_SPI_SEM_REG        uint64 = 0x22D8
const FPGA_FPGA_SPI_SLAVESEL_REG   uint64 = 0x22DC
const FPGA_FPGA_SPI_EOP_VALUE_REG  uint64 = 0x22E0
const FPGA_FPGA_SPI_MUXSEL_REG     uint64 = 0x22E4
const FPGA_S0_UART_RXDATA_REG      uint64 = 0x10000
const FPGA_S0_UART_TXDATA_REG      uint64 = 0x10004
const FPGA_S0_UART_STAT_REG        uint64 = 0x10008
const FPGA_S0_UART_CTRL_REG        uint64 = 0x1000C
const FPGA_S1_UART_RXDATA_REG      uint64 = 0x10100
const FPGA_S1_UART_TXDATA_REG      uint64 = 0x10104
const FPGA_S1_UART_STAT_REG        uint64 = 0x10108
const FPGA_S1_UART_CTRL_REG        uint64 = 0x1010C
const FPGA_S2_UART_RXDATA_REG      uint64 = 0x10200
const FPGA_S2_UART_TXDATA_REG      uint64 = 0x10204
const FPGA_S2_UART_STAT_REG        uint64 = 0x10208
const FPGA_S2_UART_CTRL_REG        uint64 = 0x1020C
const FPGA_S3_UART_RXDATA_REG      uint64 = 0x10300
const FPGA_S3_UART_TXDATA_REG      uint64 = 0x10304
const FPGA_S3_UART_STAT_REG        uint64 = 0x10308
const FPGA_S3_UART_CTRL_REG        uint64 = 0x1030C
const FPGA_S4_UART_RXDATA_REG      uint64 = 0x10400
const FPGA_S4_UART_TXDATA_REG      uint64 = 0x10404
const FPGA_S4_UART_STAT_REG        uint64 = 0x10408
const FPGA_S4_UART_CTRL_REG        uint64 = 0x1040C
const FPGA_S5_UART_RXDATA_REG      uint64 = 0x10500
const FPGA_S5_UART_TXDATA_REG      uint64 = 0x10504
const FPGA_S5_UART_STAT_REG        uint64 = 0x10508
const FPGA_S5_UART_CTRL_REG        uint64 = 0x1050C
const FPGA_S6_UART_RXDATA_REG      uint64 = 0x10600
const FPGA_S6_UART_TXDATA_REG      uint64 = 0x10604
const FPGA_S6_UART_STAT_REG        uint64 = 0x10608
const FPGA_S6_UART_CTRL_REG        uint64 = 0x1060C
const FPGA_S7_UART_RXDATA_REG      uint64 = 0x10700
const FPGA_S7_UART_TXDATA_REG      uint64 = 0x10704
const FPGA_S7_UART_STAT_REG        uint64 = 0x10708
const FPGA_S7_UART_CTRL_REG        uint64 = 0x1070C
const FPGA_S8_UART_RXDATA_REG      uint64 = 0x10800
const FPGA_S8_UART_TXDATA_REG      uint64 = 0x10804
const FPGA_S8_UART_STAT_REG        uint64 = 0x10808
const FPGA_S8_UART_CTRL_REG        uint64 = 0x1080C
const FPGA_S9_UART_RXDATA_REG      uint64 = 0x10900
const FPGA_S9_UART_TXDATA_REG      uint64 = 0x10904
const FPGA_S9_UART_STAT_REG        uint64 = 0x10908
const FPGA_S9_UART_CTRL_REG        uint64 = 0x1090C
const FPGA_DBG_UART_RXDATA_REG     uint64 = 0x10A00
const FPGA_DBG_UART_TXDATA_REG     uint64 = 0x10A04
const FPGA_DBG_UART_STAT_REG       uint64 = 0x10A08
const FPGA_DBG_UART_CTRL_REG       uint64 = 0x10A0C
const FPGA_S0_UC_UART_CTRL_REG     uint64 = 0x10B00
const FPGA_S0_UC_UART_RXDATA_REG   uint64 = 0x10B04
const FPGA_S0_UC_UART_TXDATA_REG   uint64 = 0x10B08
const FPGA_S0_UC_UART_STAT_REG     uint64 = 0x10B0C
const FPGA_S1_UC_UART_RXDATA_REG   uint64 = 0x10C00
const FPGA_S1_UC_UART_TXDATA_REG   uint64 = 0x10C04
const FPGA_S1_UC_UART_STAT_REG     uint64 = 0x10C08
const FPGA_S1_UC_UART_CTRL_REG     uint64 = 0x10C0C
const FPGA_S2_UC_UART_RXDATA_REG   uint64 = 0x10D00
const FPGA_S2_UC_UART_TXDATA_REG   uint64 = 0x10D04
const FPGA_S2_UC_UART_STAT_REG     uint64 = 0x10D08
const FPGA_S2_UC_UART_CTRL_REG     uint64 = 0x10D0C
const FPGA_S3_UC_UART_RXDATA_REG   uint64 = 0x10E00
const FPGA_S3_UC_UART_TXDATA_REG   uint64 = 0x10E04
const FPGA_S3_UC_UART_STAT_REG     uint64 = 0x10E08
const FPGA_S3_UC_UART_CTRL_REG     uint64 = 0x10E0C
const FPGA_S4_UC_UART_RXDATA_REG   uint64 = 0x10F00
const FPGA_S4_UC_UART_TXDATA_REG   uint64 = 0x10F04
const FPGA_S4_UC_UART_STAT_REG     uint64 = 0x10F08
const FPGA_S4_UC_UART_CTRL_REG     uint64 = 0x10F0C
const FPGA_S5_UC_UART_RXDATA_REG   uint64 = 0x11000
const FPGA_S5_UC_UART_TXDATA_REG   uint64 = 0x11004
const FPGA_S5_UC_UART_STAT_REG     uint64 = 0x11008
const FPGA_S5_UC_UART_CTRL_REG     uint64 = 0x1100C
const FPGA_S6_UC_UART_RXDATA_REG   uint64 = 0x11100
const FPGA_S6_UC_UART_TXDATA_REG   uint64 = 0x11104
const FPGA_S6_UC_UART_STAT_REG     uint64 = 0x11108
const FPGA_S6_UC_UART_CTRL_REG     uint64 = 0x1110C
const FPGA_S7_UC_UART_RXDATA_REG   uint64 = 0x11200
const FPGA_S7_UC_UART_TXDATA_REG   uint64 = 0x11204
const FPGA_S7_UC_UART_STAT_REG     uint64 = 0x11208
const FPGA_S7_UC_UART_CTRL_REG     uint64 = 0x1120C
const FPGA_S8_UC_UART_RXDATA_REG   uint64 = 0x11300
const FPGA_S8_UC_UART_TXDATA_REG   uint64 = 0x11304
const FPGA_S8_UC_UART_STAT_REG     uint64 = 0x11308
const FPGA_S8_UC_UART_CTRL_REG     uint64 = 0x1130C
const FPGA_S9_UC_UART_RXDATA_REG   uint64 = 0x11400
const FPGA_S9_UC_UART_TXDATA_REG   uint64 = 0x11404
const FPGA_S9_UC_UART_STAT_REG     uint64 = 0x11408
const FPGA_S9_UC_UART_CTRL_REG     uint64 = 0x1140C





var PANAREA_FPGA_REGISTERS = []FPGA_REGISTERS {
    FPGA_REGISTERS{"FPGA_REV_ID_REG                ",             FPGA_REV_ID_REG},
    FPGA_REGISTERS{"FPGA_DATECODE_REG              ",             FPGA_DATECODE_REG},
    FPGA_REGISTERS{"FPGA_TIMECODE_REG              ",             FPGA_TIMECODE_REG},
    FPGA_REGISTERS{"FPGA_BOARD_REV_ID_REG          ",             FPGA_BOARD_REV_ID_REG},
    FPGA_REGISTERS{"FGPA_SCRATCH_0_REG             ",             FPGA_SCRATCH_0_REG},
    FPGA_REGISTERS{"FGPA_SCRATCH_1_REG             ",             FPGA_SCRATCH_1_REG},
    FPGA_REGISTERS{"FGPA_SCRATCH_2_REG             ",             FPGA_SCRATCH_2_REG},
    FPGA_REGISTERS{"FGPA_SCRATCH_3_REG             ",             FPGA_SCRATCH_3_REG},
    FPGA_REGISTERS{"FGPA_DEBUG_0_REG               ",             FPGA_DEBUG_0_REG},
    FPGA_REGISTERS{"FGPA_DEBUG_1_REG               ",             FPGA_DEBUG_1_REG},
    FPGA_REGISTERS{"FGPA_DEBUG_2_REG               ",             FPGA_DEBUG_2_REG},
    FPGA_REGISTERS{"FGPA_DEBUG_3_REG               ",             FPGA_DEBUG_3_REG},
    FPGA_REGISTERS{"FGPA_INT0_EN_REG               ",             FPGA_INT0_EN_REG},
    FPGA_REGISTERS{"FGPA_INT1_EN_REG               ",             FPGA_INT1_EN_REG},
    FPGA_REGISTERS{"FGPA_INT2_EN_REG               ",             FPGA_INT2_EN_REG},
    FPGA_REGISTERS{"FGPA_INT3_EN_REG               ",             FPGA_INT3_EN_REG},
    FPGA_REGISTERS{"FGPA_INT0_PEND_REG             ",             FPGA_INT0_PEND_REG},
    FPGA_REGISTERS{"FGPA_INT1_PEND_REG             ",             FPGA_INT1_PEND_REG},
    FPGA_REGISTERS{"FGPA_INT2_PEND_REG             ",             FPGA_INT2_PEND_REG},
    FPGA_REGISTERS{"FGPA_INT3_PEND_REG             ",             FPGA_INT3_PEND_REG},
    FPGA_REGISTERS{"FGPA_RESET_CAUSE_0_REG         ",             FPGA_RESET_CAUSE_0_REG},
    FPGA_REGISTERS{"FGPA_RESET_CAUSE_1_REG         ",             FPGA_RESET_CAUSE_1_REG},
    FPGA_REGISTERS{"FGPA_RESET_CAUSE_2_REG         ",             FPGA_RESET_CAUSE_2_REG},
    FPGA_REGISTERS{"FGPA_RESET_CAUSE_3_REG         ",             FPGA_RESET_CAUSE_3_REG},
    FPGA_REGISTERS{"FGPA_SOFT_RESET_REG            ",             FPGA_SOFT_RESET_REG},
    FPGA_REGISTERS{"FGPA_FLSH_CTRL_REG             ",             FPGA_FLSH_CTRL_REG},
    FPGA_REGISTERS{"FGPA_LED_CONFIG_REG            ",             FPGA_LED_CONFIG_REG},
    FPGA_REGISTERS{"FGPA_LED_SYSTEM_REG            ",             FPGA_LED_SYSTEM_REG},
    FPGA_REGISTERS{"FGPA_LED_FAN0_REG              ",             FPGA_LED_FAN0_REG},
    FPGA_REGISTERS{"FGPA_LED_FAN1_REG              ",             FPGA_LED_FAN1_REG},
    FPGA_REGISTERS{"FGPA_PSU_CTRL_REG              ",             FPGA_PSU_CTRL_REG},
    FPGA_REGISTERS{"FGPA_PSU_STAT_REG              ",             FPGA_PSU_STAT_REG},
    FPGA_REGISTERS{"FGPA_FAN_PWR_CTRL_REG          ",             FPGA_FAN_PWR_CTRL_REG},
    FPGA_REGISTERS{"FGPA_FAN_PWM_CTRL0_REG         ",             FPGA_FAN_PWM_CTRL0_REG},
    FPGA_REGISTERS{"FGPA_FAN_PWM_CTRL1_REG         ",             FPGA_FAN_PWM_CTRL1_REG},
    FPGA_REGISTERS{"FGPA_FAN_STAT_REG              ",             FPGA_FAN_STAT_REG},
    FPGA_REGISTERS{"FGPA_FAN0_TACH_REG             ",             FPGA_FAN0_TACH_REG},
    FPGA_REGISTERS{"FGPA_FAN1_TACH_REG             ",             FPGA_FAN1_TACH_REG},
    FPGA_REGISTERS{"FGPA_FAN2_TACH_REG             ",             FPGA_FAN2_TACH_REG},
    FPGA_REGISTERS{"FGPA_FAN3_TACH_REG             ",             FPGA_FAN3_TACH_REG},
    FPGA_REGISTERS{"FGPA_FAN4_TACH_REG             ",             FPGA_FAN4_TACH_REG},
    FPGA_REGISTERS{"FGPA_S0_CONTROL_REG            ",             FPGA_S0_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S1_CONTROL_REG            ",             FPGA_S1_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S2_CONTROL_REG            ",             FPGA_S2_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S3_CONTROL_REG            ",             FPGA_S3_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S4_CONTROL_REG            ",             FPGA_S4_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S5_CONTROL_REG            ",             FPGA_S5_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S6_CONTROL_REG            ",             FPGA_S6_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S7_CONTROL_REG            ",             FPGA_S7_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S8_CONTROL_REG            ",             FPGA_S8_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S9_CONTROL_REG            ",             FPGA_S9_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_MISC_CTRL_REG             ",             FPGA_MISC_CTRL_REG},
    FPGA_REGISTERS{"FGPA_MISC_STAT_REG             ",             FPGA_MISC_STAT_REG},
    FPGA_REGISTERS{"FGPA_CPU_CTRL_REG              ",             FPGA_CPU_CTRL_REG},
    FPGA_REGISTERS{"FGPA_CPU_STAT_REG              ",             FPGA_CPU_STAT_REG},
    FPGA_REGISTERS{"FGPA_WDOG_CTRL_REG             ",             FPGA_WDOG_CTRL_REG},
    FPGA_REGISTERS{"FGPA_WDOG_RESET_REG            ",             FPGA_WDOG_RESET_REG},
    FPGA_REGISTERS{"FGPA_E0_SMI_CMD_REG            ",             FPGA_E0_SMI_CMD_REG},
    FPGA_REGISTERS{"FGPA_E0_SMI_DATA_REG           ",             FPGA_E0_SMI_DATA_REG},
    FPGA_REGISTERS{"FGPA_E1_SMI_CMD_REG            ",             FPGA_E1_SMI_CMD_REG},
    FPGA_REGISTERS{"FGPA_E1_SMI_DATA_REG           ",             FPGA_E1_SMI_DATA_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_PRSCL_LO_REG       ",             FPGA_S0_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_PRSCL_HI_REG       ",             FPGA_S0_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_CTRL_REG           ",             FPGA_S0_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_TX_REG             ",             FPGA_S0_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_RX_REG             ",             FPGA_S0_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_CMD_REG            ",             FPGA_S0_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_STAT_REG           ",             FPGA_S0_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_MUX_SEL_REG        ",             FPGA_S0_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_RST_REG            ",             FPGA_S0_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S0_I2C_SEM_REG            ",             FPGA_S0_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_PRSCL_LO_REG       ",             FPGA_S1_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_PRSCL_HI_REG       ",             FPGA_S1_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_CTRL_REG           ",             FPGA_S1_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_TX_REG             ",             FPGA_S1_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_RX_REG             ",             FPGA_S1_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_CMD_REG            ",             FPGA_S1_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_STAT_REG           ",             FPGA_S1_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_MUX_SEL_REG        ",             FPGA_S1_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_RST_REG            ",             FPGA_S1_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S1_I2C_SEM_REG            ",             FPGA_S1_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_PRSCL_LO_REG       ",             FPGA_S2_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_PRSCL_HI_REG       ",             FPGA_S2_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_CTRL_REG           ",             FPGA_S2_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_TX_REG             ",             FPGA_S2_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_RX_REG             ",             FPGA_S2_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_CMD_REG            ",             FPGA_S2_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_STAT_REG           ",             FPGA_S2_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_MUX_SEL_REG        ",             FPGA_S2_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_RST_REG            ",             FPGA_S2_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S2_I2C_SEM_REG            ",             FPGA_S2_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_PRSCL_LO_REG       ",             FPGA_S3_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_PRSCL_HI_REG       ",             FPGA_S3_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_CTRL_REG           ",             FPGA_S3_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_TX_REG             ",             FPGA_S3_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_RX_REG             ",             FPGA_S3_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_CMD_REG            ",             FPGA_S3_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_STAT_REG           ",             FPGA_S3_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_MUX_SEL_REG        ",             FPGA_S3_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_RST_REG            ",             FPGA_S3_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S3_I2C_SEM_REG            ",             FPGA_S3_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_PRSCL_LO_REG       ",             FPGA_S4_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_PRSCL_HI_REG       ",             FPGA_S4_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_CTRL_REG           ",             FPGA_S4_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_TX_REG             ",             FPGA_S4_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_RX_REG             ",             FPGA_S4_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_CMD_REG            ",             FPGA_S4_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_STAT_REG           ",             FPGA_S4_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_MUX_SEL_REG        ",             FPGA_S4_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_RST_REG            ",             FPGA_S4_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S4_I2C_SEM_REG            ",             FPGA_S4_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_PRSCL_LO_REG       ",             FPGA_S5_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_PRSCL_HI_REG       ",             FPGA_S5_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_CTRL_REG           ",             FPGA_S5_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_TX_REG             ",             FPGA_S5_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_RX_REG             ",             FPGA_S5_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_CMD_REG            ",             FPGA_S5_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_STAT_REG           ",             FPGA_S5_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_MUX_SEL_REG        ",             FPGA_S5_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_RST_REG            ",             FPGA_S5_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S5_I2C_SEM_REG            ",             FPGA_S5_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_PRSCL_LO_REG       ",             FPGA_S6_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_PRSCL_HI_REG       ",             FPGA_S6_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_CTRL_REG           ",             FPGA_S6_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_TX_REG             ",             FPGA_S6_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_RX_REG             ",             FPGA_S6_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_CMD_REG            ",             FPGA_S6_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_STAT_REG           ",             FPGA_S6_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_MUX_SEL_REG        ",             FPGA_S6_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_RST_REG            ",             FPGA_S6_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S6_I2C_SEM_REG            ",             FPGA_S6_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_PRSCL_LO_REG       ",             FPGA_S7_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_PRSCL_HI_REG       ",             FPGA_S7_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_CTRL_REG           ",             FPGA_S7_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_TX_REG             ",             FPGA_S7_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_RX_REG             ",             FPGA_S7_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_CMD_REG            ",             FPGA_S7_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_STAT_REG           ",             FPGA_S7_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_MUX_SEL_REG        ",             FPGA_S7_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_RST_REG            ",             FPGA_S7_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S7_I2C_SEM_REG            ",             FPGA_S7_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_PRSCL_LO_REG       ",             FPGA_S8_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_PRSCL_HI_REG       ",             FPGA_S8_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_CTRL_REG           ",             FPGA_S8_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_TX_REG             ",             FPGA_S8_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_RX_REG             ",             FPGA_S8_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_CMD_REG            ",             FPGA_S8_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_STAT_REG           ",             FPGA_S8_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_MUX_SEL_REG        ",             FPGA_S8_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_RST_REG            ",             FPGA_S8_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S8_I2C_SEM_REG            ",             FPGA_S8_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_PRSCL_LO_REG       ",             FPGA_S9_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_PRSCL_HI_REG       ",             FPGA_S9_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_CTRL_REG           ",             FPGA_S9_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_TX_REG             ",             FPGA_S9_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_RX_REG             ",             FPGA_S9_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_CMD_REG            ",             FPGA_S9_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_STAT_REG           ",             FPGA_S9_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_MUX_SEL_REG        ",             FPGA_S9_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_RST_REG            ",             FPGA_S9_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_S9_I2C_SEM_REG            ",             FPGA_S9_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_PRSCL_LO_REG      ",             FPGA_DBG_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_PRSCL_HI_REG      ",             FPGA_DBG_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_CTRL_REG          ",             FPGA_DBG_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_TX_REG            ",             FPGA_DBG_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_RX_REG            ",             FPGA_DBG_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_CMD_REG           ",             FPGA_DBG_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_STAT_REG          ",             FPGA_DBG_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_MUX_SEL_REG       ",             FPGA_DBG_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_RST_REG           ",             FPGA_DBG_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_DBG_I2C_SEM_REG           ",             FPGA_DBG_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_PRSCL_LO_REG     ",             FPGA_PSU0_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_PRSCL_HI_REG     ",             FPGA_PSU0_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_CTRL_REG         ",             FPGA_PSU0_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_TX_REG           ",             FPGA_PSU0_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_RX_REG           ",             FPGA_PSU0_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_CMD_REG          ",             FPGA_PSU0_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_STAT_REG         ",             FPGA_PSU0_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_MUX_SEL_REG      ",             FPGA_PSU0_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_RST_REG          ",             FPGA_PSU0_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_PSU0_I2C_SEM_REG          ",             FPGA_PSU0_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_PRSCL_LO_REG     ",             FPGA_PSU1_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_PRSCL_HI_REG     ",             FPGA_PSU1_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_CTRL_REG         ",             FPGA_PSU1_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_TX_REG           ",             FPGA_PSU1_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_RX_REG           ",             FPGA_PSU1_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_CMD_REG          ",             FPGA_PSU1_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_STAT_REG         ",             FPGA_PSU1_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_MUX_SEL_REG      ",             FPGA_PSU1_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_RST_REG          ",             FPGA_PSU1_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_PSU1_I2C_SEM_REG          ",             FPGA_PSU1_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_PRSCL_LO_REG      ",             FPGA_PMB_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_PRSCL_HI_REG      ",             FPGA_PMB_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_CTRL_REG          ",             FPGA_PMB_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_TX_REG            ",             FPGA_PMB_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_RX_REG            ",             FPGA_PMB_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_CMD_REG           ",             FPGA_PMB_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_STAT_REG          ",             FPGA_PMB_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_MUX_SEL_REG       ",             FPGA_PMB_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_RST_REG           ",             FPGA_PMB_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_PMB_I2C_SEM_REG           ",             FPGA_PMB_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_PRSCL_LO_REG     ",             FPGA_IOBR_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_PRSCL_HI_REG     ",             FPGA_IOBR_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_CTRL_REG         ",             FPGA_IOBR_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_TX_REG           ",             FPGA_IOBR_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_RX_REG           ",             FPGA_IOBR_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_CMD_REG          ",             FPGA_IOBR_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_STAT_REG         ",             FPGA_IOBR_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_MUX_SEL_REG      ",             FPGA_IOBR_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_RST_REG          ",             FPGA_IOBR_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_IOBR_I2C_SEM_REG          ",             FPGA_IOBR_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_PRSCL_LO_REG     ",             FPGA_IOBL_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_PRSCL_HI_REG     ",             FPGA_IOBL_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_CTRL_REG         ",             FPGA_IOBL_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_TX_REG           ",             FPGA_IOBL_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_RX_REG           ",             FPGA_IOBL_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_CMD_REG          ",             FPGA_IOBL_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_STAT_REG         ",             FPGA_IOBL_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_MUX_SEL_REG      ",             FPGA_IOBL_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_RST_REG          ",             FPGA_IOBL_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_IOBL_I2C_SEM_REG          ",             FPGA_IOBL_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_PRSCL_LO_REG     ",             FPGA_FPIC_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_PRSCL_HI_REG     ",             FPGA_FPIC_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_CTRL_REG         ",             FPGA_FPIC_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_TX_REG           ",             FPGA_FPIC_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_RX_REG           ",             FPGA_FPIC_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_CMD_REG          ",             FPGA_FPIC_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_STAT_REG         ",             FPGA_FPIC_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_MUX_SEL_REG      ",             FPGA_FPIC_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_RST_REG          ",             FPGA_FPIC_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_FPIC_I2C_SEM_REG          ",             FPGA_FPIC_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_PRSCL_LO_REG       ",             FPGA_ID_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_PRSCL_HI_REG       ",             FPGA_ID_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_CTRL_REG           ",             FPGA_ID_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_TX_REG             ",             FPGA_ID_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_RX_REG             ",             FPGA_ID_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_CMD_REG            ",             FPGA_ID_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_STAT_REG           ",             FPGA_ID_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_MUX_SEL_REG        ",             FPGA_ID_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_RST_REG            ",             FPGA_ID_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_ID_I2C_SEM_REG            ",             FPGA_ID_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_PRSCL_LO_REG     ",             FPGA_MCIO_I2C_PRSCL_LO_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_PRSCL_HI_REG     ",             FPGA_MCIO_I2C_PRSCL_HI_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_CTRL_REG         ",             FPGA_MCIO_I2C_CTRL_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_TX_REG           ",             FPGA_MCIO_I2C_TX_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_RX_REG           ",             FPGA_MCIO_I2C_RX_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_CMD_REG          ",             FPGA_MCIO_I2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_STAT_REG         ",             FPGA_MCIO_I2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_MUX_SEL_REG      ",             FPGA_MCIO_I2C_MUX_SEL_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_RST_REG          ",             FPGA_MCIO_I2C_RST_REG},
    FPGA_REGISTERS{"FGPA_MCIO_I2C_SEM_REG          ",             FPGA_MCIO_I2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_CMD_REG            ",             FPGA_S0_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_STAT_REG           ",             FPGA_S0_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_ADDR0_REG          ",             FPGA_S0_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_ADDR1_REG          ",             FPGA_S0_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_TXDATA_REG         ",             FPGA_S0_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_RXDATA_REG         ",             FPGA_S0_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_SEM_REG            ",             FPGA_S0_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_MAGIC_REG          ",             FPGA_S0_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_TXFIFO_REG         ",             FPGA_S0_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_RXFIFO_REG         ",             FPGA_S0_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S0_J2C_SIZE_REG           ",             FPGA_S0_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_INIT_REG            ",             FPGA_S0_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_CMD_REG             ",             FPGA_S0_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_STATUS_REG          ",             FPGA_S0_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_DATA_REG            ",             FPGA_S0_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_ADDR0_REG           ",             FPGA_S0_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_ADDR1_REG           ",             FPGA_S0_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S0_OW_EOM_WIDTH_REG       ",             FPGA_S0_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_CMD_REG            ",             FPGA_S1_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_STAT_REG           ",             FPGA_S1_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_ADDR0_REG          ",             FPGA_S1_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_ADDR1_REG          ",             FPGA_S1_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_TXDATA_REG         ",             FPGA_S1_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_RXDATA_REG         ",             FPGA_S1_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_SEM_REG            ",             FPGA_S1_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_MAGIC_REG          ",             FPGA_S1_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_TXFIFO_REG         ",             FPGA_S1_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_RXFIFO_REG         ",             FPGA_S1_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_SIZE_REG           ",             FPGA_S1_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_INIT_REG            ",             FPGA_S1_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_CMD_REG             ",             FPGA_S1_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_STATUS_REG          ",             FPGA_S1_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_DATA_REG            ",             FPGA_S1_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_ADDR0_REG           ",             FPGA_S1_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_ADDR1_REG           ",             FPGA_S1_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S1_OW_EOM_WIDTH_REG       ",             FPGA_S1_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_CMD_REG            ",             FPGA_S2_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_STAT_REG           ",             FPGA_S2_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_ADDR0_REG          ",             FPGA_S2_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_ADDR1_REG          ",             FPGA_S2_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_TXDATA_REG         ",             FPGA_S2_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_RXDATA_REG         ",             FPGA_S2_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_SEM_REG            ",             FPGA_S2_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_MAGIC_REG          ",             FPGA_S2_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_TXFIFO_REG         ",             FPGA_S2_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_RXFIFO_REG         ",             FPGA_S2_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_SIZE_REG           ",             FPGA_S2_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_INIT_REG            ",             FPGA_S2_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_CMD_REG             ",             FPGA_S2_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_STATUS_REG          ",             FPGA_S2_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_DATA_REG            ",             FPGA_S2_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_ADDR0_REG           ",             FPGA_S2_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_ADDR1_REG           ",             FPGA_S2_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S2_OW_EOM_WIDTH_REG       ",             FPGA_S2_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_CMD_REG            ",             FPGA_S3_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_STAT_REG           ",             FPGA_S3_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_ADDR0_REG          ",             FPGA_S3_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_ADDR1_REG          ",             FPGA_S3_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_TXDATA_REG         ",             FPGA_S3_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_RXDATA_REG         ",             FPGA_S3_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_SEM_REG            ",             FPGA_S3_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_MAGIC_REG          ",             FPGA_S3_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_TXFIFO_REG         ",             FPGA_S3_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_RXFIFO_REG         ",             FPGA_S3_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_SIZE_REG           ",             FPGA_S3_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_INIT_REG            ",             FPGA_S3_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_CMD_REG             ",             FPGA_S3_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_STATUS_REG          ",             FPGA_S3_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_DATA_REG            ",             FPGA_S3_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_ADDR0_REG           ",             FPGA_S3_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_ADDR1_REG           ",             FPGA_S3_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S3_OW_EOM_WIDTH_REG       ",             FPGA_S3_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_CMD_REG            ",             FPGA_S4_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_STAT_REG           ",             FPGA_S4_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_ADDR0_REG          ",             FPGA_S4_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_ADDR1_REG          ",             FPGA_S4_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_TXDATA_REG         ",             FPGA_S4_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_RXDATA_REG         ",             FPGA_S4_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_SEM_REG            ",             FPGA_S4_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_MAGIC_REG          ",             FPGA_S4_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_TXFIFO_REG         ",             FPGA_S4_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_RXFIFO_REG         ",             FPGA_S4_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_SIZE_REG           ",             FPGA_S4_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_INIT_REG            ",             FPGA_S4_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_CMD_REG             ",             FPGA_S4_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_STATUS_REG          ",             FPGA_S4_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_DATA_REG            ",             FPGA_S4_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_ADDR0_REG           ",             FPGA_S4_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_ADDR1_REG           ",             FPGA_S4_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S4_OW_EOM_WIDTH_REG       ",             FPGA_S4_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_CMD_REG            ",             FPGA_S5_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_STAT_REG           ",             FPGA_S5_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_ADDR0_REG          ",             FPGA_S5_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_ADDR1_REG          ",             FPGA_S5_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_TXDATA_REG         ",             FPGA_S5_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_RXDATA_REG         ",             FPGA_S5_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_SEM_REG            ",             FPGA_S5_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_MAGIC_REG          ",             FPGA_S5_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_TXFIFO_REG         ",             FPGA_S5_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_RXFIFO_REG         ",             FPGA_S5_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_SIZE_REG           ",             FPGA_S5_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_INIT_REG            ",             FPGA_S5_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_CMD_REG             ",             FPGA_S5_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_STATUS_REG          ",             FPGA_S5_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_DATA_REG            ",             FPGA_S5_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_ADDR0_REG           ",             FPGA_S5_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_ADDR1_REG           ",             FPGA_S5_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S5_OW_EOM_WIDTH_REG       ",             FPGA_S5_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_CMD_REG            ",             FPGA_S6_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_STAT_REG           ",             FPGA_S6_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_ADDR0_REG          ",             FPGA_S6_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_ADDR1_REG          ",             FPGA_S6_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_TXDATA_REG         ",             FPGA_S6_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_RXDATA_REG         ",             FPGA_S6_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_SEM_REG            ",             FPGA_S6_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_MAGIC_REG          ",             FPGA_S6_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_TXFIFO_REG         ",             FPGA_S6_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_RXFIFO_REG         ",             FPGA_S6_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_SIZE_REG           ",             FPGA_S6_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_INIT_REG            ",             FPGA_S6_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_CMD_REG             ",             FPGA_S6_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_STATUS_REG          ",             FPGA_S6_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_DATA_REG            ",             FPGA_S6_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_ADDR0_REG           ",             FPGA_S6_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_ADDR1_REG           ",             FPGA_S6_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S6_OW_EOM_WIDTH_REG       ",             FPGA_S6_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_CMD_REG            ",             FPGA_S7_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_STAT_REG           ",             FPGA_S7_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_ADDR0_REG          ",             FPGA_S7_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_ADDR1_REG          ",             FPGA_S7_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_TXDATA_REG         ",             FPGA_S7_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_RXDATA_REG         ",             FPGA_S7_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_SEM_REG            ",             FPGA_S7_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_MAGIC_REG          ",             FPGA_S7_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_TXFIFO_REG         ",             FPGA_S7_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_RXFIFO_REG         ",             FPGA_S7_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_SIZE_REG           ",             FPGA_S7_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_INIT_REG            ",             FPGA_S7_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_CMD_REG             ",             FPGA_S7_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_STATUS_REG          ",             FPGA_S7_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_DATA_REG            ",             FPGA_S7_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_ADDR0_REG           ",             FPGA_S7_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_ADDR1_REG           ",             FPGA_S7_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S7_OW_EOM_WIDTH_REG       ",             FPGA_S7_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_CMD_REG            ",             FPGA_S8_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_STAT_REG           ",             FPGA_S8_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_ADDR0_REG          ",             FPGA_S8_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_ADDR1_REG          ",             FPGA_S8_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_TXDATA_REG         ",             FPGA_S8_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_RXDATA_REG         ",             FPGA_S8_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_SEM_REG            ",             FPGA_S8_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_MAGIC_REG          ",             FPGA_S8_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_TXFIFO_REG         ",             FPGA_S8_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_RXFIFO_REG         ",             FPGA_S8_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_SIZE_REG           ",             FPGA_S8_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_INIT_REG            ",             FPGA_S8_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_CMD_REG             ",             FPGA_S8_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_STATUS_REG          ",             FPGA_S8_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_DATA_REG            ",             FPGA_S8_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_ADDR0_REG           ",             FPGA_S8_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_ADDR1_REG           ",             FPGA_S8_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S8_OW_EOM_WIDTH_REG       ",             FPGA_S8_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_CMD_REG            ",             FPGA_S9_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_STAT_REG           ",             FPGA_S9_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_ADDR0_REG          ",             FPGA_S9_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_ADDR1_REG          ",             FPGA_S9_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_TXDATA_REG         ",             FPGA_S9_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_RXDATA_REG         ",             FPGA_S9_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_SEM_REG            ",             FPGA_S9_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_MAGIC_REG          ",             FPGA_S9_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_TXFIFO_REG         ",             FPGA_S9_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_RXFIFO_REG         ",             FPGA_S9_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_SIZE_REG           ",             FPGA_S9_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_INIT_REG            ",             FPGA_S9_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_CMD_REG             ",             FPGA_S9_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_STATUS_REG          ",             FPGA_S9_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_DATA_REG            ",             FPGA_S9_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_ADDR0_REG           ",             FPGA_S9_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_ADDR1_REG           ",             FPGA_S9_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S9_OW_EOM_WIDTH_REG       ",             FPGA_S9_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_CMD_REG           ",             FPGA_DBG_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_STAT_REG          ",             FPGA_DBG_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_ADDR0_REG         ",             FPGA_DBG_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_ADDR1_REG         ",             FPGA_DBG_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_TXDATA_REG        ",             FPGA_DBG_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_RXDATA_REG        ",             FPGA_DBG_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_SEM_REG           ",             FPGA_DBG_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_MAGIC_REG         ",             FPGA_DBG_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_TXFIFO_REG        ",             FPGA_DBG_J2C_TXFIFO_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_RXFIFO_REG        ",             FPGA_DBG_J2C_RXFIFO_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_SIZE_REG          ",             FPGA_DBG_J2C_SIZE_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_INIT_REG           ",             FPGA_DBG_OW_INIT_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_CMD_REG            ",             FPGA_DBG_OW_CMD_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_STATUS_REG         ",             FPGA_DBG_OW_STATUS_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_DATA_REG           ",             FPGA_DBG_OW_DATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_ADDR0_REG          ",             FPGA_DBG_OW_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_ADDR1_REG          ",             FPGA_DBG_OW_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_DBG_OW_EOM_WIDTH_REG      ",             FPGA_DBG_OW_EOM_WIDTH_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_RXDATA_REG         ",             FPGA_S0_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_TXDATA4B_REG       ",             FPGA_S0_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_TXDATA2B_REG       ",             FPGA_S0_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_TXDATA1B_REG       ",             FPGA_S0_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_STATUS_REG         ",             FPGA_S0_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_CONTROL_REG        ",             FPGA_S0_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_SEM_REG            ",             FPGA_S0_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_SLAVESEL_REG       ",             FPGA_S0_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_EOP_VALUE_REG      ",             FPGA_S0_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S0_SPI_MUXSEL_REG         ",             FPGA_S0_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_RXDATA_REG         ",             FPGA_S1_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_TXDATA4B_REG       ",             FPGA_S1_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_TXDATA2B_REG       ",             FPGA_S1_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_TXDATA1B_REG       ",             FPGA_S1_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_STATUS_REG         ",             FPGA_S1_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_CONTROL_REG        ",             FPGA_S1_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_SEM_REG            ",             FPGA_S1_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_SLAVESEL_REG       ",             FPGA_S1_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_EOP_VALUE_REG      ",             FPGA_S1_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S1_SPI_MUXSEL_REG         ",             FPGA_S1_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_RXDATA_REG         ",             FPGA_S2_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_TXDATA4B_REG       ",             FPGA_S2_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_TXDATA2B_REG       ",             FPGA_S2_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_TXDATA1B_REG       ",             FPGA_S2_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_STATUS_REG         ",             FPGA_S2_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_CONTROL_REG        ",             FPGA_S2_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_SEM_REG            ",             FPGA_S2_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_SLAVESEL_REG       ",             FPGA_S2_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_EOP_VALUE_REG      ",             FPGA_S2_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S2_SPI_MUXSEL_REG         ",             FPGA_S2_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_RXDATA_REG         ",             FPGA_S3_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_TXDATA4B_REG       ",             FPGA_S3_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_TXDATA2B_REG       ",             FPGA_S3_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_TXDATA1B_REG       ",             FPGA_S3_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_STATUS_REG         ",             FPGA_S3_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_CONTROL_REG        ",             FPGA_S3_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_SEM_REG            ",             FPGA_S3_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_SLAVESEL_REG       ",             FPGA_S3_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_EOP_VALUE_REG      ",             FPGA_S3_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S3_SPI_MUXSEL_REG         ",             FPGA_S3_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_RXDATA_REG         ",             FPGA_S4_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_TXDATA4B_REG       ",             FPGA_S4_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_TXDATA2B_REG       ",             FPGA_S4_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_TXDATA1B_REG       ",             FPGA_S4_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_STATUS_REG         ",             FPGA_S4_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_CONTROL_REG        ",             FPGA_S4_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_SEM_REG            ",             FPGA_S4_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_SLAVESEL_REG       ",             FPGA_S4_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_EOP_VALUE_REG      ",             FPGA_S4_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S4_SPI_MUXSEL_REG         ",             FPGA_S4_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_RXDATA_REG         ",             FPGA_S5_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_TXDATA4B_REG       ",             FPGA_S5_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_TXDATA2B_REG       ",             FPGA_S5_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_TXDATA1B_REG       ",             FPGA_S5_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_STATUS_REG         ",             FPGA_S5_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_CONTROL_REG        ",             FPGA_S5_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_SEM_REG            ",             FPGA_S5_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_SLAVESEL_REG       ",             FPGA_S5_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_EOP_VALUE_REG      ",             FPGA_S5_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S5_SPI_MUXSEL_REG         ",             FPGA_S5_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_RXDATA_REG         ",             FPGA_S6_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_TXDATA4B_REG       ",             FPGA_S6_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_TXDATA2B_REG       ",             FPGA_S6_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_TXDATA1B_REG       ",             FPGA_S6_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_STATUS_REG         ",             FPGA_S6_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_CONTROL_REG        ",             FPGA_S6_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_SEM_REG            ",             FPGA_S6_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_SLAVESEL_REG       ",             FPGA_S6_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_EOP_VALUE_REG      ",             FPGA_S6_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S6_SPI_MUXSEL_REG         ",             FPGA_S6_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_RXDATA_REG         ",             FPGA_S7_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_TXDATA4B_REG       ",             FPGA_S7_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_TXDATA2B_REG       ",             FPGA_S7_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_TXDATA1B_REG       ",             FPGA_S7_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_STATUS_REG         ",             FPGA_S7_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_CONTROL_REG        ",             FPGA_S7_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_SEM_REG            ",             FPGA_S7_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_SLAVESEL_REG       ",             FPGA_S7_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_EOP_VALUE_REG      ",             FPGA_S7_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S7_SPI_MUXSEL_REG         ",             FPGA_S7_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_RXDATA_REG         ",             FPGA_S8_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_TXDATA4B_REG       ",             FPGA_S8_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_TXDATA2B_REG       ",             FPGA_S8_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_TXDATA1B_REG       ",             FPGA_S8_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_STATUS_REG         ",             FPGA_S8_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_CONTROL_REG        ",             FPGA_S8_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_SEM_REG            ",             FPGA_S8_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_SLAVESEL_REG       ",             FPGA_S8_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_EOP_VALUE_REG      ",             FPGA_S8_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S8_SPI_MUXSEL_REG         ",             FPGA_S8_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_RXDATA_REG         ",             FPGA_S9_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_TXDATA4B_REG       ",             FPGA_S9_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_TXDATA2B_REG       ",             FPGA_S9_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_TXDATA1B_REG       ",             FPGA_S9_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_STATUS_REG         ",             FPGA_S9_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_CONTROL_REG        ",             FPGA_S9_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_SEM_REG            ",             FPGA_S9_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_SLAVESEL_REG       ",             FPGA_S9_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_EOP_VALUE_REG      ",             FPGA_S9_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_S9_SPI_MUXSEL_REG         ",             FPGA_S9_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_RXDATA_REG        ",             FPGA_DBG_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_TXDATA4B_REG      ",             FPGA_DBG_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_TXDATA2B_REG      ",             FPGA_DBG_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_TXDATA1B_REG      ",             FPGA_DBG_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_STATUS_REG        ",             FPGA_DBG_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_CONTROL_REG       ",             FPGA_DBG_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_SEM_REG           ",             FPGA_DBG_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_SLAVESEL_REG      ",             FPGA_DBG_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_EOP_VALUE_REG     ",             FPGA_DBG_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_DBG_SPI_MUXSEL_REG        ",             FPGA_DBG_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_RXDATA_REG       ",             FPGA_FPGA_SPI_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_TXDATA4B_REG     ",             FPGA_FPGA_SPI_TXDATA4B_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_TXDATA2B_REG     ",             FPGA_FPGA_SPI_TXDATA2B_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_TXDATA1B_REG     ",             FPGA_FPGA_SPI_TXDATA1B_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_STATUS_REG       ",             FPGA_FPGA_SPI_STATUS_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_CONTROL_REG      ",             FPGA_FPGA_SPI_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_SEM_REG          ",             FPGA_FPGA_SPI_SEM_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_SLAVESEL_REG     ",             FPGA_FPGA_SPI_SLAVESEL_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_EOP_VALUE_REG    ",             FPGA_FPGA_SPI_EOP_VALUE_REG},
    FPGA_REGISTERS{"FGPA_FPGA_SPI_MUXSEL_REG       ",             FPGA_FPGA_SPI_MUXSEL_REG},
    FPGA_REGISTERS{"FGPA_S0_UART_RXDATA_REG        ",             FPGA_S0_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_UART_TXDATA_REG        ",             FPGA_S0_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_UART_STAT_REG          ",             FPGA_S0_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S0_UART_CTRL_REG          ",             FPGA_S0_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S1_UART_RXDATA_REG        ",             FPGA_S1_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_UART_TXDATA_REG        ",             FPGA_S1_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_UART_STAT_REG          ",             FPGA_S1_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_UART_CTRL_REG          ",             FPGA_S1_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S2_UART_RXDATA_REG        ",             FPGA_S2_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_UART_TXDATA_REG        ",             FPGA_S2_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_UART_STAT_REG          ",             FPGA_S2_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S2_UART_CTRL_REG          ",             FPGA_S2_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S3_UART_RXDATA_REG        ",             FPGA_S3_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_UART_TXDATA_REG        ",             FPGA_S3_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_UART_STAT_REG          ",             FPGA_S3_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S3_UART_CTRL_REG          ",             FPGA_S3_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S4_UART_RXDATA_REG        ",             FPGA_S4_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_UART_TXDATA_REG        ",             FPGA_S4_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_UART_STAT_REG          ",             FPGA_S4_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S4_UART_CTRL_REG          ",             FPGA_S4_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S5_UART_RXDATA_REG        ",             FPGA_S5_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_UART_TXDATA_REG        ",             FPGA_S5_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_UART_STAT_REG          ",             FPGA_S5_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S5_UART_CTRL_REG          ",             FPGA_S5_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S6_UART_RXDATA_REG        ",             FPGA_S6_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_UART_TXDATA_REG        ",             FPGA_S6_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_UART_STAT_REG          ",             FPGA_S6_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S6_UART_CTRL_REG          ",             FPGA_S6_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S7_UART_RXDATA_REG        ",             FPGA_S7_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_UART_TXDATA_REG        ",             FPGA_S7_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_UART_STAT_REG          ",             FPGA_S7_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S7_UART_CTRL_REG          ",             FPGA_S7_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S8_UART_RXDATA_REG        ",             FPGA_S8_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_UART_TXDATA_REG        ",             FPGA_S8_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_UART_STAT_REG          ",             FPGA_S8_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S8_UART_CTRL_REG          ",             FPGA_S8_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S9_UART_RXDATA_REG        ",             FPGA_S9_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_UART_TXDATA_REG        ",             FPGA_S9_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_UART_STAT_REG          ",             FPGA_S9_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S9_UART_CTRL_REG          ",             FPGA_S9_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_DBG_UART_RXDATA_REG       ",             FPGA_DBG_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_UART_TXDATA_REG       ",             FPGA_DBG_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_UART_STAT_REG         ",             FPGA_DBG_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_DBG_UART_CTRL_REG         ",             FPGA_DBG_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S0_UC_UART_CTRL_REG       ",             FPGA_S0_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S0_UC_UART_RXDATA_REG     ",             FPGA_S0_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_UC_UART_TXDATA_REG     ",             FPGA_S0_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S0_UC_UART_STAT_REG       ",             FPGA_S0_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_UC_UART_RXDATA_REG     ",             FPGA_S1_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_UC_UART_TXDATA_REG     ",             FPGA_S1_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_UC_UART_STAT_REG       ",             FPGA_S1_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_UC_UART_CTRL_REG       ",             FPGA_S1_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S2_UC_UART_RXDATA_REG     ",             FPGA_S2_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_UC_UART_TXDATA_REG     ",             FPGA_S2_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_UC_UART_STAT_REG       ",             FPGA_S2_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S2_UC_UART_CTRL_REG       ",             FPGA_S2_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S3_UC_UART_RXDATA_REG     ",             FPGA_S3_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_UC_UART_TXDATA_REG     ",             FPGA_S3_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_UC_UART_STAT_REG       ",             FPGA_S3_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S3_UC_UART_CTRL_REG       ",             FPGA_S3_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S4_UC_UART_RXDATA_REG     ",             FPGA_S4_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_UC_UART_TXDATA_REG     ",             FPGA_S4_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_UC_UART_STAT_REG       ",             FPGA_S4_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S4_UC_UART_CTRL_REG       ",             FPGA_S4_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S5_UC_UART_RXDATA_REG     ",             FPGA_S5_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_UC_UART_TXDATA_REG     ",             FPGA_S5_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_UC_UART_STAT_REG       ",             FPGA_S5_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S5_UC_UART_CTRL_REG       ",             FPGA_S5_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S6_UC_UART_RXDATA_REG     ",             FPGA_S6_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_UC_UART_TXDATA_REG     ",             FPGA_S6_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_UC_UART_STAT_REG       ",             FPGA_S6_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S6_UC_UART_CTRL_REG       ",             FPGA_S6_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S7_UC_UART_RXDATA_REG     ",             FPGA_S7_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_UC_UART_TXDATA_REG     ",             FPGA_S7_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_UC_UART_STAT_REG       ",             FPGA_S7_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S7_UC_UART_CTRL_REG       ",             FPGA_S7_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S8_UC_UART_RXDATA_REG     ",             FPGA_S8_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_UC_UART_TXDATA_REG     ",             FPGA_S8_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_UC_UART_STAT_REG       ",             FPGA_S8_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S8_UC_UART_CTRL_REG       ",             FPGA_S8_UC_UART_CTRL_REG},
    FPGA_REGISTERS{"FGPA_S9_UC_UART_RXDATA_REG     ",             FPGA_S9_UC_UART_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_UC_UART_TXDATA_REG     ",             FPGA_S9_UC_UART_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_UC_UART_STAT_REG       ",             FPGA_S9_UC_UART_STAT_REG},
    FPGA_REGISTERS{"FGPA_S9_UC_UART_CTRL_REG       ",             FPGA_S9_UC_UART_CTRL_REG},
}
