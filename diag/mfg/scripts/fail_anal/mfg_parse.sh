#!/bin/bash
Help()
{
   echo "Fetch mfg log and generate diag FA"
   echo
   echo "Syntax: mfg_parse.sh [-c|s|f|l|h]"
   echo "options:"
   echo "c     card_type"
   echo "s     stage"
   echo "f     FA option: first/last/all"
   echo "l     SN file"
   echo "h     print this help"
   echo
}
card_type=
stage=
fa_option=
sn_file=
cwd=$(pwd)

while getopts c:s:f:l:h name
do
    case $name in
    c)
        card_type="$OPTARG";;
    s)
        stage="$OPTARG";;
    f)
        fa_option="$OPTARG";;
    l)
        sn_file="$OPTARG";;
    h)
        Help
        exit
        ;;
    ?)
        echo "Error: Invalid option $name"
        Help
        exit
        ;;
    esac
done

echo $card_type
if [ -z "$card_type" ]; then
    echo "Option -c not specified"
    Help
    exit
fi
echo $sn_file
if [ -z "$sn_file" ]; then
    echo "Option -l not specified"
    Help
    exit
fi
echo $stage
if [ -z "$stage" ]; then
    echo "Option -s not specified"
    Help
    exit
fi
echo $fa_option
if [ -z "$fa_option" ]; then
    echo "Option -f not specified"
    Help
    exit
fi

card_type=$(echo $card_type | awk '{print toupper($0)}')
echo $card_type
stage=$(echo $stage | awk '{print toupper($0)}')
echo $stage
fa_option=$(echo $fa_option | awk '{print toupper($0)}')
echo $fa_option
to_location_top="/home/mfg/mfg_diag_fa/scripts/"
to_location=$to_location_top
cd $to_location
dir_name=$(date +%Y%m%d_%H%M%S)
mkdir -p $dir_name
to_location+=$dir_name
cd $dir_name
mkdir -p "$card_type"/"$stage"
to_location+="/$card_type/"
# copy logs one by one
if [[ "$stage" == "4C-H" ]] || [[ "$stage" == "4C-L" ]]; then
    stage_dir="4C/$stage"
    echo $stage_dir
else
    stage_dir=$stage
fi
from_location="/mfg_log/$card_type/$stage_dir"

while read -r sn; do
    echo "SN is $sn"
    cp -r $from_location/$sn $to_location/$stage/
done < "${cwd}/${sn_file}"
echo $to_location
echo "untar the log files"
# untar
cd $card_type
find ./ -name '*.tar.gz' -exec sh -c 'dir=$(dirname "$0"); tar -xf "${0}" -C "${dir}"; done' {} \;
#grep
find ./ -name "mtp_test.log" | xargs grep -an -A11 "MTP DL Test Complete" > $to_location/testresult.txt
find ./ -name "mtp_test.log" | xargs grep -an -A11 "MTP Software Install Test Complete" >> $to_location/testresult.txt
find ./ -name "mtp_test.log" | xargs grep -an -A11 "MTP Diag Regression Test Complete" >> $to_location/testresult.txt

echo "runnning the parse script"
cp $to_location_top/mfg_parse.pl $to_location
cd $to_location
./mfg_parse.pl $fa_option

cp $to_location/parse_result.xlsx $to_location_top/../
echo the temporary dir: $to_location_top$dir_name can be removed
#rm -rf $to_location_top/$dir_name
