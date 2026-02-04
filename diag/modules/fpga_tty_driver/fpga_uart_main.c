#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/moduleparam.h>
#include <linux/slab.h>
#include <linux/io.h>
#include <linux/uaccess.h>
#include <linux/hrtimer.h>
#include <linux/ktime.h>
#include <linux/timekeeping.h>
#include <linux/tty.h>
#include <linux/tty_driver.h>
#include <linux/tty_flip.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/kthread.h>
#include <linux/delay.h>
#include <linux/mutex.h>
#include <linux/jiffies.h>
#include "fpga_uart_device.h"

#define PANAREA_BOARD_ID (0xd)
#define PONZA_BOARD_ID   (0xe)

#define FPGA_UART_POLL_INTERVAL 10000  // 10 us

// Max UART: Vulsei (6 <slot>) * (1 <SuC> + 6 <Vul>) = 42
#define FPGA_MAX_UART_PORT_NUM  (42)

#define FPGA_UART_RX_BUFFER_SIZE (1024)
#define FPGA_UART_TX_BUFFER_SIZE (1024)

typedef struct _fpga_uart_device_ {
    struct tty_port uart_port;
    struct device *uart_dev;
    unsigned int enabled;
    unsigned int parity_error;
    unsigned int frame_error;
    unsigned int over_run;
    unsigned int txfifo_full;
    unsigned int rxfifo_full;
    unsigned long tx_total_bytes;
    unsigned long rx_total_bytes;
    unsigned long rx_timestamp_us;
    unsigned long tx_timestamp_s;
    unsigned int  violations;
    unsigned int __iomem* uart_rxdata_reg;
    unsigned int __iomem* uart_txdata_reg;
    unsigned int __iomem* uart_status_reg;
    unsigned int __iomem* uart_ctrl_reg;
    struct mutex tx_lock;
    char tx_buf[FPGA_UART_TX_BUFFER_SIZE];
    int tx_write_ptr;
    int tx_read_ptr;
    int tx_full;
    int rx_bytes;
    char rx_buf[FPGA_UART_RX_BUFFER_SIZE];
    int rx_full;
    int flip_full;
    unsigned long last_push_us;
} fpga_uart_device_t;

static fpga_uart_device_t fpga_uart_dev_list[FPGA_MAX_UART_PORT_NUM];

static struct hrtimer fpga_uart_timer;

static struct task_struct *fpga_uart_tx_thread;

static void __iomem *fpga_virt_ptr = NULL;
static unsigned long fpga_phy_address = 0x10020300000UL;
static unsigned long fpga_virt_address = 0x0UL;
static unsigned int fpga_mem_size = 0x100000;
static unsigned int fpga_board_id = 0;

static struct tty_driver *vul_tty_driver;
static struct tty_driver *suc_tty_driver;

static struct proc_dir_entry *fpga_uart_proc_entry;

module_param(fpga_phy_address, ulong, 0444);
MODULE_PARM_DESC(fpga_phy_address, "FPGA bar address");

static int* vul_map_tbl;
static int* suc_map_tbl;
static int fpga_uart_port_num;
static int fpga_suc_uart_num;
static int fpga_vul_uart_num;
// For Panarea: Vul0-9 map to port 0-9; SuC0-9 map to port 10-19
static int panarea_vul_map_tbl[] = { 0,  1,  2,  3,  4,  5,  6,  7,  8,  9};
static int panarea_suc_map_tbl[] = {10, 11, 12, 13, 14, 15, 16, 17, 18, 19};
// For Ponza: SuC0 map to port 0; Vul0-Vul5 map to port 1-6; SuC1 map to port 7; Vul6-11 map to port 8-13...
static int ponza_suc_map_tbl[] = { 0,  7, 14, 21, 28, 35 };
static int ponza_vul_map_tbl[] = { 1,  2,  3,  4,  5,  6,
                                   8,  9, 10, 11, 12, 13,
                                  15, 16, 17, 18, 19, 20,
                                  22, 23, 24, 25, 26, 27,
                                  29, 30, 31, 32, 33, 34,
                                  36, 37, 38, 39, 40, 41 };

