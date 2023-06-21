#!/bin/bash

hash()
{
    local algo=$1
    case "$algo" in
    md5)    md5sum | awk '{ print $1 }'; ;;
    sha256) sha256sum | awk '{ print $1 }'; ;;
    sha512) sha512sum | awk '{ print $1 }'; ;;
    *) fatal "hash: invalid algo $algo"; ;;
    esac
}

hash_algo=sha512

# check fw pointers
echo -n  "Checking FW Pointers..."
ptrs_want_hash=ded43f3a3634de130bdeb1f8636e5fa62bca8f0a2fc3fcd87cb586aca250e3c03c197e5e40ccaece803c321752eab7224962610029a758ea5903e8119d9dd25b
ptrs_got_hash=`dd if=/dev/mtd0 bs=1 count=16 status=none | hash $hash_algo 2>/dev/null`

if [ $ptrs_want_hash != $ptrs_got_hash ]; then
	echo
	echo "FW Pointers are not programmed correctly"
	echo "FAILED"
	exit 1
fi

echo "OK"

# check pentrust fw partition and it's hash

esec_fw_sizes=(36936 42596)
esec_fw_hashs=(1c5a14f990c06155dd6fb6530e81b48e0b087155f573231a530f2a5a91b53e9644ff1253fbfbd2dfebd7a7fca2d67a92d0de17e52925b5312af2560af031598b 57824d584bb3baa8b2f16200a62d1a39f1fb6eb33570ec21a593d576f8c9e761efb424b7c9c8b488a981dce246dceac2fcbad58d24b59ab11c851fe909fc2605)
esec_part1_offset=$(( 16#10000 ))
esec_part2_offset=$(( 16#30000 ))

part_hash()
{
	local off=$1 size=$2 part_hash

	part_hash=`dd if=/dev/mtd0 bs=1 skip=$off count=$size status=none | hash $hash_algo 2>/dev/null`

	echo $part_hash
}

esec_fw0_good=0
echo -n "Checking first pentrust firmware partition..."
for i in ${!esec_fw_sizes[@]}; do
    part1_hash=`part_hash $esec_part1_offset ${esec_fw_sizes[$i]}`

    if [ ${esec_fw_hashs[$i]} == $part1_hash ]; then
	esec_fw0_good=1
	break
    fi
done
if [ $esec_fw0_good -eq 0 ]; then
	echo "FAILED"
	echo "        Does not contain valid pentrust firmware image in the first partition."
else
        echo "OK"
fi

#echo "want $esec_fw_hash"
#echo "got  $part1_hash"

echo -n "Checking second pentrust firmware partition..."
esec_fw1_good=0
for i in ${!esec_fw_sizes[@]}; do
    part2_hash=`part_hash $esec_part2_offset ${esec_fw_sizes[$i]}`

    if [ ${esec_fw_hashs[$i]} == $part1_hash ]; then
         esec_fw1_good=1
	 break
    fi
done

if [ $esec_fw1_good -eq 0 ] ; then
	echo "FAILED"
	echo "       Does not contain valid pentrust firmware image in the second partition."
else
        echo "OK"
fi

# echo "want $esec_fw_hash"
# echo "got  $part2_hash"

if [ $esec_fw0_good -eq 0 -a $esec_fw1_good -eq 0 ]; then
	echo "Both pentrust firmware partitions are bad. Exiting..."
	echo "FAILED"
	exit 1
fi

# check bootsec partition (or bl1) and it's hash.
# (boot_nonsec bl1-v1 bl1-v2 bl1-v3 bl1-v4)

boot_ns_fw_sizes=(1088 57341 54053 54165 54165)
boot_ns_fw_hashs=(d68d89c842256221019b98c7fb39bf69e45c3abc72cf6a5d7115cedcced6e1099137c8a858f8faa6e777162e160711f7a8c5bf94654b0c037096e9fffca8285a 3b662a19397855b6f4f7aa99e34bbb3f43731c4b5751992a0b1e611d82eb9e959ae57b717fa6bbe7e30767d25569939d8cc47eb7e1dc5e248b9096a1ff505b73 367b48253365d1762b47da3653e43199995259e4d9fbda8f342753ea186b3a2e28ea2629b86478503c879d1c38c0bc02ecee5b6767b565cdda418174127264b7 77ff218985f6cfcbb0f12dda5fbb94a81f4c53d39eccab0aea5e034ee052df8b58a0fb2b16dd8be898d3abee520f07e7ebcc4838363956d2db169b80975170e6 e371ad22c9990c5be3be9f533e3ec72bfa0c81f5ac90636866e607e09036d8bf651e30fe44ce601c596ebfafd668f8d21612315c8763c46a6dfa7f4e05de2755)
boot_ns_part1_offset=$(( 16#50000 ))
boot_ns_part2_offset=$(( 16#70000 ))

echo -n "Checking first boot-nonsec/bl1 partition..."
boot_ns0_good=0

for i in ${!boot_ns_fw_sizes[@]}; do
    part1_hash=`part_hash $boot_ns_part1_offset ${boot_ns_fw_sizes[$i]}`

    if [ ${boot_ns_fw_hashs[$i]} == $part1_hash ]; then
         boot_ns0_good=1
	 break
    fi
done

if [ $boot_ns0_good -eq 0 ] ; then
	echo "FAILED"
        echo "        Does not contain valid boot-nonsec/bl1 firmware image in the first partition."
else
        echo "OK"
fi


echo -n "Checking second boot-nonsec/bl1 partition..."
boot_ns1_good=0

for i in ${!boot_ns_fw_sizes[@]}; do
    part2_hash=`part_hash $boot_ns_part2_offset ${boot_ns_fw_sizes[$i]}`

    if [ ${boot_ns_fw_hashs[$i]} == $part2_hash ]; then
         boot_ns1_good=1
         break
    fi
done

if [ $boot_ns1_good -eq 0 ] ; then
	echo "FAILED"
        echo "        Does not contain valid boot-nonsec/bl1 firmware image in the first partition."
else
        echo "OK"
fi

# echo "want $boot_ns_fw_hash"
# echo "got  $part1_hash"

# echo "want $boot_ns_fw_hash"
# echo "got  $part2_hash"

if [ $boot_ns0_good -eq 0 -a $boot_ns1_good -eq 0 ]; then
	echo "\nBoth boot-nonsec firmware partitions are bad. Exiting..."
	echo "FAILED"
	exit 2
fi

echo "SUCCESS"
exit 0
