#!/bin/bash
cnt=0
p6=$(./xo3dcpld -mdiord 0x3 0x10)
p7=$(./xo3dcpld -mdiord 0x3 0x10)
if [[ $p7 != "0x1152" ]]; then
    echo $p6 $p7
    echo "MVL ACC TEST FAILED - ID ERROR"
    exit 1
fi

for cnt in {1..100}
do
    cnt=$((cnt+1))
    p0=$((RANDOM%256))
    p1=$((RANDOM%256))
    p2=$((RANDOM%256))
    ./xo3dcpld -mdiowr 0x0D 0x1B $p0
    ./xo3dcpld -mdiowr 0x0E 0x1B $p1
    ./xo3dcpld -mdiowr 0x0F 0x1B $p2
    p3=$(./xo3dcpld -mdiord 0xD 0x1B)
    p4=$(./xo3dcpld -mdiord 0xE 0x1B)
    p5=$(./xo3dcpld -mdiord 0xF 0x1B)
    if [[ $p0 != $((p3)) ]]; then
        echo $cnt $p0 $p1 $p2 $((p3)) $((p4)) $((p5)) 
        echo "MVL ACC TEST FAILED - REG 0x0D ERROR"
        exit 1
    fi
    if [[ $p1 != $((p4)) ]]; then
        echo $cnt $p0 $p1 $p2 $((p3)) $((p4)) $((p5)) 
        echo "MVL ACC TEST FAILED - REG 0x0E ERROR"
        exit 1
    fi
    if [[ $p2 != $((p5)) ]]; then
        echo $cnt $p0 $p1 $p2 $((p3)) $((p4)) $((p5)) 
        echo "MVL ACC TEST FAILED - REG 0x0F ERROR"
        exit 1
    fi
done

for cnt in {1..7}
do
    ./xo3dcpld -mdiowr 0x0F $((cnt+0x10))  $p0
done

for cnt in {1..7}
do
    p3=$(./xo3dcpld -mdiord 0x0F $((cnt+0x10)))
    if [[ $p0 != $((p3)) ]]; then
        echo $cnt $p0 $((p3))
        echo "MVL ACC TEST FAILED - ADDRESS ERROR"
        exit 1
    fi
done

for cnt in {1..7}
do
    ./xo3dcpld -mdiowr 0x0F $((cnt+0x10)) 0x9100
done

echo "MVL ACC TEST PASSED"