static int suc_tty_to_port(int tty_idx)
{
    return suc_map_tbl[tty_idx];
}

static int vul_tty_to_port(int tty_idx)
{
    return vul_map_tbl[tty_idx];
}

static fpga_uart_device_t *port_to_fpga_uart_device(int port)
{
    return &(fpga_uart_dev_list[port]);
}

static int tx_ringbuf_is_empty(fpga_uart_device_t *pdev)
{
    if (pdev->tx_write_ptr == pdev->tx_read_ptr)
        return 1;
    return 0;
}

static int tx_ringbuf_is_full(fpga_uart_device_t *pdev)
{
    if (((pdev->tx_write_ptr + 1) % FPGA_UART_TX_BUFFER_SIZE) == pdev->tx_read_ptr)
        return 1;
    return 0;
}

static size_t tx_ringbuf_get_space(fpga_uart_device_t *pdev)
{
    // space in use: write_ptr - read_ptr, so
    // (FPGA_UART_TX_BUFFER_SIZE - 1) - (write_ptr - read_ptr) availabe
    if (pdev->tx_write_ptr >= pdev->tx_read_ptr)
        return (FPGA_UART_TX_BUFFER_SIZE - 1) - (pdev->tx_write_ptr - pdev->tx_read_ptr);
    // space in use: (FPGA_UART_TX_BUFFER_SIZE - read_ptr) + write_ptr, so
    // (FPGA_UART_TX_BUFFER_SIZE - 1) - [((FPGA_UART_TX_BUFFER_SIZE - read_ptr) + write_ptr] available
    // simplify: read_ptr - write_ptr - 1
    else
        return pdev->tx_read_ptr - pdev->tx_write_ptr - 1;
}

static void tx_ringbuf_enque(fpga_uart_device_t *pdev, char ch)
{
    pdev->tx_buf[pdev->tx_write_ptr] = ch;
    pdev->tx_write_ptr = (pdev->tx_write_ptr + 1) % FPGA_UART_TX_BUFFER_SIZE;
}

static char tx_ringbuf_deque(fpga_uart_device_t *pdev)
{
    char ch = pdev->tx_buf[pdev->tx_read_ptr];
    pdev->tx_read_ptr = (pdev->tx_read_ptr + 1) % FPGA_UART_TX_BUFFER_SIZE;
    return ch;
}

/************************
** /proc entry related.**
************************/
static int fpga_uart_stats_show(struct seq_file *m, void *v)
{
    int tty_idx, port;
    seq_printf(m, "%6s %2s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s %10s %10s %10s %10s\n",
                  "PORT:",
                  "EN",
                  "PARITY",
                  "FRAME",
                  "OVERRUN",
                  "TXFIFO",
                  "RXFIFO",
                  ">1388US",
                  "RX_FULL",
                  "TX_W_PTR",
                  "TX_R_PTR",
                  "TX_FULL",
                  "FLP_FULL",
                  "RX_TIMER",
                  "TX_TIMER",
                  "TX_BYTES",
                  "RX_BYTES");
    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);
        seq_printf(m, "SuC%02d: %2d %8d %8d %8d %8d %8d %8d %8d %8d %8d %8d %8d %10ld %10ld %10ld %10ld\n",
                      tty_idx,
                      pdev->enabled,
                      pdev->parity_error,
                      pdev->frame_error,
                      pdev->over_run,
                      pdev->txfifo_full,
                      pdev->rxfifo_full,
                      pdev->violations,
                      pdev->rx_full,
                      pdev->tx_write_ptr,
                      pdev->tx_read_ptr,
                      pdev->tx_full,
                      pdev->flip_full,
                      pdev->rx_timestamp_us/1000000,
                      pdev->tx_timestamp_s,
                      pdev->tx_total_bytes,
                      pdev->rx_total_bytes);
    }
    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);
        seq_printf(m, "Vul%02d: %2d %8d %8d %8d %8d %8d %8d %8d %8d %8d %8d %8d %10ld %10ld %10ld %10ld\n",
                      tty_idx,
                      pdev->enabled,
                      pdev->parity_error,
                      pdev->frame_error,
                      pdev->over_run,
                      pdev->txfifo_full,
                      pdev->rxfifo_full,
                      pdev->violations,
                      pdev->rx_full,
                      pdev->tx_write_ptr,
                      pdev->tx_read_ptr,
                      pdev->tx_full,
                      pdev->flip_full,
                      pdev->rx_timestamp_us/1000000,
                      pdev->tx_timestamp_s,
                      pdev->tx_total_bytes,
                      pdev->rx_total_bytes);
    }

    return 0;
}

