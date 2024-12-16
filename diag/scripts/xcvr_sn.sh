#!/bin/bash
usage() {
    echo "$0 Usage:"
    echo "$0 -s X -p Y [returns serial number of QSFP/SFP transceiver EEPROM on port Y]"
    echo "$0 -s X -d   [detects prescence of QSFP/SFP transceiver(s)]"
 }

if [[ $# -eq 0 ]]
then
    usage
    exit
fi

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        #-------------
        -h|--help)
        usage
        exit
        ;;
        #-------------
        -p|--port)
        PORT=$2
        shift 2
        ;;
        #-------------
        -s|--slot)
        SLOT=$2
        shift 2
        ;;
        #-------------
        *)
        echo "Invalid input"
        echo "help: $0 -h"
        exit -1
        ;;
    esac
done

if [[ -z $PORT ]]; then usage; exit -1; fi
if [[ -z $SLOT ]]; then usage; exit -1; fi

LOGFILE=/tmp/qsfp$SLOT
turn_on_slot.sh off $SLOT > $LOGFILE
# come up in proto to prevent zephyr from taking over SPI bridge
sleep 3; turn_on_slot.sh on $SLOT 0 0 >> $LOGFILE
sleep 3

reg_data=$(i2cget -y $((SLOT+2)) 0x4a 0x2)
port_mask=$(( ($PORT+1) << 4 ))
prsnt=$(( $reg_data & $port_mask ))
if [[ $prsnt == 0 ]]; then echo "SLOT-$SLOT PORT-$PORT XCVR not present/detected"; exit -1; fi

i2cset -y $((SLOT+2)) 0x4a 0x2 0x0
sleep 0.3 # wait for SPI
fpgautil spibridge $SLOT i2creset $PORT  >> $LOGFILE

fpgautil spibridge $SLOT i2ctransw $PORT 0x50 0xc4  >> $LOGFILE
sn1=$(fpgautil spibridge $SLOT i2ctransr $PORT 0x50 8 | tail -n1)

fpgautil spibridge $SLOT i2ctransw $PORT 0x50 0xcc  >> $LOGFILE
sn2=$(fpgautil spibridge $SLOT i2ctransr $PORT 0x50 4 | tail -n1)

fpgautil spibridge $SLOT i2ctransw $PORT 0x50 0xd0  >> $LOGFILE
sn3=$(fpgautil spibridge $SLOT i2ctransr $PORT 0x50 4 | tail -n1)

sn=$(echo $sn1 $sn2 $sn3 | xxd -r -p)

echo "SLOT-$SLOT PORT-$PORT XCVR SN: $sn"