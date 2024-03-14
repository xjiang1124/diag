#!/bin/bash

# Marvell 88E6185 instance 0 port 0 - 4 connect to slots 0 - 4
# Marvell 88E6185 instance 0 port 5 connects to instance 1 port 4
for((n = 0x10; n <= 0x15; n++))
{
    fpgautil mdiowr 0 $n 0x1 0x003e
    fpgautil mdiowr 0 $n 0x4 0x77 
}

# Marvell 88E6185 instance 1 port 5 - 9 connect to slots 5 - 9
# Marvell 88E6185 instance 1 port 4 connects to instance 0 port 5
for((n = 0x14; n <= 0x19; n++))
{
    fpgautil mdiowr 1 $n 0x1 0x003e
    fpgautil mdiowr 1 $n 0x4 0x77 
}

# Marvell 88E6185 instance 0 port 9 connects to CPU
fpgautil mdiowr 0 0x19 0x1 0x003e
fpgautil mdiowr 0 0x19 0x4 0x77

# Marvell 88E6185 instance 1 port 0 connects to Debug slot
fpgautil mdiowr 1 0x10 0x1 0x003e
fpgautil mdiowr 1 0x10 0x4 0x77

exit 0