static int fpga_uart_stats_open(struct inode *inode, struct file *file)
{
    return single_open(file, fpga_uart_stats_show, NULL);
}

static const struct proc_ops fpga_uart_stats_fops = {
    .proc_open    = fpga_uart_stats_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/**************************
** TTY interface related.**
**************************/
static int tty_to_uart_port(struct tty_struct *tty)
{
    if (tty->driver == vul_tty_driver)
        return vul_tty_to_port(tty->index);
    else
        return suc_tty_to_port(tty->index);
}

static int fpga_uart_tty_open(struct tty_struct *tty, struct file *filep)
{
    int port = tty_to_uart_port(tty);
    fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);

    // Reset the UART FIFO.
    writel(UART_RESET_TXFIFO_BIT|UART_RESET_RXFIFO_BIT, pdev->uart_ctrl_reg);
    readl(pdev->uart_status_reg);
    pdev->rx_timestamp_us = 0UL;
    pdev->last_push_us = 0UL;
    pdev->rx_bytes = 0;
    pdev->tx_read_ptr = 0;
    pdev->tx_write_ptr = 0;
    smp_wmb();
    pdev->enabled = 1;

    return 0;
}

static void fpga_uart_tty_close(struct tty_struct *tty, struct file *filep)
{
    int port = tty_to_uart_port(tty);
    fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);

    pdev->enabled = 0;
}

static void fpga_uart_tty_set_termios(struct tty_struct *tty, const struct ktermios *old)
{
    return;
}

static unsigned int fpga_uart_tty_write_room(struct tty_struct *tty)
{
    int port = tty_to_uart_port(tty);
    fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);
    unsigned int tx_space;

    mutex_lock(&pdev->tx_lock);
    tx_space = tx_ringbuf_get_space(pdev);
    mutex_unlock(&pdev->tx_lock);

    return tx_space;
}

static ssize_t fpga_uart_tty_write(struct tty_struct *tty, const unsigned char *buf, size_t count)
{
    int port = tty_to_uart_port(tty);
    fpga_uart_device_t *pdev = port_to_fpga_uart_device(port);
    size_t tx_bytes;

    mutex_lock(&pdev->tx_lock);

    tx_bytes = 0;
    while ((tx_bytes < count) && (!tx_ringbuf_is_full(pdev))) {
        tx_ringbuf_enque(pdev, buf[tx_bytes]);
        tx_bytes ++;
    }

    mutex_unlock(&pdev->tx_lock);

    return tx_bytes;
}

static const struct tty_operations fpga_uart_tty_ops = {
    .open  = fpga_uart_tty_open,
    .close = fpga_uart_tty_close,
    .write = fpga_uart_tty_write,
    .write_room = fpga_uart_tty_write_room,
    .set_termios= fpga_uart_tty_set_termios,
};

