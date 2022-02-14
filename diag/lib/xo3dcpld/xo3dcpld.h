#include "../../include/cType.h"

int cpld_read(u_int8_t addr);
int cpld_write(u_int8_t addr, u_int8_t data);
int mdio_wr(u_int8_t addr, u_int16_t data, u_int8_t phy);
int mdio_rd(u_int8_t addr, u_int16_t *data, u_int8_t phy);
int mdio_smi_rd(u_int8_t addr, u_int16_t *data, u_int8_t phy);
int mdio_smi_wr(u_int8_t addr, u_int16_t data, u_int8_t phy);
