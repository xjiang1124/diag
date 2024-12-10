// Support for fpga spi to cpld designware i2c code
package materafpga

import (
    //"common/cli"
    //"fmt"
    //"time"
)


type DW_REGISTERS struct {
    Name     string
    Address  uint8
}

const DW_IC_CON_MASTER                uint8 = 0x1
const DW_IC_CON_SPEED_STD             uint8 = 0x2
const DW_IC_CON_SPEED_FAST            uint8 = 0x4
const DW_IC_CON_SPEED_HIGH            uint8 = 0x6
const DW_IC_CON_SPEED_MASK            uint8 = 0x6
const DW_IC_CON_10BITADDR_SLAVE       uint8 = 0x8
const DW_IC_CON_10BITADDR_MASTER      uint8 = 0x10
const DW_IC_CON_RESTART_EN            uint8 = 0x20
const DW_IC_CON_SLAVE_DISABLE         uint8 = 0x40
const DW_IC_CON_STOP_DET_IFADDRESSED  uint8 = 0x80
const DW_IC_CON_TX_EMPTY_CTRL         uint16 = 0x100
const DW_IC_CON_RX_FIFO_FULL_HLD_CTRL uint16 = 0x200
const DW_IC_CON_BUS_CLEAR_FEATURE_CTL uint16 = 0x800

const DW_IC_INTR_RX_UNDER	uint32 = 0x001
const DW_IC_INTR_RX_OVER	uint32 = 0x002
const DW_IC_INTR_RX_FULL	uint32 = 0x004
const DW_IC_INTR_TX_OVER	uint32 = 0x008
const DW_IC_INTR_TX_EMPTY	uint32 = 0x010
const DW_IC_INTR_RD_REQ	        uint32 = 0x020
const DW_IC_INTR_TX_ABRT	uint32 = 0x040
const DW_IC_INTR_RX_DONE	uint32 = 0x080
const DW_IC_INTR_ACTIVITY	uint32 = 0x100
const DW_IC_INTR_STOP_DET	uint32 = 0x200
const DW_IC_INTR_START_DET	uint32 = 0x400
const DW_IC_INTR_GEN_CALL	uint32 = 0x800
const DW_IC_INTR_RESTART_DET	uint32 = 0x1000
const DW_IC_INTR_SCL_STUCK_AT_LOW uint32 = 0x4000

const DW_IC_INTR_DEFAULT_MASK  uint32 = (DW_IC_INTR_RX_FULL | DW_IC_INTR_TX_ABRT | DW_IC_INTR_STOP_DET)
const DW_IC_INTR_MASTER_MASK   uint32 =	(DW_IC_INTR_DEFAULT_MASK | DW_IC_INTR_TX_EMPTY)
const DW_IC_INTR_SLAVE_MASK    uint32 =	(DW_IC_INTR_DEFAULT_MASK | DW_IC_INTR_RX_DONE | DW_IC_INTR_RX_UNDER | DW_IC_INTR_RD_REQ)


/*
 * Registers offset
 */
const DW_IC_CON               uint8 = 0x0
    const IC_CON_MASTER_MODE    uint32 = (0x1 << 0)
    const IC_CON_SPD_STANDARD   uint32 = (0x1 << 1)
    const IC_CON_SPD_FAST       uint32 = (0x2 << 1)
    const IC_CON_SPD_HIGH       uint32 = (0x3 << 1)
    const IC_CON_RESTART_EN     uint32 = (0x1 << 5)
    const IC_CON_SLV_DISABLED   uint32 = (0x1 << 6)
