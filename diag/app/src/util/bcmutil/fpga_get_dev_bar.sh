# Copyright (C) 2016-2022 Pensando Systems
#!/bin/bash

echo -n "0x" > /tmp/fpgabars
lspci -s 12:00.0 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars
echo -n "0x" >> /tmp/fpgabars
lspci -s 12:00.1 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars
echo -n "0x" >> /tmp/fpgabars
lspci -s 12:00.2 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars
echo -n "0x" >> /tmp/fpgabars
lspci -s 12:00.3 -v | grep Memory | awk '{print $3}' >> /tmp/fpgabars

