#ifndef __FPGA_UART_DEVICE_H__
#define __FPGA_UART_DEVICE_H__

#define BIT00                 (0x1 << 0)
#define BIT01                 (0x1 << 1)
#define BIT02                 (0x1 << 2)
#define BIT03                 (0x1 << 3)
#define BIT04                 (0x1 << 4)
#define BIT05                 (0x1 << 5)
#define BIT06                 (0x1 << 6)
#define BIT07                 (0x1 << 7)

#define FPGA_UART0_OFFSET     0x10000
#define FPGA_UART1_OFFSET     0x10B00
#define FPGA_UART_INST_SIZE   0x0100
#define UART_RXDATA_REG       0x0000
#define UART_TXDATA_REG       0x0004
#define UART_STAT_REG         0x0008
#define UART_CTRL_REG         0x000C

#define UART_PARITY_ERR_BIT   (BIT07)
#define UART_FRAME_ERR_BIT    (BIT06)
#define UART_OVER_RUN_BIT     (BIT05)
#define UART_TXFIFO_FULL_BIT  (BIT03)
#define UART_RXFIFO_FULL_BIT  (BIT01)
#define UART_RXDATA_READY_BIT (BIT00)

#define UART_RX_VALID_FLAG       \
    (UART_PARITY_ERR_BIT   |     \
     UART_FRAME_ERR_BIT    |     \
     UART_OVER_RUN_BIT     |     \
     UART_TXFIFO_FULL_BIT  |     \
     UART_RXFIFO_FULL_BIT  |     \
     UART_RXDATA_READY_BIT)

#define UART_RESET_TXFIFO_BIT (BIT00)
#define UART_RESET_RXFIFO_BIT (BIT01)

#endif