const DW_IC_TAR               uint8 = 0x4
const DW_IC_SAR               uint8 = 0x8
const DW_IC_HS_MADDR          uint8 = 0xC
const DW_IC_DATA_CMD          uint8 = 0x10
const DW_IC_SS_SCL_HCNT       uint8 = 0x14
const DW_IC_SS_SCL_LCNT       uint8 = 0x18
const DW_IC_FS_SCL_HCNT       uint8 = 0x1c
const DW_IC_FS_SCL_LCNT       uint8 = 0x20
const DW_IC_HS_SCL_HCNT       uint8 = 0x24
const DW_IC_HS_SCL_LCNT       uint8 = 0x28
const DW_IC_INTR_STAT         uint8 = 0x2c
const DW_IC_INTR_MASK         uint8 = 0x30
const DW_IC_RAW_INTR_STAT     uint8 = 0x34
const DW_IC_RX_TL             uint8 = 0x38
const DW_IC_TX_TL             uint8 = 0x3c
const DW_IC_CLR_INTR          uint8 = 0x40
const DW_IC_CLR_RX_UNDER      uint8 = 0x44
const DW_IC_CLR_RX_OVER       uint8 = 0x48
const DW_IC_CLR_TX_OVER       uint8 = 0x4c
const DW_IC_CLR_RD_REQ        uint8 = 0x50
const DW_IC_CLR_TX_ABRT       uint8 = 0x54
const DW_IC_CLR_RX_DONE       uint8 = 0x58
const DW_IC_CLR_ACTIVITY      uint8 = 0x5c
const DW_IC_CLR_STOP_DET      uint8 = 0x60
const DW_IC_CLR_START_DET     uint8 = 0x64
const DW_IC_CLR_GEN_CALL      uint8 = 0x68
const DW_IC_ENABLE            uint8 = 0x6c
const DW_IC_STATUS            uint8 = 0x70
const DW_IC_TXFLR             uint8 = 0x74
const DW_IC_RXFLR             uint8 = 0x78
const DW_IC_SDA_HOLD          uint8 = 0x7c
const DW_IC_TX_ABRT_SOURCE    uint8 = 0x80
const DW_IC_SDA_SETUP         uint8 = 0x94
const DW_IC_ACK_GENERAL       uint8 = 0x98
const DW_IC_ENABLE_STATUS     uint8 = 0x9c
const DW_IC_FS_SPKLEN         uint8 = 0xa0
const DW_IC_UFM_SPKLEN        uint8 = 0xa4
const DW_IC_CLR_RESTART_DET   uint8 = 0xa8
const DW_IC_SCL_STUCK_AT_LOW  uint8 = 0xac
const DW_IC_SDA_STUCK_AT_LOW  uint8 = 0xb0
const DW_IC_SDA_STUCK_DETERM  uint8 = 0xb4
const DW_IC_DEVICE_ID         uint8 = 0xb8
const DW_IC_COMP_PARAM_1      uint8 = 0xf4
const DW_IC_COMP_VERSION      uint8 = 0xf8
const DW_IC_SDA_HOLD_MIN_VERS uint32 = 0x3131312A
const DW_IC_COMP_TYPE         uint8 = 0xfc
const DW_IC_COMP_TYPE_VALUE   uint32 = 0x44570140

