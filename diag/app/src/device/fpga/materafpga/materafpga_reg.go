package materafpga


/*
 * Registers offset
 */


type FPGA_REGISTERS struct {
    Name     string
    Address  uint64
}

const L_I2C_MAILBOX_STRIDE = 0x20


//Convert registger and address from excel spreadsheet.  Save 2 columns to reg1.txt and run commands below
//awk '{print "FPGA_" $0}' reg1.txt > reg1_.txt
//awk '{ printf "const %-28s uint64 = 0x%s\n", $1, $2 }' ./reg1_.txt > reg2_.txt
//awk '{ printf "    FPGA_REGISTERS{\"FGPA_%-26s\",             FPGA_%s},\n", $1, $1 }' ./reg1.txt > reg3_.txt


const FPGA_FPGA_REV_ID_REG         uint64 = 0x0
const FPGA_FPGA_DATECODE_REG       uint64 = 0x4
const FPGA_FPGA_TIMECODE_REG       uint64 = 0x8
const FPGA_FPGA_BOARD_REV_ID_REG   uint64 = 0xC
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
const FPGA_FAN_PWR_CTRL_REG        uint64 = 0x150
const FPGA_FAN_PWM_CTRL0_REG       uint64 = 0x154
const FPGA_FAN_PWM_CTRL1_REG       uint64 = 0x158
const FPGA_FAN_STAT_REG            uint64 = 0x15C
const FPGA_FAN0_TACH_REG           uint64 = 0x160
const FPGA_FAN1_TACH_REG           uint64 = 0x164
const FPGA_FAN2_TACH_REG           uint64 = 0x168
const FPGA_FAN3_TACH_REG           uint64 = 0x16C
const FPGA_FAN4_TACH_REG           uint64 = 0x170
const FPGA_P12_CONTROL_REG         uint64 = 0x174
const FPGA_P03_CONTROL_REG         uint64 = 0x178
const FPGA_RESET_CONTROL_REG       uint64 = 0x17C
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
const FPGA_S0_I2C_RX_REG           uint64 = 0x410
const FPGA_S0_I2C_CMD_REG          uint64 = 0x414
const FPGA_S0_I2C_STAT_REG         uint64 = 0x418
const FPGA_S0_I2C_MUX_SEL_REG      uint64 = 0x41C
const FPGA_S0_I2C_RST_REG          uint64 = 0x420
const FPGA_S0_I2C_SEM_REG          uint64 = 0x424
const FPGA_S1_I2C_PRSCL_LO_REG     uint64 = 0x428
const FPGA_S1_I2C_PRSCL_HI_REG     uint64 = 0x42C
const FPGA_S1_I2C_CTRL_REG         uint64 = 0x430
const FPGA_S1_I2C_TX_REG           uint64 = 0x434
const FPGA_S1_I2C_RX_REG           uint64 = 0x438
const FPGA_S1_I2C_CMD_REG          uint64 = 0x43C
const FPGA_S1_I2C_STAT_REG         uint64 = 0x440
const FPGA_S1_I2C_MUX_SEL_REG      uint64 = 0x444
const FPGA_S1_I2C_RST_REG          uint64 = 0x448
const FPGA_S1_I2C_SEM_REG          uint64 = 0x44C
const FPGA_S2_I2C_PRSCL_LO_REG     uint64 = 0x450
const FPGA_S2_I2C_PRSCL_HI_REG     uint64 = 0x454
const FPGA_S2_I2C_CTRL_REG         uint64 = 0x458
const FPGA_S2_I2C_TX_REG           uint64 = 0x45C
const FPGA_S2_I2C_RX_REG           uint64 = 0x460
const FPGA_S2_I2C_CMD_REG          uint64 = 0x464
const FPGA_S2_I2C_STAT_REG         uint64 = 0x468
const FPGA_S2_I2C_MUX_SEL_REG      uint64 = 0x46C
const FPGA_S2_I2C_RST_REG          uint64 = 0x470
const FPGA_S2_I2C_SEM_REG          uint64 = 0x474
const FPGA_S3_I2C_PRSCL_LO_REG     uint64 = 0x478
const FPGA_S3_I2C_PRSCL_HI_REG     uint64 = 0x47C
const FPGA_S3_I2C_CTRL_REG         uint64 = 0x480
const FPGA_S3_I2C_TX_REG           uint64 = 0x484
const FPGA_S3_I2C_RX_REG           uint64 = 0x488
const FPGA_S3_I2C_CMD_REG          uint64 = 0x48C
const FPGA_S3_I2C_STAT_REG         uint64 = 0x490
const FPGA_S3_I2C_MUX_SEL_REG      uint64 = 0x494
const FPGA_S3_I2C_RST_REG          uint64 = 0x498
const FPGA_S3_I2C_SEM_REG          uint64 = 0x49C
const FPGA_S4_I2C_PRSCL_LO_REG     uint64 = 0x4A0
const FPGA_S4_I2C_PRSCL_HI_REG     uint64 = 0x4A4
const FPGA_S4_I2C_CTRL_REG         uint64 = 0x4A8
const FPGA_S4_I2C_TX_REG           uint64 = 0x4AC
const FPGA_S4_I2C_RX_REG           uint64 = 0x4B0
const FPGA_S4_I2C_CMD_REG          uint64 = 0x4B4
const FPGA_S4_I2C_STAT_REG         uint64 = 0x4B8
const FPGA_S4_I2C_MUX_SEL_REG      uint64 = 0x4BC
const FPGA_S4_I2C_RST_REG          uint64 = 0x4C0
const FPGA_S4_I2C_SEM_REG          uint64 = 0x4C4
const FPGA_S5_I2C_PRSCL_LO_REG     uint64 = 0x4C8
const FPGA_S5_I2C_PRSCL_HI_REG     uint64 = 0x4CC
const FPGA_S5_I2C_CTRL_REG         uint64 = 0x4D0
const FPGA_S5_I2C_TX_REG           uint64 = 0x4D4
const FPGA_S5_I2C_RX_REG           uint64 = 0x4D8
const FPGA_S5_I2C_CMD_REG          uint64 = 0x4DC
const FPGA_S5_I2C_STAT_REG         uint64 = 0x4E0
const FPGA_S5_I2C_MUX_SEL_REG      uint64 = 0x4E4
const FPGA_S5_I2C_RST_REG          uint64 = 0x4E8
const FPGA_S5_I2C_SEM_REG          uint64 = 0x4EC
const FPGA_S6_I2C_PRSCL_LO_REG     uint64 = 0x4F0
const FPGA_S6_I2C_PRSCL_HI_REG     uint64 = 0x4F4
const FPGA_S6_I2C_CTRL_REG         uint64 = 0x4F8
const FPGA_S6_I2C_TX_REG           uint64 = 0x4FC
const FPGA_S6_I2C_RX_REG           uint64 = 0x500
const FPGA_S6_I2C_CMD_REG          uint64 = 0x504
const FPGA_S6_I2C_STAT_REG         uint64 = 0x508
const FPGA_S6_I2C_MUX_SEL_REG      uint64 = 0x50C
const FPGA_S6_I2C_RST_REG          uint64 = 0x510
const FPGA_S6_I2C_SEM_REG          uint64 = 0x514
const FPGA_S7_I2C_PRSCL_LO_REG     uint64 = 0x518
const FPGA_S7_I2C_PRSCL_HI_REG     uint64 = 0x51C
const FPGA_S7_I2C_CTRL_REG         uint64 = 0x520
const FPGA_S7_I2C_TX_REG           uint64 = 0x524
const FPGA_S7_I2C_RX_REG           uint64 = 0x528
const FPGA_S7_I2C_CMD_REG          uint64 = 0x52C
const FPGA_S7_I2C_STAT_REG         uint64 = 0x530
const FPGA_S7_I2C_MUX_SEL_REG      uint64 = 0x534
const FPGA_S7_I2C_RST_REG          uint64 = 0x538
const FPGA_S7_I2C_SEM_REG          uint64 = 0x53C
const FPGA_S8_I2C_PRSCL_LO_REG     uint64 = 0x540
const FPGA_S8_I2C_PRSCL_HI_REG     uint64 = 0x544
const FPGA_S8_I2C_CTRL_REG         uint64 = 0x548
const FPGA_S8_I2C_TX_REG           uint64 = 0x54C
const FPGA_S8_I2C_RX_REG           uint64 = 0x550
const FPGA_S8_I2C_CMD_REG          uint64 = 0x554
const FPGA_S8_I2C_STAT_REG         uint64 = 0x558
const FPGA_S8_I2C_MUX_SEL_REG      uint64 = 0x55C
const FPGA_S8_I2C_RST_REG          uint64 = 0x560
const FPGA_S8_I2C_SEM_REG          uint64 = 0x564
const FPGA_S9_I2C_PRSCL_LO_REG     uint64 = 0x568
const FPGA_S9_I2C_PRSCL_HI_REG     uint64 = 0x56C
const FPGA_S9_I2C_CTRL_REG         uint64 = 0x570
const FPGA_S9_I2C_TX_REG           uint64 = 0x574
const FPGA_S9_I2C_RX_REG           uint64 = 0x578
const FPGA_S9_I2C_CMD_REG          uint64 = 0x57C
const FPGA_S9_I2C_STAT_REG         uint64 = 0x580
const FPGA_S9_I2C_MUX_SEL_REG      uint64 = 0x584
const FPGA_S9_I2C_RST_REG          uint64 = 0x588
const FPGA_S9_I2C_SEM_REG          uint64 = 0x58C
const FPGA_DBG_I2C_PRSCL_LO_REG    uint64 = 0x600
const FPGA_DBG_I2C_PRSCL_HI_REG    uint64 = 0x604
const FPGA_DBG_I2C_CTRL_REG        uint64 = 0x608
const FPGA_DBG_I2C_TX_REG          uint64 = 0x60C
const FPGA_DBG_I2C_RX_REG          uint64 = 0x610
const FPGA_DBG_I2C_CMD_REG         uint64 = 0x614
const FPGA_DBG_I2C_STAT_REG        uint64 = 0x618
const FPGA_DBG_I2C_MUX_SEL_REG     uint64 = 0x61C
const FPGA_DBG_I2C_RST_REG         uint64 = 0x620
const FPGA_DBG_I2C_SEM_REG         uint64 = 0x624
const FPGA_PSU0_I2C_PRSCL_LO_REG   uint64 = 0x628
const FPGA_PSU0_I2C_PRSCL_HI_REG   uint64 = 0x62C
const FPGA_PSU0_I2C_CTRL_REG       uint64 = 0x630
const FPGA_PSU0_I2C_TX_REG         uint64 = 0x634
const FPGA_PSU0_I2C_RX_REG         uint64 = 0x638
const FPGA_PSU0_I2C_CMD_REG        uint64 = 0x63C
const FPGA_PSU0_I2C_STAT_REG       uint64 = 0x640
const FPGA_PSU0_I2C_MUX_SEL_REG    uint64 = 0x644
const FPGA_PSU0_I2C_RST_REG        uint64 = 0x648
const FPGA_PSU0_I2C_SEM_REG        uint64 = 0x64C
const FPGA_PSU1_I2C_PRSCL_LO_REG   uint64 = 0x650
const FPGA_PSU1_I2C_PRSCL_HI_REG   uint64 = 0x654
const FPGA_PSU1_I2C_CTRL_REG       uint64 = 0x658
const FPGA_PSU1_I2C_TX_REG         uint64 = 0x65C
const FPGA_PSU1_I2C_RX_REG         uint64 = 0x660
const FPGA_PSU1_I2C_CMD_REG        uint64 = 0x664
const FPGA_PSU1_I2C_STAT_REG       uint64 = 0x668
const FPGA_PSU1_I2C_MUX_SEL_REG    uint64 = 0x66C
const FPGA_PSU1_I2C_RST_REG        uint64 = 0x670
const FPGA_PSU1_I2C_SEM_REG        uint64 = 0x674
const FPGA_PMB_I2C_PRSCL_LO_REG    uint64 = 0x678
const FPGA_PMB_I2C_PRSCL_HI_REG    uint64 = 0x67C
const FPGA_PMB_I2C_CTRL_REG        uint64 = 0x680
const FPGA_PMB_I2C_TX_REG          uint64 = 0x684
const FPGA_PMB_I2C_RX_REG          uint64 = 0x688
const FPGA_PMB_I2C_CMD_REG         uint64 = 0x68C
const FPGA_PMB_I2C_STAT_REG        uint64 = 0x690
const FPGA_PMB_I2C_MUX_SEL_REG     uint64 = 0x694
const FPGA_PMB_I2C_RST_REG         uint64 = 0x698
const FPGA_PMB_I2C_SEM_REG         uint64 = 0x69C
const FPGA_IOBR_I2C_PRSCL_LO_REG   uint64 = 0x6A0
const FPGA_IOBR_I2C_PRSCL_HI_REG   uint64 = 0x6A4
const FPGA_IOBR_I2C_CTRL_REG       uint64 = 0x6A8
const FPGA_IOBR_I2C_TX_REG         uint64 = 0x6AC
const FPGA_IOBR_I2C_RX_REG         uint64 = 0x6B0
const FPGA_IOBR_I2C_CMD_REG        uint64 = 0x6B4
const FPGA_IOBR_I2C_STAT_REG       uint64 = 0x6B8
const FPGA_IOBR_I2C_MUX_SEL_REG    uint64 = 0x6BC
const FPGA_IOBR_I2C_RST_REG        uint64 = 0x6C0
const FPGA_IOBR_I2C_SEM_REG        uint64 = 0x6C4
const FPGA_IOBL_I2C_PRSCL_LO_REG   uint64 = 0x6C8
const FPGA_IOBL_I2C_PRSCL_HI_REG   uint64 = 0x6CC
const FPGA_IOBL_I2C_CTRL_REG       uint64 = 0x6D0
const FPGA_IOBL_I2C_TX_REG         uint64 = 0x6D4
const FPGA_IOBL_I2C_RX_REG         uint64 = 0x6D8
const FPGA_IOBL_I2C_CMD_REG        uint64 = 0x6DC
const FPGA_IOBL_I2C_STAT_REG       uint64 = 0x6E0
const FPGA_IOBL_I2C_MUX_SEL_REG    uint64 = 0x6E4
const FPGA_IOBL_I2C_RST_REG        uint64 = 0x6E8
const FPGA_IOBL_I2C_SEM_REG        uint64 = 0x6EC
const FPGA_FPIC_I2C_PRSCL_LO_REG   uint64 = 0x6F0
const FPGA_FPIC_I2C_PRSCL_HI_REG   uint64 = 0x6F4
const FPGA_FPIC_I2C_CTRL_REG       uint64 = 0x6F8
const FPGA_FPIC_I2C_TX_REG         uint64 = 0x6FC
const FPGA_FPIC_I2C_RX_REG         uint64 = 0x700
const FPGA_FPIC_I2C_CMD_REG        uint64 = 0x704
const FPGA_FPIC_I2C_STAT_REG       uint64 = 0x708
const FPGA_FPIC_I2C_MUX_SEL_REG    uint64 = 0x70C
const FPGA_FPIC_I2C_RST_REG        uint64 = 0x710
const FPGA_FPIC_I2C_SEM_REG        uint64 = 0x714
const FPGA_ID_I2C_PRSCL_LO_REG     uint64 = 0x718
const FPGA_ID_I2C_PRSCL_HI_REG     uint64 = 0x71C
const FPGA_ID_I2C_CTRL_REG         uint64 = 0x720
const FPGA_ID_I2C_TX_REG           uint64 = 0x724
const FPGA_ID_I2C_RX_REG           uint64 = 0x728
const FPGA_ID_I2C_CMD_REG          uint64 = 0x72C
const FPGA_ID_I2C_STAT_REG         uint64 = 0x730
const FPGA_ID_I2C_MUX_SEL_REG      uint64 = 0x734
const FPGA_ID_I2C_RST_REG          uint64 = 0x738
const FPGA_ID_I2C_SEM_REG          uint64 = 0x73C
const FPGA_MCIO_I2C_PRSCL_LO_REG   uint64 = 0x740
const FPGA_MCIO_I2C_PRSCL_HI_REG   uint64 = 0x744
const FPGA_MCIO_I2C_CTRL_REG       uint64 = 0x748
const FPGA_MCIO_I2C_TX_REG         uint64 = 0x74C
const FPGA_MCIO_I2C_RX_REG         uint64 = 0x750
const FPGA_MCIO_I2C_CMD_REG        uint64 = 0x754
const FPGA_MCIO_I2C_STAT_REG       uint64 = 0x758
const FPGA_MCIO_I2C_MUX_SEL_REG    uint64 = 0x75C
const FPGA_MCIO_I2C_RST_REG        uint64 = 0x760
const FPGA_MCIO_I2C_SEM_REG        uint64 = 0x764
const FPGA_S0_J2C_CMD_REG          uint64 = 0xA00
const FPGA_S0_J2C_STAT_REG         uint64 = 0xA04
const FPGA_S0_J2C_ADDR0_REG        uint64 = 0xA08
const FPGA_S0_J2C_ADDR1_REG        uint64 = 0xA0C
const FPGA_S0_J2C_TXDATA_REG       uint64 = 0xA10
const FPGA_S0_J2C_RXDATA_REG       uint64 = 0xA14
const FPGA_S0_J2C_SEM_REG          uint64 = 0xA18
const FPGA_S0_J2C_MAGIC_REG        uint64 = 0xA1C
const FPGA_S1_J2C_CMD_REG          uint64 = 0xA20
const FPGA_S1_J2C_STAT_REG         uint64 = 0xA24
const FPGA_S1_J2C_ADDR0_REG        uint64 = 0xA28
const FPGA_S1_J2C_ADDR1_REG        uint64 = 0xA2C
const FPGA_S1_J2C_TXDATA_REG       uint64 = 0xA30
const FPGA_S1_J2C_RXDATA_REG       uint64 = 0xA34
const FPGA_S1_J2C_SEM_REG          uint64 = 0xA38
const FPGA_S1_J2C_MAGIC_REG        uint64 = 0xA3C
const FPGA_S2_J2C_CMD_REG          uint64 = 0xA40
const FPGA_S2_J2C_STAT_REG         uint64 = 0xA44
const FPGA_S2_J2C_ADDR0_REG        uint64 = 0xA48
const FPGA_S2_J2C_ADDR1_REG        uint64 = 0xA4C
const FPGA_S2_J2C_TXDATA_REG       uint64 = 0xA50
const FPGA_S2_J2C_RXDATA_REG       uint64 = 0xA54
const FPGA_S2_J2C_SEM_REG          uint64 = 0xA58
const FPGA_S2_J2C_MAGIC_REG        uint64 = 0xA5C
const FPGA_S3_J2C_CMD_REG          uint64 = 0xA60
const FPGA_S3_J2C_STAT_REG         uint64 = 0xA64
const FPGA_S3_J2C_ADDR0_REG        uint64 = 0xA68
const FPGA_S3_J2C_ADDR1_REG        uint64 = 0xA6C
const FPGA_S3_J2C_TXDATA_REG       uint64 = 0xA70
const FPGA_S3_J2C_RXDATA_REG       uint64 = 0xA74
const FPGA_S3_J2C_SEM_REG          uint64 = 0xA78
const FPGA_S3_J2C_MAGIC_REG        uint64 = 0xA7C
const FPGA_S4_J2C_CMD_REG          uint64 = 0xA80
const FPGA_S4_J2C_STAT_REG         uint64 = 0xA84
const FPGA_S4_J2C_ADDR0_REG        uint64 = 0xA88
const FPGA_S4_J2C_ADDR1_REG        uint64 = 0xA8C
const FPGA_S4_J2C_TXDATA_REG       uint64 = 0xA90
const FPGA_S4_J2C_RXDATA_REG       uint64 = 0xA94
const FPGA_S4_J2C_SEM_REG          uint64 = 0xA98
const FPGA_S4_J2C_MAGIC_REG        uint64 = 0xA9C
const FPGA_S5_J2C_CMD_REG          uint64 = 0xAA0
const FPGA_S5_J2C_STAT_REG         uint64 = 0xAA4
const FPGA_S5_J2C_ADDR0_REG        uint64 = 0xAA8
const FPGA_S5_J2C_ADDR1_REG        uint64 = 0xAAC
const FPGA_S5_J2C_TXDATA_REG       uint64 = 0xAB0
const FPGA_S5_J2C_RXDATA_REG       uint64 = 0xAB4
const FPGA_S5_J2C_SEM_REG          uint64 = 0xAB8
const FPGA_S5_J2C_MAGIC_REG        uint64 = 0xABC
const FPGA_S6_J2C_CMD_REG          uint64 = 0xAC0
const FPGA_S6_J2C_STAT_REG         uint64 = 0xAC4
const FPGA_S6_J2C_ADDR0_REG        uint64 = 0xAC8
const FPGA_S6_J2C_ADDR1_REG        uint64 = 0xACC
const FPGA_S6_J2C_TXDATA_REG       uint64 = 0xAD0
const FPGA_S6_J2C_RXDATA_REG       uint64 = 0xAD4
const FPGA_S6_J2C_SEM_REG          uint64 = 0xAD8
const FPGA_S6_J2C_MAGIC_REG        uint64 = 0xADC
const FPGA_S7_J2C_CMD_REG          uint64 = 0xAE0
const FPGA_S7_J2C_STAT_REG         uint64 = 0xAE4
const FPGA_S7_J2C_ADDR0_REG        uint64 = 0xAE8
const FPGA_S7_J2C_ADDR1_REG        uint64 = 0xAEC
const FPGA_S7_J2C_TXDATA_REG       uint64 = 0xAF0
const FPGA_S7_J2C_RXDATA_REG       uint64 = 0xAF4
const FPGA_S7_J2C_SEM_REG          uint64 = 0xAF8
const FPGA_S7_J2C_MAGIC_REG        uint64 = 0xAFC
const FPGA_S8_J2C_CMD_REG          uint64 = 0xB00
const FPGA_S8_J2C_STAT_REG         uint64 = 0xB04
const FPGA_S8_J2C_ADDR0_REG        uint64 = 0xB08
const FPGA_S8_J2C_ADDR1_REG        uint64 = 0xB0C
const FPGA_S8_J2C_TXDATA_REG       uint64 = 0xB10
const FPGA_S8_J2C_RXDATA_REG       uint64 = 0xB14
const FPGA_S8_J2C_SEM_REG          uint64 = 0xB18
const FPGA_S8_J2C_MAGIC_REG        uint64 = 0xB1C
const FPGA_S9_J2C_CMD_REG          uint64 = 0xB20
const FPGA_S9_J2C_STAT_REG         uint64 = 0xB24
const FPGA_S9_J2C_ADDR0_REG        uint64 = 0xB28
const FPGA_S9_J2C_ADDR1_REG        uint64 = 0xB2C
const FPGA_S9_J2C_TXDATA_REG       uint64 = 0xB30
const FPGA_S9_J2C_RXDATA_REG       uint64 = 0xB34
const FPGA_S9_J2C_SEM_REG          uint64 = 0xB38
const FPGA_S9_J2C_MAGIC_REG        uint64 = 0xB3C
const FPGA_DBG_J2C_CMD_REG         uint64 = 0xB40
const FPGA_DBG_J2C_STAT_REG        uint64 = 0xB44
const FPGA_DBG_J2C_ADDR0_REG       uint64 = 0xB48
const FPGA_DBG_J2C_ADDR1_REG       uint64 = 0xB4C
const FPGA_DBG_J2C_TXDATA_REG      uint64 = 0xB50
const FPGA_DBG_J2C_RXDATA_REG      uint64 = 0xB54
const FPGA_DBG_J2C_SEM_REG         uint64 = 0xB58
const FPGA_DBG_J2C_MAGIC_REG       uint64 = 0xB5C
const FPGA_S0_SPI_RXDATA_REG       uint64 = 0xC00
const FPGA_S0_SPI_TXDATA4B_REG     uint64 = 0xC04
const FPGA_S0_SPI_TXDATA2B_REG     uint64 = 0xC08
const FPGA_S0_SPI_TXDATA1B_REG     uint64 = 0xC0C
const FPGA_S0_SPI_STATUS_REG       uint64 = 0xC10
const FPGA_S0_SPI_CONTROL_REG      uint64 = 0xC14
const FPGA_S0_SPI_SEM_REG          uint64 = 0xC18
const FPGA_S0_SPI_SLAVESEL_REG     uint64 = 0xC1C
const FPGA_S0_SPI_EOP_VALUE_REG    uint64 = 0xC20
const FPGA_S0_SPI_MUXSEL_REG       uint64 = 0xC24
const FPGA_S1_SPI_RXDATA_REG       uint64 = 0xC28
const FPGA_S1_SPI_TXDATA4B_REG     uint64 = 0xC2C
const FPGA_S1_SPI_TXDATA2B_REG     uint64 = 0xC30
const FPGA_S1_SPI_TXDATA1B_REG     uint64 = 0xC34
const FPGA_S1_SPI_STATUS_REG       uint64 = 0xC38
const FPGA_S1_SPI_CONTROL_REG      uint64 = 0xC3C
const FPGA_S1_SPI_SEM_REG          uint64 = 0xC40
const FPGA_S1_SPI_SLAVESEL_REG     uint64 = 0xC44
const FPGA_S1_SPI_EOP_VALUE_REG    uint64 = 0xC48
const FPGA_S1_SPI_MUXSEL_REG       uint64 = 0xC4C
const FPGA_S2_SPI_RXDATA_REG       uint64 = 0xC50
const FPGA_S2_SPI_TXDATA4B_REG     uint64 = 0xC54
const FPGA_S2_SPI_TXDATA2B_REG     uint64 = 0xC58
const FPGA_S2_SPI_TXDATA1B_REG     uint64 = 0xC5C
const FPGA_S2_SPI_STATUS_REG       uint64 = 0xC60
const FPGA_S2_SPI_CONTROL_REG      uint64 = 0xC64
const FPGA_S2_SPI_SEM_REG          uint64 = 0xC68
const FPGA_S2_SPI_SLAVESEL_REG     uint64 = 0xC6C
const FPGA_S2_SPI_EOP_VALUE_REG    uint64 = 0xC70
const FPGA_S2_SPI_MUXSEL_REG       uint64 = 0xC74
const FPGA_S3_SPI_RXDATA_REG       uint64 = 0xC78
const FPGA_S3_SPI_TXDATA4B_REG     uint64 = 0xC7C
const FPGA_S3_SPI_TXDATA2B_REG     uint64 = 0xC80
const FPGA_S3_SPI_TXDATA1B_REG     uint64 = 0xC84
const FPGA_S3_SPI_STATUS_REG       uint64 = 0xC88
const FPGA_S3_SPI_CONTROL_REG      uint64 = 0xC8C
const FPGA_S3_SPI_SEM_REG          uint64 = 0xC90
const FPGA_S3_SPI_SLAVESEL_REG     uint64 = 0xC94
const FPGA_S3_SPI_EOP_VALUE_REG    uint64 = 0xC98
const FPGA_S3_SPI_MUXSEL_REG       uint64 = 0xC9C
const FPGA_S4_SPI_RXDATA_REG       uint64 = 0xCA0
const FPGA_S4_SPI_TXDATA4B_REG     uint64 = 0xCA4
const FPGA_S4_SPI_TXDATA2B_REG     uint64 = 0xCA8
const FPGA_S4_SPI_TXDATA1B_REG     uint64 = 0xCAC
const FPGA_S4_SPI_STATUS_REG       uint64 = 0xCB0
const FPGA_S4_SPI_CONTROL_REG      uint64 = 0xCB4
const FPGA_S4_SPI_SEM_REG          uint64 = 0xCB8
const FPGA_S4_SPI_SLAVESEL_REG     uint64 = 0xCBC
const FPGA_S4_SPI_EOP_VALUE_REG    uint64 = 0xCC0
const FPGA_S4_SPI_MUXSEL_REG       uint64 = 0xCC4
const FPGA_S5_SPI_RXDATA_REG       uint64 = 0xCC8
const FPGA_S5_SPI_TXDATA4B_REG     uint64 = 0xCCC
const FPGA_S5_SPI_TXDATA2B_REG     uint64 = 0xCD0
const FPGA_S5_SPI_TXDATA1B_REG     uint64 = 0xCD4
const FPGA_S5_SPI_STATUS_REG       uint64 = 0xCD8
const FPGA_S5_SPI_CONTROL_REG      uint64 = 0xCDC
const FPGA_S5_SPI_SEM_REG          uint64 = 0xCE0
const FPGA_S5_SPI_SLAVESEL_REG     uint64 = 0xCE4
const FPGA_S5_SPI_EOP_VALUE_REG    uint64 = 0xCE8
const FPGA_S5_SPI_MUXSEL_REG       uint64 = 0xCEC
const FPGA_S6_SPI_RXDATA_REG       uint64 = 0xCF0
const FPGA_S6_SPI_TXDATA4B_REG     uint64 = 0xCF4
const FPGA_S6_SPI_TXDATA2B_REG     uint64 = 0xCF8
const FPGA_S6_SPI_TXDATA1B_REG     uint64 = 0xCFC
const FPGA_S6_SPI_STATUS_REG       uint64 = 0xD00
const FPGA_S6_SPI_CONTROL_REG      uint64 = 0xD04
const FPGA_S6_SPI_SEM_REG          uint64 = 0xD08
const FPGA_S6_SPI_SLAVESEL_REG     uint64 = 0xD0C
const FPGA_S6_SPI_EOP_VALUE_REG    uint64 = 0xD10
const FPGA_S6_SPI_MUXSEL_REG       uint64 = 0xD14
const FPGA_S7_SPI_RXDATA_REG       uint64 = 0xD18
const FPGA_S7_SPI_TXDATA4B_REG     uint64 = 0xD1C
const FPGA_S7_SPI_TXDATA2B_REG     uint64 = 0xD20
const FPGA_S7_SPI_TXDATA1B_REG     uint64 = 0xD24
const FPGA_S7_SPI_STATUS_REG       uint64 = 0xD28
const FPGA_S7_SPI_CONTROL_REG      uint64 = 0xD2C
const FPGA_S7_SPI_SEM_REG          uint64 = 0xD30
const FPGA_S7_SPI_SLAVESEL_REG     uint64 = 0xD34
const FPGA_S7_SPI_EOP_VALUE_REG    uint64 = 0xD38
const FPGA_S7_SPI_MUXSEL_REG       uint64 = 0xD3C
const FPGA_S8_SPI_RXDATA_REG       uint64 = 0xD40
const FPGA_S8_SPI_TXDATA4B_REG     uint64 = 0xD44
const FPGA_S8_SPI_TXDATA2B_REG     uint64 = 0xD48
const FPGA_S8_SPI_TXDATA1B_REG     uint64 = 0xD4C
const FPGA_S8_SPI_STATUS_REG       uint64 = 0xD50
const FPGA_S8_SPI_CONTROL_REG      uint64 = 0xD54
const FPGA_S8_SPI_SEM_REG          uint64 = 0xD58
const FPGA_S8_SPI_SLAVESEL_REG     uint64 = 0xD5C
const FPGA_S8_SPI_EOP_VALUE_REG    uint64 = 0xD60
const FPGA_S8_SPI_MUXSEL_REG       uint64 = 0xD64
const FPGA_S9_SPI_RXDATA_REG       uint64 = 0xD68
const FPGA_S9_SPI_TXDATA4B_REG     uint64 = 0xD6C
const FPGA_S9_SPI_TXDATA2B_REG     uint64 = 0xD70
const FPGA_S9_SPI_TXDATA1B_REG     uint64 = 0xD74
const FPGA_S9_SPI_STATUS_REG       uint64 = 0xD78
const FPGA_S9_SPI_CONTROL_REG      uint64 = 0xD7C
const FPGA_S9_SPI_SEM_REG          uint64 = 0xD80
const FPGA_S9_SPI_SLAVESEL_REG     uint64 = 0xD84
const FPGA_S9_SPI_EOP_VALUE_REG    uint64 = 0xD88
const FPGA_S9_SPI_MUXSEL_REG       uint64 = 0xD8C
const FPGA_DBG_SPI_RXDATA_REG      uint64 = 0xD90
const FPGA_DBG_SPI_TXDATA4B_REG    uint64 = 0xD94
const FPGA_DBG_SPI_TXDATA2B_REG    uint64 = 0xD98
const FPGA_DBG_SPI_TXDATA1B_REG    uint64 = 0xD9C
const FPGA_DBG_SPI_STATUS_REG      uint64 = 0xDA0
const FPGA_DBG_SPI_CONTROL_REG     uint64 = 0xDA4
const FPGA_DBG_SPI_SEM_REG         uint64 = 0xDA8
const FPGA_DBG_SPI_SLAVESEL_REG    uint64 = 0xDAC
const FPGA_DBG_SPI_EOP_VALUE_REG   uint64 = 0xDB0
const FPGA_DBG_SPI_MUXSEL_REG      uint64 = 0xDB4
const FPGA_FPGA_SPI_RXDATA_REG     uint64 = 0xDB8
const FPGA_FPGA_SPI_TXDATA4B_REG   uint64 = 0xDBC
const FPGA_FPGA_SPI_TXDATA2B_REG   uint64 = 0xDC0
const FPGA_FPGA_SPI_TXDATA1B_REG   uint64 = 0xDC4
const FPGA_FPGA_SPI_STATUS_REG     uint64 = 0xDC8
const FPGA_FPGA_SPI_CONTROL_REG    uint64 = 0xDCC
const FPGA_FPGA_SPI_SEM_REG        uint64 = 0xDD0
const FPGA_FPGA_SPI_SLAVESEL_REG   uint64 = 0xDD4
const FPGA_FPGA_SPI_EOP_VALUE_REG  uint64 = 0xDD8
const FPGA_FPGA_SPI_MUXSEL_REG     uint64 = 0xDDC
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



