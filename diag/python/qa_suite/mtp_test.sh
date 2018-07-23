# Use this command to turn on all UUT 12v
# Need this to show PSU DC ok is good
devmgr -dev=fan -speed -pct=75
turn_on_uut.sh 1 0

sensors
i2cdetect -y -r 0
mtptest -fan
mtptest -fanspd
devmgr -dev=fan -speed -pct=75
mtptest -fantmp
mtptest -psu
mtptest -vrm
mtptest -mvl
mtptest -wdt
mtptest -present
mtp_pcie_test.sh
mtp_pcs_test.sh
sensors
