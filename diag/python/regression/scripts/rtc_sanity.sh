echo "=== RTC Sanity Check ==="

stop_en="$(smbutil -dev=RTC -rd -addr=0x2E)"
echo "Before RTC reset"
echo $stop_en


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
fi

echo "Resetting RTC"
smbutil -dev=rtc -wr -addr=0x2F -data=0x2C

stop_en="$(smbutil -dev=RTC -rd -addr=0x2E)"
echo "After RTC reset"
echo $stop_en

