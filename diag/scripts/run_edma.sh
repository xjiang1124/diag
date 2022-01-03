# ! /bin/bash

cd /data/nic_util/edma_test/

./edma_test.sh | tee /data/nic_util/edma_test.log

echo "EDMA test done"
sleep 3
echo "Checking EMDA result"

pass_cnt=$(grep PASS /data/nic_util/edma_test.log | wc -l)
echo "pass_cnt $pass_cnt"

if [[ $pass_cnt == "21" ]]
then
    echo "EDMA TEST PASSED"
    echo "EDMA TEST PASSED"
else
    echo "EDMA TEST FAILED"
    echo "EDMA TEST FAILED"
fi