/***********************************
** kthread to send data to txfifo.**
***********************************/
static int fpga_uart_tx_callback(void *unused)
{
    int port;
    fpga_uart_device_t *pdev;
    unsigned int sts_val;
    unsigned int tx_val;

    while (!kthread_should_stop()) {
        for (port = 0; port < fpga_uart_port_num; port++) {
            pdev = port_to_fpga_uart_device(port);
            if (pdev->enabled == 0)
                continue;

            pdev->tx_timestamp_s = get_jiffies_64() / HZ;
            sts_val = readl(pdev->uart_status_reg);
            // FIFO is full, try again latter.
            if (sts_val & UART_TXFIFO_FULL_BIT) {
                pdev->txfifo_full ++;
                continue;
            }

            mutex_lock(&pdev->tx_lock);

            while ((!tx_ringbuf_is_empty(pdev)) && ((sts_val & UART_TXFIFO_FULL_BIT) == 0)) {
                tx_val = (unsigned int)tx_ringbuf_deque(pdev);
                writel(tx_val, pdev->uart_txdata_reg);
                pdev->tx_total_bytes ++;
                sts_val = readl(pdev->uart_status_reg);
            }

            mutex_unlock(&pdev->tx_lock);
        }
        usleep_range(800, 1000);
    }

    return 0;
}

/********************************
** hrtimer to poll uart rxfifo.**
********************************/
static enum hrtimer_restart fpga_uart_rx_callback(struct hrtimer *t)
{
    int port;
    unsigned long ts, delta_us;
    unsigned int sts_val;
    fpga_uart_device_t *pdev;
    int m=0, n=0, i;

    for (port = 0; port < fpga_uart_port_num; port++) {
        pdev = port_to_fpga_uart_device(port);
        if (pdev->enabled == 0)
            continue;

        ts = ktime_to_us(ktime_get());  // timestamp in us
        if (pdev->rx_timestamp_us != 0UL)
            delta_us = ts - pdev->rx_timestamp_us;
        else
            delta_us = 0UL;
        pdev->rx_timestamp_us = ts;
        // There is 16-bytes fifo in FPGA, assuming speed is 115200 and 8-N-1 format(1 bit start, 8 bit data, 1 bit stop):
        // 1000000/(115200/10)*16 = 1388.888888888889
        // So if delta_us > 1388, there is possibility to lose data.
        if (delta_us > 1388)
            pdev->violations += 1;

        sts_val = readl(pdev->uart_status_reg);
        if (sts_val & UART_PARITY_ERR_BIT)
            pdev->parity_error ++;
        if (sts_val & UART_FRAME_ERR_BIT)
            pdev->frame_error ++;
        if (sts_val & UART_OVER_RUN_BIT)
            pdev->over_run ++;
        if (sts_val & UART_RXFIFO_FULL_BIT)
            pdev->rxfifo_full ++;

        while (sts_val & UART_RXDATA_READY_BIT) {
            // rx buffer is full, could be:
            // 1. uart rx data ready bit is somehow stuck, hw misbehavior.
            // 2. user open the uart port, but don't read, that will cause tty core flip buffer full and backpressure rx buffer.
            if (pdev->rx_bytes >= FPGA_UART_RX_BUFFER_SIZE) {
                pdev->rx_full ++;
                break;
            }
            pdev->rx_buf[pdev->rx_bytes] = (char)readl(pdev->uart_rxdata_reg);
            pdev->rx_bytes ++;
            pdev->rx_total_bytes ++;
            sts_val = readl(pdev->uart_status_reg);
        }

        // Now decide to push rx data to tty core policy:
        // Assuming speed is 115200 and 8-N-1 format(1 bit start, 8 bit data, 1 bit stop):
        // (115200 / 10) * 5 / 1000 = ~58 bytes, so copy 58 bytes at most
        if (pdev->last_push_us == 0UL)
            pdev->last_push_us = ts;
        delta_us = ts - pdev->last_push_us;

        if ((pdev->rx_bytes > 0) && (delta_us > 5000)) {
            n = pdev->rx_bytes;
            m = tty_insert_flip_string(&(pdev->uart_port), pdev->rx_buf, n);
            if (m == 0) {
                // 0 byte copied, which means no space left in tty core, have to wait.
                pdev->flip_full ++;
                continue;
            } else if (m == n) {
                // all bytes copied.
                pdev->rx_bytes = 0;
            } else if (m > 0) {
                // partially copied: [0, ..., m-1, m, ..., n-1, ?, ?], move uncopied bytes to front.
                for (i = 0; i < n - m; i++)
                    pdev->rx_buf[i] = pdev->rx_buf[m+i];
                pdev->rx_bytes = n - m;
            }
            tty_flip_buffer_push(&(pdev->uart_port));
            pdev->last_push_us = ts;
        }
    }

