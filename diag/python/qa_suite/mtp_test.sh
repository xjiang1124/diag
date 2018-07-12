# Use this command to turn on all UUT 12v
# Need this to show PSU DC ok is good
turn_on_uut.sh 1 0

i2cdetect -y -r 0
mtptest -fan
mtptest -fanspd
devmgr -dev=fan -speed -pct=40
mtptest -fantmp
mtptest -psu
mtptest -vrm
mtptest -mvl
mtptest -wdt
mtptest -present
mtp_pcie_test.sh
mtp_pcs_test.sh
