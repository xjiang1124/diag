#!/bin/bash

if [[ $# -ne 1 ]]; then
    exit 1
fi
if [[ $1 != "LINKUP" && $1 != "PRBS" ]]; then
    exit 1
fi
PRBS_GEN_START=1
PRBS_GEN_STOP=2
PRBS_CHECKER_START=3
PRBS_CHECKER_STOP=4
PRBS_ERR_READ=5
PRBS_ERR_CLEAR=6
AN_ENABLE=7
CONFIG_PHY_STUB_TEST=11
CONFIG_PHY_PKT_CHECKER=14
CONFIG_PHY_PKT_GENERATOR=15
PHY_PKT_CHECKER_READ_COUNTER=16
CONFIG_PHY_MODE=18

ENABLE=1
DISABLE=0

DEV_XCVR=0
DEV_PHY=1

NON_ERR_PKT_BURST=127
ERR_PKT_BURST=126
PKT_PAYLOAD=1
PKT_LEN=1
NON_ERR_PKT=0
ERR_PKT=1
TX_POLARITY_NO_INVERT=0
NO_FORCE_ERR=0

PRBS_31=31
TX_POLARITY_NO_INVERT=0
NO_FORCE_ERR=0
RX_POLARITY_NO_INVERT=0
PRBS_NO_LOCK_BEFORE_COUNTING=0

PHY_PAGE_1=1
PHY_PAGE_REG=22
PHY_SPECIFIC_STATUS_REG=17
PHY_PRBS_ERROR_COUNTER_LSB_REG=24
PHY_PRBS_ERROR_COUNTER_MSB_REG=25

XCVR_STA_OFFSET=0x44
STATUS_VECTOR_MASK=0x1FFFE0
PHY_SPECIFIC_STATUS_MASK=0xEC20

./artix7fpga -init

echo "setting up PHY mode"
./artix7fpga -serdes $CONFIG_PHY_MODE

echo "setting up PHY external loopback"
./artix7fpga -serdes $CONFIG_PHY_STUB_TEST $ENABLE
sleep 1
echo "enable auto-negotiation for the link"
./artix7fpga -serdes $AN_ENABLE
sleep 1
# check the result of auto-negotiation: must be 1Gbps
./artix7fpga -mdiowr $PHY_PAGE_REG $PHY_PAGE_1
p0=$(./artix7fpga -mdiord $PHY_SPECIFIC_STATUS_REG)
p1=$(./artix7fpga -xcvrrd $XCVR_STA_OFFSET)
if [[ $(( p0 & PHY_SPECIFIC_STATUS_MASK )) -ne 0xAC20 ]]; then
    echo "PHY status register: $(( p0 & PHY_SPECIFIC_STATUS_MASK )), expected: 0xAC20"
    echo "TRANSCEIVER PHY INTERFACE TEST FAILED -- auto-negotiation failed"
    exit 1
fi
if [[ $(( p1 & STATUS_VECTOR_MASK )) -ne $(( 0x388B << 5 )) ]]; then
    echo "transceiver status vector: $(( p1 & STATUS_VECTOR_MASK )), expected: $(( 0x388B << 5 ))"
    echo "TRANSCEIVER PHY INTERFACE TEST FAILED -- auto-negotiation failed"
    exit 1
fi

echo "TRANSCEIVER RJ45 port link is up"
if [[ $1 != "PRBS" ]]; then
    exit 0
fi

# first do pkt test on PHY external loopback
echo "enable pkt checker on PHY"
./artix7fpga -serdes $CONFIG_PHY_PKT_CHECKER $ENABLE
sleep 1

echo "enable pkt generator on PHY to generate non-error pkt"
./artix7fpga -serdes $CONFIG_PHY_PKT_GENERATOR $ENABLE $NON_ERR_PKT_BURST $PKT_PAYLOAD $PKT_LEN $NON_ERR_PKT
sleep 1

echo "read pkt counter on PHY"
output=$(./artix7fpga -serdes $PHY_PKT_CHECKER_READ_COUNTER)
echo $output
if [[ $output != "pkt counter: $NON_ERR_PKT_BURST, CRC error counter: 0" ]]; then
    echo "TRANSCEIVER PHY INTERFACE TEST FAILED -- packet counter not expected, result: $output"
    exit 1
fi

echo "enable pkt generator on PHY to generate error pkt"
./artix7fpga -serdes $CONFIG_PHY_PKT_GENERATOR $ENABLE $ERR_PKT_BURST $PKT_PAYLOAD $PKT_LEN $ERR_PKT
sleep 1

echo "read pkt counter on PHY"
output=$(./artix7fpga -serdes $PHY_PKT_CHECKER_READ_COUNTER)
echo $output
if [[ $output != "pkt counter: $((NON_ERR_PKT_BURST + ERR_PKT_BURST)), CRC error counter: $ERR_PKT_BURST" ]]; then
    echo "TRANSCEIVER PHY INTERFACE TEST FAILED -- packet counter not expected, result: $output"
    exit 1
fi

echo "disable pkt generator on PHY"
./artix7fpga -serdes $CONFIG_PHY_PKT_GENERATOR $DISABLE
sleep 1

echo "disable pkt checker on PHY"
./artix7fpga -serdes $CONFIG_PHY_PKT_CHECKER $DISABLE
sleep 1

# next run the xcvr->PHY PRBS test
echo "start PRBS generator on transceiver"
./artix7fpga -serdes $PRBS_GEN_START $DEV_XCVR $PRBS_31 $TX_POLARITY_NO_INVERT $NO_FORCE_ERR
echo "start PRBS checker on PHY"
# use PRBS_NO_LOCK_BEFORE_COUNTING in checker because if use lock before counting, when the counters are 0,
# we don't know if there's really no error or if PRBS is not locked at all (in this case counter is also 0)
./artix7fpga -serdes $PRBS_CHECKER_START $DEV_PHY $PRBS_31 $RX_POLARITY_NO_INVERT $PRBS_NO_LOCK_BEFORE_COUNTING
sleep 1
echo "read PRBS error counter on PHY"
output=$(./artix7fpga -serdes $PRBS_ERR_READ $DEV_PHY)
echo $output
if [[ $output != *"MSB: 0x0, LSB: 0x0"* ]]; then
    echo "clear PRBS error counter on PHY"
    ./artix7fpga -serdes $PRBS_ERR_CLEAR $DEV_PHY
else
    echo "error counter should not be zero before being cleared"
    exit 1
fi
echo "run PRBS for 60 seconds..."
sleep 60
echo "read PRBS error counter on PHY"
./artix7fpga -mdiowr $PHY_PAGE_REG $PHY_PAGE_1
err_cnt_lsb=$(./artix7fpga -mdiord $PHY_PRBS_ERROR_COUNTER_LSB_REG)
err_cnt_msb=$(./artix7fpga -mdiord $PHY_PRBS_ERROR_COUNTER_MSB_REG)
echo "err_cnt_msb=$err_cnt_msb"
echo "err_cnt_lsb=$err_cnt_lsb"
err_cnt=$(((err_cnt_msb << 16) + err_cnt_lsb))
echo "err_cnt=$err_cnt"

echo "stop PRBS generator on transceiver"
./artix7fpga -serdes $PRBS_GEN_STOP $DEV_XCVR
echo "stop PRBS checker on PHY"
./artix7fpga -serdes $PRBS_CHECKER_STOP $DEV_PHY

if [[ $err_cnt > 3 ]]; then
    echo "TRANSCEIVER PHY INTERFACE TEST FAILED -- TRANSCEIVER to PHY PRBS error counter $err_cnt > 3"
    exit 1
fi

echo "TRANSCEIVER PHY INTERFACE TEST PASSED"
exit 0