    hrtimer_forward_now(t, ktime_set(0, FPGA_UART_POLL_INTERVAL));
    return HRTIMER_RESTART;
}

static int __init fpga_uart_init(void)
{
    int rc = 0;
    int slot, vul_inst, tty_idx, port;
    int num_slot, vul_per_slot;
    unsigned long uart_base_addr;
    fpga_uart_device_t *pdev;

    fpga_virt_ptr = ioremap(fpga_phy_address, fpga_mem_size);
    if (fpga_virt_ptr == NULL) {
        pr_info("Failed to ioremap fpga io memory.\n");
        return -ENOMEM;
    }

    // TODO: Currently diag use FPGA_REV_ID_REG(offset 0x0) upper 16-bits to decide MTP type
    fpga_board_id = (readl(fpga_virt_ptr) & 0xFFFF0000) >> 16;
    if (fpga_board_id == PANAREA_BOARD_ID) {
        pr_info("Panarea MTP is detected.\n");
        vul_map_tbl = panarea_vul_map_tbl;
        suc_map_tbl = panarea_suc_map_tbl;
        num_slot = 10;
        vul_per_slot = 1;
    } else if (fpga_board_id == PONZA_BOARD_ID) {
        pr_info("Ponza MTP is detected.\n");
        vul_map_tbl = ponza_vul_map_tbl;
        suc_map_tbl = ponza_suc_map_tbl;
        num_slot = 6;
        vul_per_slot = 6;
    } else {
        pr_info("Unknown MTP (ID=0x%x) is detected, check MTP type or pass correct fpga base address.\n", fpga_board_id);
        rc = -ENODEV;
        goto cleanup_ioremap;
    }
    fpga_suc_uart_num = num_slot;
    fpga_vul_uart_num = num_slot * vul_per_slot;
    fpga_uart_port_num = fpga_suc_uart_num + fpga_vul_uart_num;

    fpga_virt_address = (unsigned long)fpga_virt_ptr;
    pr_info("Map FPGA physical address 0x%lx to virtual address 0x%lx(%p)\n", fpga_phy_address, fpga_virt_address, fpga_virt_ptr);

    // SuC <1> tty port per slot
    for (slot = 0; slot < num_slot; slot++) {
        tty_idx = slot;
        port = suc_tty_to_port(tty_idx);
        if (fpga_board_id == PANAREA_BOARD_ID) {
            uart_base_addr = fpga_virt_address + FPGA_UART_OFFSET + 0xB00 + 0x100 * slot;
        } else if (fpga_board_id == PONZA_BOARD_ID) {
            uart_base_addr = fpga_virt_address + FPGA_UART_OFFSET + 0x1000 * slot;
        } else {
            // Should not reach here.
            pr_info("Need to add MTP(ID = 0x%x) support here.\n", fpga_board_id);
            rc = -ENODEV;
            goto cleanup_ioremap;
        }
        fpga_uart_dev_list[port].uart_ctrl_reg = (unsigned int __iomem *)(uart_base_addr + UART_CTRL_REG);
        fpga_uart_dev_list[port].uart_status_reg = (unsigned int __iomem *)(uart_base_addr + UART_STAT_REG);
        fpga_uart_dev_list[port].uart_rxdata_reg = (unsigned int __iomem *)(uart_base_addr + UART_RXDATA_REG);
        fpga_uart_dev_list[port].uart_txdata_reg = (unsigned int __iomem *)(uart_base_addr + UART_TXDATA_REG);
        pr_info("SuC-%02d: (port=%d) Map FPGA registers(base, rxdata, txdata, status, control): 0x%lx, %p, %p, %p, %p\n",
                 tty_idx,
                 port,
                 uart_base_addr,
                 fpga_uart_dev_list[port].uart_rxdata_reg,
                 fpga_uart_dev_list[port].uart_txdata_reg,
                 fpga_uart_dev_list[port].uart_status_reg,
                 fpga_uart_dev_list[port].uart_ctrl_reg
                );
    }

    // Vulcano <vul_per_slot> tty ports per slot
    for (slot = 0; slot < num_slot; slot++) {
        for (vul_inst = 0; vul_inst < vul_per_slot; vul_inst ++) {
            tty_idx = vul_per_slot * slot + vul_inst;
            port = vul_tty_to_port(tty_idx);
            if (fpga_board_id == PANAREA_BOARD_ID) {
                uart_base_addr = fpga_virt_address + FPGA_UART_OFFSET + 0x100 * slot;
            } else if (fpga_board_id == PONZA_BOARD_ID) {
                uart_base_addr = fpga_virt_address + FPGA_UART_OFFSET + 0x1000 * slot + 0x100 + 0x100 * vul_inst;
            } else {
                // Should not reach here.
                pr_info("Need to add MTP(ID = 0x%x) support here.\n", fpga_board_id);
                rc = -ENODEV;
                goto cleanup_ioremap;
            }
            fpga_uart_dev_list[port].uart_ctrl_reg = (unsigned int __iomem *)(uart_base_addr + UART_CTRL_REG);
            fpga_uart_dev_list[port].uart_status_reg = (unsigned int __iomem *)(uart_base_addr + UART_STAT_REG);
            fpga_uart_dev_list[port].uart_rxdata_reg = (unsigned int __iomem *)(uart_base_addr + UART_RXDATA_REG);
            fpga_uart_dev_list[port].uart_txdata_reg = (unsigned int __iomem *)(uart_base_addr + UART_TXDATA_REG);
            pr_info("Vul-%02d: (port=%d) Map FPGA registers(base, rxdata, txdata, status, control): 0x%lx, %p, %p, %p, %p\n",
                     tty_idx,
                     port,
                     uart_base_addr,
                     fpga_uart_dev_list[port].uart_rxdata_reg,
                     fpga_uart_dev_list[port].uart_txdata_reg,
                     fpga_uart_dev_list[port].uart_status_reg,
                     fpga_uart_dev_list[port].uart_ctrl_reg
                    );
        }
    }

    for (port = 0; port < fpga_uart_port_num; port++) {
        pdev = port_to_fpga_uart_device(port);
        mutex_init(&(pdev->tx_lock));
        tty_port_init(&(pdev->uart_port));
    }

    pr_info("FPGA UART ports initialized.\n");

    // Vulcano tty driver
    vul_tty_driver = tty_alloc_driver(fpga_vul_uart_num, TTY_DRIVER_REAL_RAW);
    if (IS_ERR(vul_tty_driver)) {
        rc = PTR_ERR(vul_tty_driver);
        goto cleanup_ioremap;
    }
    vul_tty_driver->driver_name = "fpga_vul_uart";
    vul_tty_driver->name        = "ttyVul";
    vul_tty_driver->major       = 0;  /* dynamic */
    vul_tty_driver->minor_start = 0;
    vul_tty_driver->type        = TTY_DRIVER_TYPE_SERIAL;
    vul_tty_driver->subtype     = SERIAL_TYPE_NORMAL;
    vul_tty_driver->flags       = TTY_DRIVER_REAL_RAW;
    vul_tty_driver->init_termios = tty_std_termios;
    vul_tty_driver->init_termios.c_lflag = 0;
    tty_set_operations(vul_tty_driver, &fpga_uart_tty_ops);
    if (tty_register_driver(vul_tty_driver))
        goto cleanup_ioremap;
    pr_info("Vulcano TTY driver registered.\n");

    // SuC tty driver
    suc_tty_driver = tty_alloc_driver(fpga_suc_uart_num, TTY_DRIVER_REAL_RAW);
    if (IS_ERR(suc_tty_driver)) {
        rc = PTR_ERR(suc_tty_driver);
        goto cleanup_vul_driver;
    }
    suc_tty_driver->driver_name = "fpga_suc_uart";
    suc_tty_driver->name        = "ttySuC";
    suc_tty_driver->major       = 0;  /* dynamic */
    suc_tty_driver->minor_start = 0;
    suc_tty_driver->type        = TTY_DRIVER_TYPE_SERIAL;
    suc_tty_driver->subtype     = SERIAL_TYPE_NORMAL;
    suc_tty_driver->flags       = TTY_DRIVER_REAL_RAW;
    suc_tty_driver->init_termios = tty_std_termios;
    suc_tty_driver->init_termios.c_lflag = 0;
    tty_set_operations(suc_tty_driver, &fpga_uart_tty_ops);
    if (tty_register_driver(suc_tty_driver))
        goto cleanup_vul_driver;
    pr_info("SuC TTY driver registered.\n");

    // Vul tty device
    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_link_device(&(pdev->uart_port), vul_tty_driver, tty_idx);
    }
    pr_info("Vulcano TTY devices registered.\n");

    // SuC tty device
    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_link_device(&(pdev->uart_port), suc_tty_driver, tty_idx);
    }
    pr_info("SuC TTY devices registered.\n");

    // Create proc entry for statistics
    fpga_uart_proc_entry = proc_create("fpga_uart_stats", 0444, NULL, &fpga_uart_stats_fops);
    if (fpga_uart_proc_entry == NULL) {
        rc = -ENOMEM;
        goto cleanup_device;
    }
    pr_info("FPGA UART proc entry is created.\n");

    // Initialize the timer
    hrtimer_setup(&fpga_uart_timer, fpga_uart_rx_callback, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
    hrtimer_start(&fpga_uart_timer, ktime_set(0, FPGA_UART_POLL_INTERVAL), HRTIMER_MODE_REL);

    // Start the kernel thread for tx
    fpga_uart_tx_thread = kthread_run(fpga_uart_tx_callback, NULL, "fpga_uart_tx");

    pr_info("FPGA UART driver loaded\n");
    return 0;

cleanup_device:
    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        if (!IS_ERR(pdev->uart_dev))
            tty_unregister_device(suc_tty_driver, tty_idx);
    }
    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        if (!IS_ERR(pdev->uart_dev))
            tty_unregister_device(vul_tty_driver, tty_idx);
    }
    tty_unregister_driver(suc_tty_driver);
    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_destroy(&(pdev->uart_port));
    }

