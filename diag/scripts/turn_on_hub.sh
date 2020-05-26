/bin/bash

hub_ctrl() {
    #disable all the hubs first before enabling one of them 
    #to avoid a race condition where you can get more than one i2c channel enabled
    smbutil -dev=hub_1 -sd -addr=0
    smbutil -dev=hub_2 -sd -addr=0
    smbutil -dev=hub_3 -sd -addr=0
    smbutil -dev=hub_4 -sd -addr=0
    #smbutil -dev=hub_5 -sd -addr=0

    smbutil -dev=hub_1 -sd -addr=$1
    smbutil -dev=hub_2 -sd -addr=$2
    smbutil -dev=hub_3 -sd -addr=$3
    smbutil -dev=hub_4 -sd -addr=$4
    #smbutil -dev=hub_5 -sd -addr=$5
}

case $1 in
    "1")
        echo "1-1"
        hub_ctrl 1 0 0 0 0
        ;;
    "2")
        echo "2-2"
        hub_ctrl 2 0 0 0 0
        ;;
    "3")
        echo "3-3"
        hub_ctrl 4 0 0 0 0
        ;;
    "4")
        echo "4-4"
        hub_ctrl 8 0 0 0 0
        ;;
    "5")
        echo "5-5"
        hub_ctrl 0 1 0 0 0
        ;;
    "6")
        echo "6-6"
        hub_ctrl 0 2 0 0 0
        ;;
    "7")
        echo "7-7"
        hub_ctrl 0 4 0 0 0
        ;;
    "8")
        echo "8-8"
        hub_ctrl 0 8 0 0 0
        ;;
    "9")
        echo "9-9"
        hub_ctrl 0 0 1 0 0
        ;;
    "10")
        echo "10-10"
        hub_ctrl 0 0 2 0 0
        ;;
    "21")
        echo "21-21"
        hub_ctrl 0 0 0 0 1
        ;;
    "22")
        echo "22-22"
        hub_ctrl 0 0 0 0 2
        ;;
    "23")
        echo "23-23"
        hub_ctrl 0 0 0 0 4
        ;;
    *)
        echo "invalid input", $1
esac

if [ "$#" -ne 1 ]; then
    case $2 in
        "0")
            bus="1"
            ;;
        "1")
            bus="2"
            ;;
        "2")
            bus="4"
            ;;
        "3")
            bus="8"
            ;;
        *)
            echo "Invalide second argument", $2
    esac
    smbutil -dev=NIC_HUB -sd -addr=$bus -uut=UUT_$1
fi


