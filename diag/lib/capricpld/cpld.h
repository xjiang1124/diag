#include "../../include/cType.h"

int Cpld_read(unsigned char addr);
int Cpld_write(unsigned char addr, unsigned char data);
int Mdio_wr(unsigned char addr, unsigned short int data, unsigned char phy);
int Mdio_rd(unsigned char addr, unsigned short int* data, unsigned char phy);
int Mdio_smi_rd(unsigned char addr, unsigned short int* data, unsigned char phy);
int Mdio_smi_wr(unsigned char addr, unsigned short int data, unsigned char phy);
