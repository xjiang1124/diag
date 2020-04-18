# !/bin/bash

echo "scp $1 to slot $2:$3"
ip=$(expr 100 + $2)

sshpass -p pen123 scp -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $1 root@10.1.1.$ip:$3