var MATERA_FPGA_REGISTERS = []FPGA_REGISTERS {
    FPGA_REGISTERS{"FGPA_FPGA_REV_ID_REG           ",             FPGA_FPGA_REV_ID_REG},
    FPGA_REGISTERS{"FGPA_FPGA_DATECODE_REG         ",             FPGA_FPGA_DATECODE_REG},
    FPGA_REGISTERS{"FGPA_FPGA_TIMECODE_REG         ",             FPGA_FPGA_TIMECODE_REG},
    FPGA_REGISTERS{"FGPA_FPGA_BOARD_REV_ID_REG     ",             FPGA_FPGA_BOARD_REV_ID_REG},
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
    FPGA_REGISTERS{"FGPA_P12_CONTROL_REG           ",             FPGA_P12_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_P03_CONTROL_REG           ",             FPGA_P03_CONTROL_REG},
    FPGA_REGISTERS{"FGPA_RESET_CONTROL_REG         ",             FPGA_RESET_CONTROL_REG},
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
    FPGA_REGISTERS{"FGPA_S1_J2C_CMD_REG            ",             FPGA_S1_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_STAT_REG           ",             FPGA_S1_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_ADDR0_REG          ",             FPGA_S1_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_ADDR1_REG          ",             FPGA_S1_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_TXDATA_REG         ",             FPGA_S1_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_RXDATA_REG         ",             FPGA_S1_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_SEM_REG            ",             FPGA_S1_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S1_J2C_MAGIC_REG          ",             FPGA_S1_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_CMD_REG            ",             FPGA_S2_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_STAT_REG           ",             FPGA_S2_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_ADDR0_REG          ",             FPGA_S2_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_ADDR1_REG          ",             FPGA_S2_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_TXDATA_REG         ",             FPGA_S2_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_RXDATA_REG         ",             FPGA_S2_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_SEM_REG            ",             FPGA_S2_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S2_J2C_MAGIC_REG          ",             FPGA_S2_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_CMD_REG            ",             FPGA_S3_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_STAT_REG           ",             FPGA_S3_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_ADDR0_REG          ",             FPGA_S3_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_ADDR1_REG          ",             FPGA_S3_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_TXDATA_REG         ",             FPGA_S3_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_RXDATA_REG         ",             FPGA_S3_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_SEM_REG            ",             FPGA_S3_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S3_J2C_MAGIC_REG          ",             FPGA_S3_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_CMD_REG            ",             FPGA_S4_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_STAT_REG           ",             FPGA_S4_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_ADDR0_REG          ",             FPGA_S4_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_ADDR1_REG          ",             FPGA_S4_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_TXDATA_REG         ",             FPGA_S4_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_RXDATA_REG         ",             FPGA_S4_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_SEM_REG            ",             FPGA_S4_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S4_J2C_MAGIC_REG          ",             FPGA_S4_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_CMD_REG            ",             FPGA_S5_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_STAT_REG           ",             FPGA_S5_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_ADDR0_REG          ",             FPGA_S5_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_ADDR1_REG          ",             FPGA_S5_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_TXDATA_REG         ",             FPGA_S5_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_RXDATA_REG         ",             FPGA_S5_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_SEM_REG            ",             FPGA_S5_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S5_J2C_MAGIC_REG          ",             FPGA_S5_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_CMD_REG            ",             FPGA_S6_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_STAT_REG           ",             FPGA_S6_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_ADDR0_REG          ",             FPGA_S6_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_ADDR1_REG          ",             FPGA_S6_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_TXDATA_REG         ",             FPGA_S6_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_RXDATA_REG         ",             FPGA_S6_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_SEM_REG            ",             FPGA_S6_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S6_J2C_MAGIC_REG          ",             FPGA_S6_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_CMD_REG            ",             FPGA_S7_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_STAT_REG           ",             FPGA_S7_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_ADDR0_REG          ",             FPGA_S7_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_ADDR1_REG          ",             FPGA_S7_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_TXDATA_REG         ",             FPGA_S7_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_RXDATA_REG         ",             FPGA_S7_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_SEM_REG            ",             FPGA_S7_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S7_J2C_MAGIC_REG          ",             FPGA_S7_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_CMD_REG            ",             FPGA_S8_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_STAT_REG           ",             FPGA_S8_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_ADDR0_REG          ",             FPGA_S8_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_ADDR1_REG          ",             FPGA_S8_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_TXDATA_REG         ",             FPGA_S8_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_RXDATA_REG         ",             FPGA_S8_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_SEM_REG            ",             FPGA_S8_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S8_J2C_MAGIC_REG          ",             FPGA_S8_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_CMD_REG            ",             FPGA_S9_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_STAT_REG           ",             FPGA_S9_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_ADDR0_REG          ",             FPGA_S9_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_ADDR1_REG          ",             FPGA_S9_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_TXDATA_REG         ",             FPGA_S9_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_RXDATA_REG         ",             FPGA_S9_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_SEM_REG            ",             FPGA_S9_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_S9_J2C_MAGIC_REG          ",             FPGA_S9_J2C_MAGIC_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_CMD_REG           ",             FPGA_DBG_J2C_CMD_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_STAT_REG          ",             FPGA_DBG_J2C_STAT_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_ADDR0_REG         ",             FPGA_DBG_J2C_ADDR0_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_ADDR1_REG         ",             FPGA_DBG_J2C_ADDR1_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_TXDATA_REG        ",             FPGA_DBG_J2C_TXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_RXDATA_REG        ",             FPGA_DBG_J2C_RXDATA_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_SEM_REG           ",             FPGA_DBG_J2C_SEM_REG},
    FPGA_REGISTERS{"FGPA_DBG_J2C_MAGIC_REG         ",             FPGA_DBG_J2C_MAGIC_REG},
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
}

