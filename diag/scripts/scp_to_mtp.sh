# !/bin/bash

echo "scp slot $1 file: $2 to MTP location $3"
ip=$(expr 100 + $1)

sshpass -p pen123 rsync -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@10.1.1.$ip:$2 $3

