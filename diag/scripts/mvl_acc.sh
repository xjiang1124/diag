#!/bin/bash
set -x
cnt=0
p6=$(cpldapp -mdiord 0x3 0x10)
p7=$(cpldapp -mdiord 0x3 0x10)
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
    cpldapp -mdiowr 0x0D 0x1B $p0
    cpldapp -mdiowr 0x0E 0x1B $p1
    cpldapp -mdiowr 0x0F 0x1B $p2
    p3=$(cpldapp -mdiord 0xD 0x1B)
    p4=$(cpldapp -mdiord 0xE 0x1B)
    p5=$(cpldapp -mdiord 0xF 0x1B)
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

for cnt in {0..6}
do
    cpldapp -mdiowr 0x0F $((cnt+0x10))  $p0
done

for cnt in {0..6}
do
    p3=$(cpldapp -mdiord 0x0F $((cnt+0x10)))
    if [[ $p0 != $((p3)) ]]; then
        echo $cnt $p0 $((p3))
        echo "MVL ACC TEST FAILED - ADDRESS ERROR"
        exit 1
    fi
done

for cnt in {0..6}
do
    cpldapp -mdiowr 0x0F $((cnt+0x10)) 0x9100
done

echo "MVL ACC TEST PASSED"