cleanup_vul_driver:
    tty_unregister_driver(vul_tty_driver);
    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_destroy(&(pdev->uart_port));
    }

cleanup_ioremap:
    if (fpga_virt_ptr != NULL)
        iounmap(fpga_virt_ptr);

    return rc;
}

static void __exit fpga_uart_exit(void)
{
    int tty_idx, port;
    fpga_uart_device_t *pdev;

    kthread_stop(fpga_uart_tx_thread);

    hrtimer_cancel(&fpga_uart_timer);

    proc_remove(fpga_uart_proc_entry);

    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        if (!IS_ERR(pdev->uart_dev))
            tty_unregister_device(suc_tty_driver, tty_idx);
    }

    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        if (!IS_ERR(pdev->uart_dev))
            tty_unregister_device(vul_tty_driver, tty_idx);
    }

    tty_unregister_driver(suc_tty_driver);
    for (tty_idx = 0; tty_idx < fpga_suc_uart_num; tty_idx++) {
        port = suc_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_destroy(&(pdev->uart_port));
    }

    tty_unregister_driver(vul_tty_driver);
    for (tty_idx = 0; tty_idx < fpga_vul_uart_num; tty_idx++) {
        port = vul_tty_to_port(tty_idx);
        pdev = port_to_fpga_uart_device(port);
        tty_port_destroy(&(pdev->uart_port));
    }

    if (fpga_virt_ptr != NULL)
        iounmap(fpga_virt_ptr);

    pr_info("FPGA UART driver unloaded\n");
}

module_init(fpga_uart_init);
module_exit(fpga_uart_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("FPGA UART driver.");
