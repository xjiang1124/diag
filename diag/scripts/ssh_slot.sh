# !/bin/bash

echo "ssh to slot $1"
slot=$((100+$1))

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@10.1.1.$slot

