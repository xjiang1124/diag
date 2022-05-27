#!/bin/bash

display() {
    echo "=== TPS53695 Core OC Current Setting ==="
    echo "Setting on Page 0"
    i2cset -yf 0 0x62 0 0
    val_da=$(i2cget -yf 0 0x62 0xda w)
    val_46=$(i2cget -yf 0 0x62 0x46 w)
    val_4a=$(i2cget -yf 0 0x62 0x4A w)
    echo "0xDA: ${val_da}"
    echo "0x46: ${val_46}"
    echo "0x4A: ${val_4a}"
    echo "========================================"

}

apply_fix() {
    echo "=== Applying TPS53705 Core OC Fix ==="
    echo "Fix is on Page 0 only"
    i2cset -yf 0 0x62 0 0
    i2cset -yf 0 0x62 0xda 0xC864 w
    i2cset -yf 0 0x62 0x46 0x007D w
    i2cset -yf 0 0x62 0x4A 0x0064 w
    i2cset -yf 0 0x62 0x11 c
    echo "TPS53659 Core OC fix done"
    echo "====================================="
}

if [[ $# -eq 0 ]]
then
    display
    exit
fi

if [[ $1 = "apply" ]]
then
    apply_fix
    display
fi

echo "FIX O2 VRM OC DONE"
echo "FIX O2 VRM OC DONE"
