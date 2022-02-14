lsof | grep usb | tail -1 | awk '{print $2}' | xargs kill -9
