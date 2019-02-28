rtc_sec_pre="$(smbutil -dev=RTC -rd -addr=0x1 | awk -F ';' '{print $2}')"
echo $rtc_sec_pre

sleep 2

rtc_sec_post="$(smbutil -dev=RTC -rd -addr=0x1 | awk -F ';' '{print $2}')"
echo $rtc_sec_post

if [[ $rtc_sec_pre != $rtc_sec_post ]]
then
    echo "RTC sanity check passed"
else
    echo "RTC sanity check FAILED"
    echo "Resetting RTC"
    cpld -w 0x2F 0x2C
fi