var DW_ALL_REGISTERS = []DW_REGISTERS {
    DW_REGISTERS{"DW_IC_CON            ", DW_IC_CON },
    DW_REGISTERS{"DW_IC_TAR            ", DW_IC_TAR },
    DW_REGISTERS{"DW_IC_SAR            ", DW_IC_SAR },
    DW_REGISTERS{"DW_IC_HS_MADDR       ", DW_IC_HS_MADDR },
    DW_REGISTERS{"DW_IC_DATA_CMD       ", DW_IC_DATA_CMD },
    DW_REGISTERS{"DW_IC_SS_SCL_HCNT    ", DW_IC_SS_SCL_HCNT },
    DW_REGISTERS{"DW_IC_SS_SCL_LCNT    ", DW_IC_SS_SCL_LCNT },
    DW_REGISTERS{"DW_IC_FS_SCL_HCNT    ", DW_IC_FS_SCL_HCNT },
    DW_REGISTERS{"DW_IC_FS_SCL_LCNT    ", DW_IC_FS_SCL_LCNT },
    DW_REGISTERS{"DW_IC_HS_SCL_HCNT    ", DW_IC_HS_SCL_HCNT },
    DW_REGISTERS{"DW_IC_HS_SCL_LCNT    ", DW_IC_HS_SCL_LCNT },
    DW_REGISTERS{"DW_IC_INTR_STAT      ", DW_IC_INTR_STAT },
    DW_REGISTERS{"DW_IC_INTR_MASK      ", DW_IC_INTR_MASK },
    DW_REGISTERS{"DW_IC_RAW_INTR_STAT  ", DW_IC_RAW_INTR_STAT },
    DW_REGISTERS{"DW_IC_RX_TL          ", DW_IC_RX_TL },
    DW_REGISTERS{"DW_IC_TX_TL          ", DW_IC_TX_TL },
    DW_REGISTERS{"DW_IC_CLR_INTR       ", DW_IC_CLR_INTR },
    DW_REGISTERS{"DW_IC_CLR_RX_UNDER   ", DW_IC_CLR_RX_UNDER },
    DW_REGISTERS{"DW_IC_CLR_RX_OVER    ", DW_IC_CLR_RX_OVER },
    DW_REGISTERS{"DW_IC_CLR_TX_OVER    ", DW_IC_CLR_TX_OVER },
    DW_REGISTERS{"DW_IC_CLR_RD_REQ     ", DW_IC_CLR_RD_REQ },
    DW_REGISTERS{"DW_IC_CLR_TX_ABRT    ", DW_IC_CLR_TX_ABRT },
    DW_REGISTERS{"DW_IC_CLR_RX_DONE    ", DW_IC_CLR_RX_DONE },
    DW_REGISTERS{"DW_IC_CLR_ACTIVITY   ", DW_IC_CLR_ACTIVITY },
    DW_REGISTERS{"DW_IC_CLR_STOP_DET   ", DW_IC_CLR_STOP_DET },
    DW_REGISTERS{"DW_IC_CLR_START_DET  ", DW_IC_CLR_START_DET },
    DW_REGISTERS{"DW_IC_CLR_GEN_CALL   ", DW_IC_CLR_GEN_CALL },
    DW_REGISTERS{"DW_IC_ENABLE         ", DW_IC_ENABLE },
    DW_REGISTERS{"DW_IC_STATUS         ", DW_IC_STATUS },
    DW_REGISTERS{"DW_IC_TXFLR          ", DW_IC_TXFLR },
    DW_REGISTERS{"DW_IC_RXFLR          ", DW_IC_RXFLR },
    DW_REGISTERS{"DW_IC_SDA_HOLD       ", DW_IC_SDA_HOLD },
    DW_REGISTERS{"DW_IC_TX_ABRT_SOURCE ", DW_IC_TX_ABRT_SOURCE },
    DW_REGISTERS{"DW_IC_SDA_SETUP      ", DW_IC_SDA_SETUP },
    DW_REGISTERS{"DW_IC_ACK_GENERAL    ", DW_IC_ACK_GENERAL },
    DW_REGISTERS{"DW_IC_ENABLE_STATUS  ", DW_IC_ENABLE_STATUS },
    DW_REGISTERS{"DW_IC_FS_SPKLEN      ", DW_IC_FS_SPKLEN },
    DW_REGISTERS{"DW_IC_UFM_SPKLEN     ", DW_IC_UFM_SPKLEN },
    DW_REGISTERS{"DW_IC_CLR_RESTART_DET", DW_IC_CLR_RESTART_DET },
    DW_REGISTERS{"DW_IC_SCL_STK_AT_LOW ", DW_IC_SCL_STUCK_AT_LOW },
    DW_REGISTERS{"DW_IC_SDA_STK_AT_LOW ", DW_IC_SDA_STUCK_AT_LOW },
    DW_REGISTERS{"DW_IC_SDA_STK_DETERM ", DW_IC_SDA_STUCK_DETERM},
    DW_REGISTERS{"DW_IC_DEVICE_ID      ", DW_IC_DEVICE_ID },
    DW_REGISTERS{"DW_IC_COMP_PARAM_1   ", DW_IC_COMP_PARAM_1 },
    DW_REGISTERS{"DW_IC_COMP_VERSION   ", DW_IC_COMP_VERSION },
    DW_REGISTERS{"DW_IC_COMP_TYPE      ", DW_IC_COMP_TYPE },
}

