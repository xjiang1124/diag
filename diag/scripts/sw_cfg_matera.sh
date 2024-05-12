#!/bin/bash

# Marvell 88E6185 instance 0 port 0 - 4 connect to slots 0 - 4
# Marvell 88E6185 instance 0 port 5 connects to instance 1 port 4
for((n = 0x10; n <= 0x15; n++))
{
    /home/diag/diag/util/fpgautil mdiowr 0 $n 0x1 0x003e
    value=$(/home/diag/diag/util/fpgautil mdiord 0 $n 0x1 | grep RD | awk -F "= " '{print $2}')
    printf 'MVL 0 phy: 0x%02x, reg 0x1 value: 0x%04x\n' "$n" "$value"
    /home/diag/diag/util/fpgautil mdiowr 0 $n 0x4 0x77
    value=$(/home/diag/diag/util/fpgautil mdiord 0 $n 0x4 | grep RD | awk -F "= " '{print $2}')
    printf 'MVL 0 phy: 0x%02x, reg 0x4 value: 0x%04x\n' "$n" "$value"
}

# Marvell 88E6185 instance 1 port 5 - 9 connect to slots 5 - 9
# Marvell 88E6185 instance 1 port 4 connects to instance 0 port 5
for((n = 0x14; n <= 0x19; n++))
{
    /home/diag/diag/util/fpgautil mdiowr 1 $n 0x1 0x003e
    value=$(/home/diag/diag/util/fpgautil mdiord 1 $n 0x1 | grep RD | awk -F "= " '{print $2}')
    printf 'MVL 1 phy: 0x%02x, reg 0x1 value: 0x%04x\n' "$n" "$value"
    /home/diag/diag/util/fpgautil mdiowr 1 $n 0x4 0x77
    value=$(/home/diag/diag/util/fpgautil mdiord 1 $n 0x4 | grep RD | awk -F "= " '{print $2}')
    printf 'MVL 1 phy: 0x%02x, reg 0x4 value: 0x%04x\n' "$n" "$value"
}

# Marvell 88E6185 instance 0 port 9 connects to CPU
/home/diag/diag/util/fpgautil mdiowr 0 0x19 0x1 0x003e
value=$(/home/diag/diag/util/fpgautil mdiord 0 0x19 0x1 | grep RD | awk -F "= " '{print $2}')
printf 'MVL 0 phy: 0x19, reg 0x1 value: 0x%04x\n' "$value"
/home/diag/diag/util/fpgautil mdiowr 0 0x19 0x4 0x77
value=$(/home/diag/diag/util/fpgautil mdiord 0 0x19 0x4 | grep RD | awk -F "= " '{print $2}')
printf 'MVL 0 phy: 0x19, reg 0x4 value: 0x%04x\n' "$value"

# Marvell 88E6185 instance 1 port 0 connects to Debug slot
/home/diag/diag/util/fpgautil mdiowr 1 0x10 0x1 0x003e
value=$(/home/diag/diag/util/fpgautil mdiord 1 0x10 0x1 | grep RD | awk -F "= " '{print $2}')
printf 'MVL 1 phy: 0x10, reg 0x1 value: 0x%04x\n' "$value"
/home/diag/diag/util/fpgautil mdiowr 1 0x10 0x4 0x77
value=$(/home/diag/diag/util/fpgautil mdiord 1 0x10 0x4 | grep RD | awk -F "= " '{print $2}')
printf 'MVL 1 phy: 0x10, reg 0x4 value: 0x%04x\n' "$value"
exit 0