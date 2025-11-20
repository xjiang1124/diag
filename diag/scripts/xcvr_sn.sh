#!/bin/bash
usage() {
    echo "$0 Usage:"
    echo "$0 -s X -p Y [returns serial number of QSFP/SFP transceiver EEPROM on port Y]"
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

if [[ $MTP_TYPE == "MTP_MATERA" ]]
then
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
    fpgautil spibridge $SLOT qsfpdump $PORT | tee -a $LOGFILE
    sn=$(grep -a "Vendor SN" $LOGFILE | awk -F"'" '{print $(NF-1)}')
    echo
    echo "SLOT-$SLOT PORT-$PORT XCVR SN: $sn"
elif [[ $MTP_TYPE == "MTP_PANAREA" ]]
then
    LOGFILE=/tmp/qsfp$SLOT
    rm $LOGFILE
    sucutil exec -s $SLOT -c "osfp info"
    printf "\n"
    sucutil exec -s $SLOT -c "osfp page_dump" 
    printf "\n"
    sucutil exec -s $SLOT -c "osfp serialnumber" >> $LOGFILE
    sn=$(awk -F'N:' '{print $2}' /tmp/qsfp6)
    #sn=$(awk '{print $(NF)}' $LOGFILE)
    echo "SLOT-$SLOT PORT-$PORT XCVR SN:$sn"
else
    echo "ERROR: THIS COMMAND ONLY WORKS ON MATERA OR PANAREA MTP's!!"
    exit -1
fi
