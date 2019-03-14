log_path="/data/nic_arm/nic/asic_src/ip/cosim/tclsh/snake.log"
#log_path="./snake.log"

sig_found="$(grep "Snake Done" $log_path | wc | awk -F ' ' '{print $1}')"
echo $sig_found

if [[ $sig_found == "1" || $sig_found == "2" ]]
then
    echo "Test Finished"
else
    echo "Test Not Done"
    exit 0
fi

err_count="$(grep "ERROR :" $log_path | wc | awk -F ' ' '{print $1}')"
echo "err_count: $err_count"
if [[ $err_count != "3" ]]
then
    echo "Snake Failed"
else
    echo "Snake Passed"
fi

sync
sync
sync

