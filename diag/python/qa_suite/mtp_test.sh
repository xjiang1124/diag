i2cdetect -y -r 0
mtptest -fan
mtptest -fanspd
devmgr -dev=fan -speed -pct=40
mtptest -fantmp
mtptest -psu
mtptest -vrm
mtptest -mvl
mtptest -wdt
