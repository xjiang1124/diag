log_path="/data/nic_arm/nic/asic_src/ip/cosim/tclsh/snake.log"
#log_path="./snake.log"

echo $1

sig_found="$(grep "Snake Done" $log_path | wc | awk -F ' ' '{print $1}')"
echo $sig_found

if [[ $sig_found == "1" || $sig_found == "2" ]]
then
    echo "TEST Finished"
else
    echo "TEST Not Done"
    exit 0
fi

err_count="$(grep "ERROR :" $log_path | wc | awk -F ' ' '{print $1}')"
echo "err_count: $err_count"
if [[ $err_count != $1 ]]
then
    echo "TEST Failed"
else
    echo "TEST Passed"
fi

sync
sync
sync

