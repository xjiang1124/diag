#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <ctype.h>

#define DISPLAY_STRING 1

char *strupr(char *str)
{
    char *p = str;
    while ( *p ) {
        *p = toupper(*p);
        p++;
    }
    p = '\0';
    return str;
}

void printhexdata(FILE *fptr, unsigned char *data, int size)
{
    int i;

    fprintf(fptr, "data:");
    for ( i =0; i < size; i++ ) {
        if ( ( i% 16 ) == 0 )
            fprintf(fptr, "\n");
        fprintf(fptr, " 0x%2.2x", *data);
        data++;
    }
    fprintf(fptr, "\n");
    return;
}

int set_interface_attribs(int fd, FILE *fptr, int speed)
{
    struct termios tty;

    if (tcgetattr(fd, &tty) < 0) {
        fprintf(fptr, "Error getting tcgetattr: %s\n", strerror(errno));
        return -1;
    }

    cfsetospeed(&tty, (speed_t)speed);
    cfsetispeed(&tty, (speed_t)speed);

    tty.c_cflag |= (CLOCAL | CREAD);    /* ignore modem controls */
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;         /* 8-bit characters */
    tty.c_cflag &= ~PARENB;     /* no parity bit */
    tty.c_cflag &= ~CSTOPB;     /* only need 1 stop bit */
    tty.c_cflag &= ~CRTSCTS;    /* no hardware flowcontrol */

    /* setup for non-canonical mode */
    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    tty.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    tty.c_oflag &= ~OPOST;

    /* fetch bytes as they become available */
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 1;

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        fprintf(fptr, "Error setting tcsetattr: %s\n", strerror(errno));
        return -1;
    }
    return 0;
}

void set_mincount(int fd, int mcount)
{
    struct termios tty;

    if (tcgetattr(fd, &tty) < 0) {
        printf("Error tcgetattr: %s\n", strerror(errno));
        return;
    }

    tty.c_cc[VMIN] = mcount ? 1 : 0;
    tty.c_cc[VTIME] = 5;        /* half second timer */

    if (tcsetattr(fd, TCSANOW, &tty) < 0)
        printf("Error tcsetattr: %s\n", strerror(errno));
}

unsigned char wr_reg[7] = {0x73, 0x69, 0x00, 0x01, 0x77, 0x61, 0x73};
unsigned char rd_reg[7] = {0x73, 0x69, 0x00, 0x01, 0x72, 0x61, 0x73};
unsigned char wr_dpram[7] = {0x73, 0x6d, 0x00, 0x00, 0x77, 0x61, 0x73};
unsigned char rd_dpram[7] = {0x73, 0x6d, 0x00, 0x00, 0x72, 0x61, 0x73};

void uart_set_dtr(int fd, FILE *fptr, int on)
{
    int status;

    ioctl(fd, TIOCMGET, &status);
    fprintf(fptr, "before dtr state %x %d\n", status, on);
    if ( on == 1 ) {
        status |= TIOCM_DTR;
        ioctl(fd, TIOCMSET, &status);
    } else {                                                      
        status &= ~TIOCM_DTR;
        ioctl(fd, TIOCMSET, &status);
    }
    ioctl(fd, TIOCMGET, &status);
    fprintf(fptr, "after dtr state %x %d\n", status, on);
    return;
}

void uart_set_rts(int fd, FILE *fptr, int on)
{
    int status;

    ioctl(fd, TIOCMGET, &status);
    fprintf(fptr, "before rts state %x %d\n", status, on);
    if ( on == 1 ) {
        status |= TIOCM_RTS;
        ioctl(fd, TIOCMSET, &status);
    } else {
        status &= ~TIOCM_RTS;
        ioctl(fd, TIOCMSET, &status);
    }
    ioctl(fd, TIOCMGET, &status);
    fprintf(fptr, "after rts state %x %d\n", status, on);
    return;
}

int UartWrite(int fd, char *data, int size)
{
    int wlen;

    /* printhexdata(data, size); */
    wlen = write(fd, data, size);
    tcdrain(fd);
    return wlen;
}

