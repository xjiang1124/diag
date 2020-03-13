#!/bin/bash

function usage() {
    echo "aapl_prbs_all.sh PCIE/ETH PRBS PRBS7/9/15/31 DURATION"
}

if [ $# -eq 0 ]
then
    usage
    exit 0
fi

if [ $# -ge 1 ]
then
    INF=$1
    INF=${INF^^}
else
    INF="PCIE"
fi

if [ $# -ge 2 ]
then
    STAGE=$2
    STAGE=${STAGE^^}
else
    STAGE="PRBS"
fi

if [ $# -ge 3 ]
then
    POLY=$3
    POLY=${POLY^^}
else
    POLY="PRBS31"
fi

if [ $# -ge 4 ]
then
    DURATION=$4
else
    DURATION=60
fi

echo "INF: $INF; STAGE: $STAGE; POLY: $POLY; DURA: $DURATION"

echo $CARD_TYPE
card_type=$CARD_TYPE

SERVER_IP=localhost
PORT=9000

function get_card_config() {
    # Naples100
    declare -a sbus_list_naples100_eth=("34" "35" "36" "37" "38" "39" "40" "41")
    declare -a atten_list_naples100_eth=("0" "0" "0" "0" "0" "0" "0" "0")
    declare -a pre_list_naples100_eth=("2" "2" "2" "2" "2" "2" "2" "2")
    declare -a post_list_naples100_eth=("12" "12" "12" "12" "12" "12" "12" "12")
    declare -a tx_inv_list_naples100_eth=("0" "0" "0" "0" "0" "0" "0" "0")
    declare -a rx_inv_list_naples100_eth=("0" "0" "0" "0" "0" "0" "0" "0")

    declare -a sbus_list_naples100_pcie=("2" "4" "6" "8" "10" "12" "14" "16" "18" "20" "22" "24" "26" "28" "30" "32")

    # Naples25
    declare -a sbus_list_naples25_eth=("34" "38")
    declare -a atten_list_naples25_eth=("0" "0")
    declare -a pre_list_naples25_eth=("2" "2")
    declare -a post_list_naples25_eth=("12" "12")
    declare -a tx_inv_list_naples25_eth=("1" "0")
    declare -a rx_inv_list_naples25_eth=("0" "1")

    declare -a sbus_list_naples25_pcie=("18" "20" "22" "24" "26" "28" "30" "32")

    # Naples25OCP
    declare -a sbus_list_naples25ocp_eth=("34" "38")
    declare -a atten_list_naples25ocp_eth=("0" "0")
    declare -a pre_list_naples25ocp_eth=("2" "2")
    declare -a post_list_naples25ocp_eth=("12" "12")
    declare -a tx_inv_list_naples25ocp_eth=("1" "0")
    declare -a rx_inv_list_naples25ocp_eth=("0" "1")

    declare -a sbus_list_naples25ocp_pcie=("2" "4" "6" "8" "10" "12" "14" "16")

    # Naples25SWM
    declare -a sbus_list_naples25swm_eth=("34" "38")
    declare -a atten_list_naples25swm_eth=("0" "0")
    declare -a pre_list_naples25swm_eth=("2" "2")
    declare -a post_list_naples25swm_eth=("12" "12")
    declare -a tx_inv_list_naples25swm_eth=("1" "0")
    declare -a rx_inv_list_naples25swm_eth=("0" "1")

    declare -a sbus_list_naples25swm_pcie=("18" "20" "22" "24" "26" "28" "30" "32")

    if [ $card_type = "NAPLES100" ]
    then
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples100_eth[@]}") 
            atten_list=("${atten_list_naples100_eth[@]}") 
            pre_list=("${pre_list_naples100_eth[@]}") 
            post_list=("${post_list_naples100_eth[@]}") 
            tx_inv_list=("${tx_inv_list_naples100_eth[@]}") 
            rx_inv_list=("${rx_inv_list_naples100_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples100_pcie[@]}") 
        else
            echo "Wrong INF $INF"
            exit 1
        fi
    elif [ $card_type = "NAPLES25" ]
    then
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples25_eth[@]}") 
            atten_list=("${atten_list_naples25_eth[@]}") 
            pre_list=("${pre_list_naples25_eth[@]}") 
            post_list=("${post_list_naples25_eth[@]}") 
            tx_inv_list=("${tx_inv_list_naples25_eth[@]}") 
            rx_inv_list=("${rx_inv_list_naples25_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples25_pcie[@]}") 
        else
            echo "Wrong INF $INF"
            exit 1
        fi
    elif [ $card_type = "NAPLES25OCP" ]
    then
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples25ocp_eth[@]}") 
            atten_list=("${atten_list_naples25ocp_eth[@]}") 
            pre_list=("${pre_list_naples25ocp_eth[@]}") 
            post_list=("${post_list_naples25ocp_eth[@]}") 
            tx_inv_list=("${tx_inv_list_naples25ocp_eth[@]}") 
            rx_inv_list=("${rx_inv_list_naples25ocp_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples25ocp_pcie[@]}") 
        else
            echo "Wrong INF $INF"
            exit 1
        fi
    elif [ $card_type = "NAPLES25SWM" ]
    then
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples25swm_eth[@]}") 
            atten_list=("${atten_list_naples25swm_eth[@]}") 
            pre_list=("${pre_list_naples25swm_eth[@]}") 
            post_list=("${post_list_naples25swm_eth[@]}") 
            tx_inv_list=("${tx_inv_list_naples25swm_eth[@]}") 
            rx_inv_list=("${rx_inv_list_naples25swm_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples25swm_pcie[@]}") 
        else
            echo "Wrong INF $INF"
            exit 1
        fi

    else
        if [ $INF = "ETH" ]
        then
            sbus_list=("${sbus_list_naples100_eth[@]}") 
            atten_list=("${atten_list_naples100_eth[@]}") 
            pre_list=("${pre_list_naples100_eth[@]}") 
            post_list=("${post_list_naples100_eth[@]}") 
            tx_inv_list=("${tx_inv_list_naples100_eth[@]}") 
            rx_inv_list=("${rx_inv_list_naples100_eth[@]}") 
        elif [ $INF = "PCIE" ]
        then
            sbus_list=("${sbus_list_naples100_pcie[@]}") 
        else
            echo "Wrong INF $INF"
            exit 1
        fi
    fi

    if [ $INF = "ETH" ]
    then
        rom_file="/data/nic_arm/aapl/serdes.0x1087_244D.rom"
        div="165"
        width="40"
    elif [ $INF = "PCIE" ]
    then
        rom_file="/data/nic_arm/aapl/serdes.0x10A0_2347.rom"
        div="160"
        width="40"
    else
        echo "Wrong INF $INF"
        exit 1
    fi
}

function disp_eye() {
    for sbus in ${sbus_list[@]}
    do
        echo "=== DISP EYE;  sbus $sbus; $SERVER_IP:$PORT"
        aapl eye -server $SERVER_IP -port $PORT -addr $sbus -min-dwell 1e6 -max-dwell 1e8 -x-res 64 -y-points 512 -print-vbtc -print-hbtc
    done
    echo "AAPL DISP EYE DONE"
}

function do_reset() {
    for sbus in ${sbus_list[@]}
    do
        echo "Resetting sbus $sbus; $SERVER_IP:$PORT"
        aapl serdes-init -server $SERVER_IP -port $PORT -addr $sbus -reset 
        aapl cmd -server $SERVER_IP -port $PORT -addr $sbus -aacs "tck_delay 10"
    done
    echo "AAPL SERDES RESET DONE"
}

function do_init() {
    for sbus in ${sbus_list[@]}
    do
        echo "Initializing sbus $sbus; $SERVER_IP:$PORT"
        aapl  serdes-init -server $SERVER_IP -port $PORT -addr $sbus -div $div -width $width -elb -disable-signal-ok -firm $rom_file
    done
    echo "AAPL SERDES INIT DONE"
}

function set_si() {
    for idx in "${!sbus_list[@]}"
    do
        sbus=${sbus_list[$idx]}
        atten=${atten_list[$idx]}
        pre=${pre_list[$idx]}
        post=${post_list[$idx]}
        tx_inv=${tx_inv_list[$idx]}
        rx_inv=${rx_inv_list[$idx]}

        echo "=== Setting SI $SERVER_IP:$PORT sbus $sbus atten $atten pre $pre post $post ==="
        if [ $INF = "ETH" ]
        then
            aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -atten 0 -pre $pre -post $post -tx-invert $tx_inv -rx-invert $rx_inv
        fi
    done
}

function do_dfe() {
    for idx in "${!sbus_list[@]}"
    do
        sbus=${sbus_list[$idx]}

        echo "=== DFE $SERVER_IP:$PORT sbus $sbus atten $atten pre $pre post $post ==="

        aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -ical-tune
        #aapl dfe -server $SERVER_IP -port $PORT -addr $sbus -start-adaptive
    done

    echo "Wait for DFE done"
    sleep 5
    echo "DFE done"
}

function serdes_display() {
    for sbus in "${sbus_list[@]}"
    do
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -display
    done
}

function prbs_preset() {
    for sbus in ${sbus_list[@]}
    do
        echo "=== PRBS preset $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -tx-data-sel $POLY -rx-mode $POLY
    done
}

function prbs_start() {
    #for sbus in $sbus_list
    for sbus in ${sbus_list[@]}
    do
        echo "=== PRBS started $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -error-reset
    done
}

function prbs_check() {
    #for sbus in $sbus_list
    for sbus in ${sbus_list[@]}
    do
        echo "=== $SERVER_IP:$PORT $sbus ==="
        aapl serdes -server $SERVER_IP -port $PORT -addr $sbus -ber -ber-dwell 1
    done

}

function do_prbs() {
    echo "do prbs"
    echo $1
    
    if [ $1 == "SET_SI" ]
    then
        set_si
    elif [ $1 == "DFE" ]
    then
        do_dfe
    elif [ $1 == "DISP" ]
    then
        serdes_display        
    elif [ $1 == "EYE" ]
    then
        disp_eye        
    elif [ $1 == "PRBS_PRE" ]
    then
        prbs_preset
    elif [ $1 == "PRBS_START" ]
    then
        prbs_start
    elif [ $1 == "PRBS_CHECK" ]
    then
        prbs_check
    elif [ $1 == "PRBS" ]
    then
        # Do all prbs stuff
        set_si
        prbs_preset
        do_dfe
        serdes_display
        prbs_preset
        prbs_start
        echo "Sleep $DURATION"
        sleep $DURATION
        prbs_check
    else
        echo "Invalid stage $1"
    fi

    echo "AAPL PRBS DONE"
}

get_card_config

if [ $STAGE = "RESET" ]
then
    do_reset
elif [ $STAGE = "INIT" ]
then
    do_init | tee /data/nic_arm/aapl/aapl_init.log
else
    do_prbs $STAGE | tee /data/nic_arm/aapl/aapl.log
fi

echo "AAPL OP DONE"

