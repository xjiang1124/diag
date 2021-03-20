/data/nic_util/smbutil -dev=ELB0_ARM -wr -addr=0 -data=0
/data/nic_util/smbutil -dev=ELB0_CORE -rd -addr=0
/data/nic_util/smbutil -dev=ELB0_CORE -rd -mode=w -addr=0xda
/data/nic_util/smbutil -dev=ELB0_CORE -wr -mode=w -addr=0xda -data=0xa055
/data/nic_util/smbutil -dev=ELB0_CORE -rd -mode=w -addr=0xda
/data/nic_util/smbutil -dev=ELB0_CORE -sd -addr=0x11
sleep 1
/data/nic_util/devmgr -status
echo "Ortano2 VRM fix done"
