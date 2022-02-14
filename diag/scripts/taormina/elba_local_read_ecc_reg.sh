#!/bin/bash

/nic/bin/capview << EOF
secure on
read 0x30520020
read 0x305a0020
read 0x30530464
read 0x30530468
read 0x3053046C
read 0x30530470
read 0x30530474
read 0x305B0464
read 0x305B0468
read 0x305B046C
read 0x305B0470
read 0x305B0474

EOF
