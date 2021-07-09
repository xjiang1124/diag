#!/bin/bash


#    VID = 255 – (1.52- (1.6- (ROV-2)*0.00625)/0.005

function readV {
	vout=$(./taorfpga i2c 0 3 0x60 w 0x21 r 2 | grep RD | awk '{print $2}')
	vboot=$(./taorfpga i2c 0 3 0x60 w 0xDB r 1 | grep RD | awk '{print $2}')
	voutValue=$(awk "BEGIN {print ($vout-255.0)*0.005+1.52}")
	vbootValue=$(awk "BEGIN {print ($vboot-255.0)*0.005+1.52}")
	echo "vout = $voutValue [$vout],  vboot=$vbootValue [$vboot]"
}

function  convert {
	rovSDK=$(echo $rovSDK | sed 's/0x//')
	rovSDKDec=$(printf "%d" 0x$rovSDK)
	rovSDKDec=$(($rovSDKDec-2))
	Voltage=$(awk "BEGIN {print 1.6-$rovSDKDec*0.00625}")
	ROV=$Voltage

	VIDf=$(awk "BEGIN {print 255-(1.52-$Voltage)/0.005}")
	VID=$(printf "0x%x" $VIDf)

	echo "ROV is $ROV [$rovSDK],  new VID is $VID"
	if awk 'BEGIN {exit !('$ROV' >= '1.00')}'; then
		echo "Error: ROV must be in the range of 0.75V ~ 1.00V"
	elif awk 'BEGIN {exit !('$ROV' <='0.75')}'; then
		echo "Error: ROV must be in the range of 0.75V ~ 1.00V"
	fi
}

function program  {
	#SET VID
	./taorfpga i2c 0 3 0x60 w 0x00 0x00 > /dev/null
	./taorfpga i2c 0 3 0x60 w 0x21 $VID 0x00 > /dev/null
	./taorfpga i2c 0 3 0x60 w 0xDB $VID > /dev/null
	./taorfpga i2c 0 3 0x60 w 0x11 > /dev/null
}

rovSDK=$2
if [ x$1 == "xread" ] ; then
	readV;
	exit;
elif [ x$1 == "xconvert" ] ; then
	convert;
	exit;
elif [ x$1 == "xprogram" ] ; then
	convert;
	readV;
	echo "programming"
	program;
	readV;
	exit
else
	echo "need VID from Broadcom shell"
	echo "$0 [read|convert|program] VID"
	echo "	read    : read programmed VID"
	echo "	convert : convert Broadcom VID to TI VID"
	echo "	program : program VID after conversion"
	exit
fi