int UartRead(int fd, FILE *fptr, char *data, int size)
{
    int rlen, rdlen = 0, len = 0;
    int timeout = 200;
    char *rx_ptr = data;

    rlen = size;
    do {
        rdlen = read(fd, data, rlen);
        if ( rdlen < 0 ) {
            fprintf(fptr, "Error from reading dpram: %d, %d\n", rdlen, errno);
            return len;
        }
        data = data + rdlen;
        len = len + rdlen;
        rlen = rlen - rdlen;
        timeout--;
        rdlen = 0;
    } while ( (rlen > 0) && (timeout > 0) );

    if ( timeout == 0 )
        fprintf(fptr, "UartRead time out\n");
    return len;
}

int UartSpiWrite(int fd, FILE *fptr, char *data, int size)
{
    int wlen;
    int tx_size = size + 8;
    char tx_buf[tx_size];
    char *tx_ptr = tx_buf;

    memcpy(tx_buf, wr_dpram, sizeof(wr_dpram));
    tx_buf[2] = (size & 0xff00) >> 8;
    tx_buf[3] = size & 0xff;
    tx_ptr = tx_ptr + sizeof(wr_dpram);
    memcpy(tx_ptr, data, size);
    tx_ptr = tx_ptr + size;
    *tx_ptr = 0x70;

    wlen = UartWrite(fd, tx_buf, tx_size);

    return (wlen - 8);
}

int UartSpiRead(int fd, FILE *fptr, char *data, int size)
{
    int wlen;
    char tx_buf[sizeof(rd_dpram)];

    memcpy(tx_buf, rd_dpram, sizeof(rd_dpram));
    tx_buf[2] = (size & 0xff00) >> 8;
    tx_buf[3] = size & 0xff;

    wlen = UartWrite(fd, tx_buf, sizeof(rd_dpram));
    if ( wlen != sizeof(rd_dpram) ) {
        printf("Error from sending read cmd: %d, %d\n", wlen, errno);
        return - 1;
    }
    return UartRead(fd, fptr, data, size);
}

int UartRegWrite(int fd, char *data, int size)
{
    int wlen;
    int tx_size = size + 8;
    char tx_buf[tx_size];
    char *tx_ptr = tx_buf;

    memcpy(tx_buf, wr_reg, sizeof(wr_reg));
    tx_buf[2] = (size & 0xff00) >> 8;
    tx_buf[3] = size & 0xff;
    tx_ptr = tx_ptr + sizeof(wr_reg);
    memcpy(tx_ptr, data, size);
    tx_ptr = tx_ptr + size;
    *tx_ptr = 0x70;

    wlen = UartWrite(fd, tx_buf, tx_size);
    return (wlen - 8);
}

int UartRegRead(int fd, FILE *fptr, char *data, int size)
{
    int wlen;
    char tx_buf[sizeof(rd_reg)];

    memcpy(tx_buf, rd_reg, sizeof(rd_reg));
    tx_buf[2] = (size & 0xff00) >> 8;
    tx_buf[3] = size & 0xff;

    wlen = UartWrite(fd, tx_buf, sizeof(rd_reg));
    if ( wlen != sizeof(rd_reg) ) {
        fprintf(fptr, "Error from sending read cmd: %d, %d\n", wlen, errno);
        return - 1;
    }
    return UartRead(fd, fptr, data, size);
}

unsigned char cmdRdId[21] = {0x9f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                                   0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff};

int qspi_read_id(int fd, FILE *fptr, unsigned char *id)
{
    int i, wlen;
    int cmdSize;
    unsigned char *data;

    cmdSize = sizeof(cmdRdId);
    wlen = UartSpiWrite(fd, fptr, cmdRdId, cmdSize);
    if ( wlen != cmdSize ) {
        fprintf(fptr, "Error from write cmdRdId: %d, %d\n", wlen, errno);
        return - 1;
    }

    data = malloc(cmdSize);
    if ( data == NULL ) {
        fprintf(fptr, "failed to allocate %d bytes of memory\n", cmdSize);
    }

    wlen = UartSpiRead(fd, fptr, data, cmdSize);
    if ( wlen != cmdSize ) {
        printf("Error from read data: %d, %d\n", wlen, errno);
        return - 1;
    }

    fprintf(fptr, "QSPI device ID#:\n");
    printhexdata(fptr, data, cmdSize);
    memcpy(id, data, 5);
    return 0;
}

