# !/bin/bash

echo "scp $1 to $2"

scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $1 $2

