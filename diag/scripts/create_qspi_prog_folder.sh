#!/bin/bash
new_folder=$1
image_rev=$2

mkdir -p $new_folder
cd $new_folder
mkdir -p a35_gold
tar xf /vol/builds/hourly/${image_rev}/release-artifacts/gold_rudra/naples_salina_a35_dpu_gold.tar -C a35_gold salina/zephyr.img salina/ubootg.img salina/boot0.img
mkdir -p n1_gold
tar xf /vol/builds/hourly/${image_rev}/release-artifacts/gold_rudra/naples_goldfw_salina.tar -C n1_gold salina/ubootg.img salina/kernel.img
mkdir a35_main
tar xf /vol/builds/hourly/${image_rev}/naples_salina_a35_dpu_ddr.tar -C a35_main salina/zephyr.img salina/uboota.img salina/device_config.dtb salina/boot0.img salina/ubootb.img
mkdir n1_main
tar xf /vol/builds/hourly/${image_rev}/sw-athena-salina/nic/dsc_fw_salina_${image_rev}.tar -C n1_main salina/uboota.img salina/boot0.img salina/ubootb.img
echo "#!/bin/bash" > qspi_prog.sh
echo "slot=(\$1)" >> qspi_prog.sh
echo "declare -a addr=(0x00100000 \\" >> qspi_prog.sh
echo "                 0x06800000 \\" >> qspi_prog.sh
echo "                 0x07000000 \\" >> qspi_prog.sh
echo "                 0x07800000 \\" >> qspi_prog.sh
echo "                 0x08000000 \\" >> qspi_prog.sh
echo "                 0x009e0000 \\" >> qspi_prog.sh
echo "                 0x00140000 \\" >> qspi_prog.sh
echo "                 0x06350000 \\" >> qspi_prog.sh
echo "                 0x01f50000 \\" >> qspi_prog.sh
echo "                 0x0cc70000 \\" >> qspi_prog.sh
echo "                 0x0d070000 \\" >> qspi_prog.sh
echo "                 0x02350000 \\" >> qspi_prog.sh
echo "                 0xbc10000 \\" >> qspi_prog.sh
echo "                 0xbc30000)" >> qspi_prog.sh
echo "declare -a image=(a35_main/salina/boot0.img \\" >> qspi_prog.sh
echo "                  a35_main/salina/uboota.img \\" >> qspi_prog.sh
echo "                  a35_main/salina/ubootb.img \\" >> qspi_prog.sh
echo "                  a35_gold/salina/ubootg.img \\" >> qspi_prog.sh
echo "                  a35_main/salina/zephyr.img \\" >> qspi_prog.sh
echo "                  a35_main/salina/zephyr.img \\" >> qspi_prog.sh
echo "                  a35_gold/salina/zephyr.img \\" >> qspi_prog.sh
echo "                  n1_main/salina/boot0.img \\" >> qspi_prog.sh
echo "                  n1_gold/salina/ubootg.img \\" >> qspi_prog.sh
echo "                  n1_main/salina/uboota.img \\" >> qspi_prog.sh
echo "                  n1_main/salina/ubootb.img \\" >> qspi_prog.sh
echo "                  n1_gold/salina/kernel.img \\" >> qspi_prog.sh
echo "                  a35_main/salina/device_config.dtb \\" >> qspi_prog.sh
echo "                  a35_main/salina/device_config.dtb)" >> qspi_prog.sh
echo " " >> qspi_prog.sh
echo "turn_on_slot.sh off \$slot" >> qspi_prog.sh
echo "sleep 3" >> qspi_prog.sh
echo "turn_on_slot.sh on \$slot 0 0" >> qspi_prog.sh
echo "sleep 3" >> qspi_prog.sh
echo " " >> qspi_prog.sh
echo "for i in \${!addr[*]}" >> qspi_prog.sh
echo "do" >> qspi_prog.sh
echo "    echo \"Programming \${image[\$i]} to address \${addr[\$i]}\"" >> qspi_prog.sh
echo "    fpgautil flash \$slot 1 writefile \${addr[\$i]} \${image[\$i]}" >> qspi_prog.sh
echo "    if [ \$? != 0 ]" >> qspi_prog.sh
echo "    then" >> qspi_prog.sh
echo "    echo \"Programming \${image[\$i]} to address \${addr[\$i]} FAILED\"" >> qspi_prog.sh
echo "    exit 1" >> qspi_prog.sh
echo "    fi" >> qspi_prog.sh
echo "done" >> qspi_prog.sh
chmod 755 qspi_prog.sh