int spi_cpld_id(int fd, FILE *fptr, char *cpld_id)
{
    unsigned char cmd[8] = {0xE0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    unsigned char id[8];
    int wlen, i;

    wlen = UartSpiWrite(fd, fptr, cmd, sizeof(cmd));
    if ( wlen != sizeof(cmd) ) {
        printf("Error writing command: %d, %d\n", wlen, errno);
        return - 1;
    }

    wlen = UartSpiRead(fd, fptr, id, 8);
    if ( wlen != 8 ) {
        printf("Error Reading spi: %d, %d\n", wlen, errno);
        return -1;
    }

    fprintf(fptr, "CPLD device ID:\n");
    printhexdata(fptr, id, 8);
    memcpy(cpld_id, &id[4], 4);

    return 0;
}

char portname[14] = "/dev/ttyUSB0";
char loginprompt[14] = "capri login:";
char card_type[32] = "export CARD_TYPE=VOMERO2\n";
char mnt_command[] = "mount /dev/mmcblk0p10 /data\n";
char sysreset_cmd[] = "sysreset.sh\n";
char sn_command[] = "/data/nic_util/eeutil -disp -field=sn\n";
char fru_json[] = "cat /tmp/fru.json | grep serial-number\n";
char read_cpld_cmd[] = "cpldapp -r ";
char enter_cmd[] = "\r";
char username[] = "root\r";
char password[] = "pen123\r";

int baudrate = 115200;
int res_len = 1024;
char xo3d_id[4] = {0x21, 0x2e, 0x30, 0x43};

int config_serial(int fd, FILE *fptr, int baudrate)
{
    /*baudrate 115200, 8 bits, no parity, 1 stop bit */
    fprintf(fptr, "setting serial port with %d baud rate\n", baudrate);
    switch ( baudrate ) {
        case 115200:
            set_interface_attribs(fd, fptr, B115200);
        break;

        case 230400:
            set_interface_attribs(fd, fptr, B230400);
        break;

        default:
        fprintf(fptr, "invalid baudrate\n");
        return 0;
    break;
    }
    //set_mincount(fd, 0);                /* set to pure timed read */
}

int send_command(int fd, FILE *fptr, char *cmd, char *resp, int resp_len, int timeout)
{
    int cmd_len;
    int rdlen;
    char *pbuf;

    cmd_len = strlen(cmd);
    rdlen = write(fd, cmd, cmd_len);
    if ( rdlen != cmd_len ) {
        fprintf(fptr, "Error writing cmd: %d, %d\n", rdlen, errno);
        return -1;
    }
    tcdrain(fd);    /* delay for output */

    if ( resp == NULL )
        return 0;
    memset(resp, 0, resp_len);
    pbuf = resp;
    do { 
        rdlen = read(fd, pbuf, resp_len);
        resp_len = resp_len - rdlen;
        if ( resp_len > 0 ) {
            pbuf += rdlen;
        } 
        /* repeat read to get full message */
        timeout--; 
    } while ( (resp_len > 0) && (timeout > 0) );

    fprintf(fptr, "%s\n", resp);
    return 0;
}

int connect_nic(int fd, FILE *fptr)
{
    int rc = 0;
    char *res_ptr;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    memset(res_ptr, 0, res_len);
    rc = send_command(fd, fptr, enter_cmd, res_ptr, res_len, 5);
    /*
    send two more carriage return to workaround the issue:
    characters igmored by strstr function if read function return strings which leading character hex value is0x00(NULL).
    in this case, login prompt "elba-gold" will not match
    */
    rc = send_command(fd, fptr, enter_cmd, res_ptr, res_len, 5);
    rc = send_command(fd, fptr, enter_cmd, res_ptr, res_len, 5);
    if ( rc ) {
        fprintf(fptr, "error sending enter command\n");
    free((void *)res_ptr);
    return rc;
    }
    if ( strstr(res_ptr, loginprompt) ) {
        memset(res_ptr, 0, res_len);
        rc = send_command(fd, fptr, username, res_ptr, res_len, 5);
        if ( rc ) {
            fprintf(fptr, "error sending user name\n");
            printf("error sending user name\n");
            free((void *)res_ptr);
            return rc;
        }
        if ( strstr(res_ptr, "assword:") == NULL ) {
            fprintf(fptr, "no password prompt %s\n", res_ptr);
            printf("no password prompt %s\n", res_ptr);
            free((void *)res_ptr);
            return -1;
        }
        memset(res_ptr, 0, res_len);
        rc = send_command(fd, fptr, password, res_ptr, res_len, 5);
        if ( rc ) {
            fprintf(fptr, "error sending password\n");
            printf("error sending password\n");
            free((void *)res_ptr);
            return rc;
        }
        if ( strstr(res_ptr, "#")  == NULL) {
            fprintf(fptr, "failed to get nic prompt %s\n", res_ptr);
            printf("failed to get nic prompt %s\n", res_ptr);
            free((void *)res_ptr);
            return rc;
        }
        fprintf(fptr, "login successful\n"); 
    } else if ( strstr(res_ptr, "elba-gold") || strstr(res_ptr, "salina-gold")) {
        fprintf(fptr, "got goldfw  prompt %s\n", res_ptr);
        printf("got goldfw  prompt %s\n", res_ptr);
        return 0xa;
    } else if ( strstr(res_ptr, "assword:") ) {
        memset(res_ptr, 0, res_len);
        rc = send_command(fd, fptr, password, res_ptr, res_len, 5);
        if ( rc ) {
            fprintf(fptr, "error sending password\n");
            printf("error sending password\n");
            free((void *)res_ptr);
            return rc;
        }
        if ( strstr(res_ptr, "#")  == NULL) {
            fprintf(fptr, "failed to get nic prompt %s\n", res_ptr);
            printf("failed to get nic prompt %s\n", res_ptr);
            free((void *)res_ptr);
            return rc;
        }
        fprintf(fptr, "login successful\n"); 
    } else if ( strstr(res_ptr, "#") ) {
        fprintf(fptr, "login successful\n"); 
    } else {
        fprintf(fptr, "failed to connect %s\n", res_ptr);
        rc = UartRegRead(fd, fptr, res_ptr, 2);
        if ( rc != 2) { 
            uart_set_dtr(fd, fptr, 1);
            sleep(1);
            rc = UartRegRead(fd, fptr, res_ptr, 2);
            if ( rc != 2) { 
                fprintf(fptr, "%s: failed to get uart register value with both dtr value, possible bad cable\n", __func__);
                printf("%s: failed to get uart register value with both dtr value, possible bad cable\n", __func__);
            } else {
                fprintf(fptr, "get data from uart register, possible NIC console is dead: 0x%2.2x 0x%2.2x\n", res_ptr[0], res_ptr[1]);
                printf("get data from uart register, possible NIC console is dead: 0x%2.2x 0x%2.2x\n", res_ptr[0], res_ptr[1]);
            }
        } else {
            fprintf(fptr, "get data from uart register, possible dtr signal is wrong: 0x%2.2x 0x%2.2x\n", res_ptr[0], res_ptr[1]);
            printf("get data from uart register, possible dtr signal is wrong: 0x%2.2x 0x%2.2x\n", res_ptr[0], res_ptr[1]);
        }
        rc = -1;
    }

    free((void *)res_ptr);
    return rc;
}

int setup_env(int fd, FILE *fptr)
{
    int rc = 0;
    char *res_ptr;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    memset(res_ptr, 0, res_len);
    rc = send_command(fd, fptr, card_type, res_ptr, res_len, 5);
    if ( rc ) {
        fprintf(fptr, "error sending env command\n");
        printf("error sending env command\n");
    }
    free((void *)res_ptr);
    return rc;
}

int mount_partition(int fd, FILE *fptr)
{
    int rc = 0;
    char *res_ptr;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    memset(res_ptr, 0, res_len);
    rc = send_command(fd, fptr, mnt_command, res_ptr, res_len, 5);
    if ( rc ) {
        fprintf(fptr, "error sending mount command\n");
        printf("error sending mount command\n");
    }
    free((void *)res_ptr);
    return rc;
}

int get_sn_string(int fd, FILE *fptr, char *sn)
{
    int rc = 0;
    char *res_ptr;
    char *token, *target, *target_pre;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    memset(res_ptr, 0, res_len);
    rc = send_command(fd, fptr, sn_command, res_ptr, res_len, 5);
    if ( rc ) {
        fprintf(fptr, "error sending disp fru command\n");
        printf("error sending disp fru command\n");
    }
    token = strtok(res_ptr, "\r");
    while ( token != NULL ) {
        target_pre = target;
        target = token;
        fprintf(fptr, "target = %s \n", target);
        token = strtok(NULL, " ");
    }
    target = target_pre;
    if ( strlen(target) > 8 )
        strcpy(sn, target);
    free((void *)res_ptr);
    return rc;
}

int get_fru_json(int fd, FILE *fptr, char *sn)
{
    int rc = 0;
    char *res_ptr;
    char *token = NULL, *target = NULL, *target_pre = NULL;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    memset(res_ptr, 0, res_len);
    rc = send_command(fd, fptr, fru_json, res_ptr, res_len, 10);
    if ( rc ) {
        fprintf(fptr, "error sending disp fru command\n");
        printf("error sending disp fru command\n");
    }
    token = strtok(res_ptr, "\"");
    while ( token != NULL ) { 
    target_pre = target;
    target = token;
    fprintf(fptr, "target = %s \n", target);
        token = strtok(NULL, "\"");
    }
    if ( target > target_pre )
        strncpy(sn, target_pre, target - target_pre);
    free((void *)res_ptr);
    return rc;
}

int read_cpld(int fd, FILE *fptr, char *offset, char *value)
{
    int rc = 0;
    char *res_ptr;
    char *cmd, *res;

    res_ptr = (char *)malloc(sizeof(char) * res_len);
    res = res_ptr;
    cmd = (char *)malloc(sizeof(char) * strlen(read_cpld_cmd) + 6);
    memset(res_ptr, 0, res_len);
    memset(cmd, 0, strlen(read_cpld_cmd) + 6);
    strcpy(cmd, read_cpld_cmd);
    strcat(cmd, offset);
    strcat(cmd, "\n");
    *value = 0;
    rc = send_command(fd, fptr, cmd, res_ptr, res_len, 10);
    if ( rc ) {
        fprintf(fptr, "error sending read cpld command\n");
        printf("error sending read cpld command\n");
    } else {
        while ( *res != '\n' )
            res++;
        res++;
    printf("%s\n", res);
        *value = (char)strtol(res, NULL, 0);
    }
    fprintf(fptr, "response from read command %s\n", res_ptr);

    free((void *)res_ptr);
    free((void *)cmd);
    return rc;
}

int sysreset(int fd, FILE *fptr)
{
    int rc = 0;
    char *cmd;

    cmd = (char *)malloc(sizeof(char) * strlen(sysreset_cmd) + 6);
    memset(cmd, 0, strlen(sysreset_cmd) + 6);
    strcpy(cmd, sysreset_cmd);
    rc = send_command(fd, fptr, cmd, NULL, 0, 10);
    if ( rc ) {
        fprintf(fptr, "error sending sysreset.sh command\n");
        printf("error sending sysreset.sh command\n");
    }
    free((void *)cmd);
    return rc;
}

int get_sn(int fd, FILE *fptr, char *sn_string)
{
    int rc = 0;

    uart_set_dtr(fd, fptr, 0);
    sleep(1);

    rc = connect_nic(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to connect to nic\n");
        printf("failed to connect to nic\n");
    return rc;
    }
/*    
    rc = setup_env(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to setup nic env\n");
    return rc;
    }
    rc = mount_partition(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to mount nic_util\n");
    return rc;
    }
*/
    rc = get_fru_json(fd, fptr, sn_string);
    if ( rc ) {
        fprintf(fptr, "failed to get sierial number\n");
        printf("failed to get sierial number\n");
    return rc;
    }
    fprintf(fptr, "serial number is %s\n", sn_string);
    return rc;
}

int check_force_gold(int fd, FILE *fptr)
{
    int rc = 0;
    char gold_value;

    uart_set_dtr(fd, fptr, 0);
    uart_set_rts(fd, fptr, 1);
    sleep(1);

    rc = connect_nic(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to connect to nic\n");
        printf("failed to connect to nic\n");
        return rc;
    }

    rc = read_cpld(fd, fptr, "0x12", &gold_value);
    if ( rc ) {
        fprintf(fptr, "failed to get cpld reg value %x at dts high\n", gold_value);
        printf("failed to get cpld reg value %x at dts high\n", gold_value);
        return rc;
    }
    fprintf(fptr, "cpld value = 0x%2.2x\n", gold_value);
    printf("gold_value = %x\n", gold_value);
    if ( gold_value & 0x08 )
        fprintf(fptr, "force gold is set as expected\n");
    else {
        fprintf(fptr, "force gold is not set as expected\n");
        printf("force gold is not set as expected\n");
        return -1;
    }

    uart_set_rts(fd, fptr, 0);
    rc = read_cpld(fd, fptr, "0x12", &gold_value);
    if ( rc ) {
        fprintf(fptr, "failed to get cpld reg value %x at dts low\n", gold_value);
        printf("failed to get cpld reg value %x at dts low\n", gold_value);
        return rc;
    }
    fprintf(fptr, "cpld value = 0x%2.2x\n", gold_value);
    if ( (gold_value & 0x08) == 0 )
        fprintf(fptr, "force gold is cleared as expected\n");
    else {
        fprintf(fptr, "force gold is not cleared as expected\n");
        printf("force gold is not cleared as expected\n");
        return -1;
    }
    return rc;
}

int check_force_goldboot(int fd, FILE *fptr)
{
    int rc = 0, i;
    char gold_value;
    char pbuf[1024];

    uart_set_dtr(fd, fptr, 0);
    uart_set_rts(fd, fptr, 1);
    sleep(1);

    rc = connect_nic(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to connect to nic\n");
        printf("failed to connect to nic\n");
        return rc;
    }

    rc = sysreset(fd, fptr);
    if ( rc ) {
        fprintf(fptr, "failed to sysreset nic\n");
        printf("failed to sysreset nic\n");
        return rc;
    }
    
    
    /*
    waiting fw to bootup, it was sleep(90), but we run into issue: read function get extra data which not show up on UART Rx Line.
    this is a known issue, tcflush(fd, TCIOFLUSH) doesn't work well on FTDI serial device, sometimes leave data there, 
    details https://bugzilla.kernel.org/show_bug.cgi?id=5730
    so, as a workaround we keep read all output while waiting to clear FTDI device buffer
    */
    for ( i=0; i < 90; i++ ) {
        memset(pbuf, 0, 1024);
        read(fd, pbuf, 1024);
        fprintf(fptr, "%s", pbuf);
        printf("%s", pbuf);
        sleep(1);
    }

    tcflush(fd, TCIOFLUSH);
    rc = connect_nic(fd, fptr);
    if ( rc == 0xa ) {
        fprintf(fptr, "connected to nic running goldfw\n");
        printf("connected to nic running goldfw\n");
        rc = 0;
    } else if ( rc ) {
        fprintf(fptr, "failed to connect nic after forcing goldfw\n");
        printf("failed to connect nic after forcing goldfw\n");
    } else if ( rc == 0 ) {
        fprintf(fptr, "failed to find gold-fw prompt, possible still in mainfw\n");
        printf("failed to find gold-fw prompt, possible still in mainfw\n");
        rc = -1;
    }
    
    fprintf(fptr, "clear force gold signal\n");
    printf("clear force gold signal\n");
    uart_set_rts(fd, fptr, 0);

    return rc;
}

int set_spi_mux(int fd, FILE *fptr, unsigned char mux)
{
    int rc;
    unsigned char mask;
    unsigned char data[2];

    mask = (mux & 0x3) << 6;
    rc = UartRegRead(fd, fptr, data, 2);
    if ( rc != 2) {
        fprintf(fptr, "%s: failed to get uart register value\n", __func__);
        printf("%s: failed to get uart register value\n", __func__);
        return -1;
    }
    fprintf(fptr, "%s initial reg value 0x%2x 0x%2x\n", __func__, data[0], data[1]);
    data[0] &= 0x3e;
    data[0] |= mask;
    fprintf(fptr, "%s setting reg value 0x%2x 0x%2x\n", __func__, data[0], data[1]);
    rc = UartRegWrite(fd, data, 2);
    if ( rc != 2) {
        fprintf(fptr, "%s: failed to write uart register value\n", __func__);
        printf("%s: failed to write uart register value\n", __func__);
        return -1;
    }
    return 0;
}

int check_qspi_id(int fd, FILE *fptr)
{
    int rc;
    unsigned char qspi_id[5] = {0x00, 0xc2, 0x25, 0x3c, 0xc2};
    unsigned char qspi_id_1[5] = {0x00, 0x20, 0xbb, 0x22, 0x10};
    unsigned char qspi_id_2[5] = {0x00, 0xef, 0x80, 0x22, 0x00};
    unsigned char id[5];

    uart_set_dtr(fd, fptr, 1);
    sleep(1);

    rc = set_spi_mux(fd, fptr, 1);
    if ( rc ) { 
        fprintf(fptr, "failed to set up spi mux to qspi\n");
        printf("failed to set up spi mux to qspi\n");
        return rc;
    }
    rc = qspi_read_id(fd, fptr, id);
    if ( rc ) {
        fprintf(fptr, "failed to read qspi id\n");
        printf("failed to read qspi id\n");
        return rc;
    }
    if ( (memcmp(qspi_id, id, 5) != 0) && (memcmp(qspi_id_1, id, 5) != 0) && (memcmp(qspi_id_2, id, 5) != 0) ) {
        fprintf(fptr, "invalid qspi device id read\n");
        printf("invalid qspi device id read\n");
        printf("id fields %x %x %x %x %x\n", id[0], id[1], id[2], id[3], id[4]);
        return -1;
    }
    return 0;
}

int check_cpld_id(int fd, FILE *fptr)
{
    int rc;
    unsigned char cpld_id_ortano[4] = {0x21, 0x2e, 0x30, 0x43}; 
    unsigned char cpld_id_vomero2[4] = {0x01, 0x2b, 0xc0, 0x43};
    unsigned char id[4];

    uart_set_dtr(fd, fptr, 1);
    sleep(1);

    rc = set_spi_mux(fd, fptr, 0);
    if ( rc ) { 
        fprintf(fptr, "failed to set up spi mux to qspi\n");
        printf("failed to set up spi mux to qspi\n");
        return rc;
    }
    rc = spi_cpld_id(fd, fptr, id);
    if ( rc ) {
        fprintf(fptr, "failed to read cpld id\n");
        printf("failed to read cpld id\n");
        return rc;
    }
    if ( strstr(card_type, "VOMERO2") )
        rc = memcmp(cpld_id_vomero2, id, 4);
    else
        rc = memcmp(cpld_id_ortano, id, 4);
    if ( rc ) {
        fprintf(fptr, "invalid cpld device id read\n");
        printf("invalid cpld device id read\n");
        return -1;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    int fd, opt, rc;
    FILE *fptr;
    char filename[12]="ttyUSB0.log";
    char sn_string[16];

    sn_string[0] = 0;
    while( (opt = getopt(argc, argv, ":b:p:d:c:") ) != -1) {
        switch ( opt ) {
            case 'b':
                baudrate = atoi(optarg);
                break;

            case 'p':
                if ( strlen(optarg) > 14 ) {
                    printf("port name longer than expected\n");
                    return -1;
                }
                strcpy(filename, optarg);
                strcat(filename, ".log");
                strcpy(portname, "/dev/");
                strcat(portname, optarg);
                break;

            case 'd':
                if ( strlen(optarg) > 11 ) {
                    printf("invalid asic device name\n");
                    return -1;
                }
                strcpy(loginprompt, optarg);
                strcat(loginprompt, " login:");
            break;

            case 'c':
                if ( strlen(optarg) > 7 ) {
                    printf("invalid card type name\n");
                    return -1;
                }
                strcpy(card_type, "export CARD_TYPE=");
                strcat(card_type, strupr(optarg));
                strcat(card_type, "\n");
            break;

            default:
            break;
        }
    }

    fd = open(portname, O_RDWR | O_NOCTTY | O_SYNC);
    fptr = fopen(filename, "w");

    if (fd < 0) {
        fprintf(fptr, "Error opening %s: %s\n", portname, strerror(errno));
        close(fd);
        fclose(fptr);
        return -1;
    }

    rc = config_serial(fd, fptr, baudrate);
    if ( rc )
        goto exit;
    fprintf(fptr, "Flushing receive buffer\n");
    sleep(1);
    tcflush(fd, TCIOFLUSH);

    if ( strstr(loginprompt, "elba-gold") ) {

        fprintf(fptr, "goldfw only test\n");
        printf("goldfw only test\n");
        rc = get_sn(fd, fptr, sn_string);
        if ( rc )
            goto exit;

        rc = check_force_gold(fd, fptr);

    } else {

        rc = get_sn(fd, fptr, sn_string);
        if ( rc )
            goto exit;

        rc = check_qspi_id(fd, fptr);
        if ( rc )
            goto exit;

        rc = check_cpld_id(fd, fptr);
        if ( rc )
            goto exit;

        rc = check_force_gold(fd, fptr);
        if ( rc )
            goto exit;

        rc = check_force_goldboot(fd, fptr);
    }

exit:    
    close(fd);

    if ( rc == 0 && strlen(sn_string) ) {
        fprintf(fptr, "ROT test PASSED %s %s\n", sn_string, portname);
        printf("ROT test PASSED %s %s\n", sn_string, portname);
        strcat(sn_string, ".log");
        rename(filename, sn_string);
    } else {
        fprintf(fptr, "ROT test FAILED\n");
        printf("ROT test FAILED\n");
    }
    fclose(fptr);
    return 0;
}
