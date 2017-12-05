# !/bib/bash

reset_line=`grep -in -E "^reset" $1 | awk -F ":" '{print $1}'`

sed -n "1,$reset_line p" $1 > pro_temp
tail -n +$reset_line $1 > ver_temp

#grep -e "^Write" -e "^BlockWrite" -e "^SendByte" pro_temp > naples_53659.img
grep -e "^Read" -e "^BlockRead" -e "^Write" -e "^BlockWrite" -e "^SendByte" pro_temp > pro_temp1
echo "=== READ VERIFY ===" > ver_temp1
grep -e "^Read" -e "^BlockRead" -e "^Write" -e "^BlockWrite" -e "^SendByte" ver_temp >> ver_temp1

cat pro_temp1 ver_temp1 > naples_53659.img
sed -i 's/,0x62,/,/g' naples_53659.img
