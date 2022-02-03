#!/bin/bash
Help()
{
   echo "Fetch mfg log and generate diag FA"
   echo
   echo "Usage: $0 [options]"
   echo "options:"
   echo "-c, --card        Card type"
   echo "-s, --stage       Stage(s), comma separated"
   echo "-f, --faopt       FA option: first/last/all"
   echo "-l, --snfile      SN file"
   echo "-d, --logdir      Directory to store logs"
   echo "-t, --testname    Test name (optional parameter to only parse this particular test name)"
   echo "-m, --mfgerrcode  Mfg err code (optional parameter to only parse this particular MFG err code)"
   echo "-h, --help        Print this help"
   echo
}
card_type=
stage=
fa_opt=
sn_file=
log_dir=
test_name=
mfg_err_code=
cwd=$(pwd)

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    #-------------
    -c|--card)
    card_type="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -s|--stage)
    stage="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -f|--faopt)
    fa_opt="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -l|--snfile)
    sn_file="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -d|--logdir)
    log_dir="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -t|--testname)
    test_name="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -m|--mfgerrcode)
    mfg_err_code="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -h|--help)
    Help
    exit
    ;;
    #-------------
    *)    # unknown option
    echo "Unknown option $key"
    Help
    exit
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

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
echo $fa_opt
if [ -z "$fa_opt" ]; then
    echo "Option -f not specified"
    Help
    exit
fi
echo $log_dir
if [ -z "$log_dir" ]; then
    echo "Option -d not specified, using default dir name mfg_log"
    log_dir="mfg_log"
fi

card_type=$(echo $card_type | awk '{print toupper($0)}')
echo $card_type
stage=$(echo $stage | awk '{print toupper($0)}')
echo $stage
fa_opt=$(echo $fa_opt | awk '{print toupper($0)}')
echo $fa_opt

to_location_top="/home/mfg/mfg_diag_fa/scripts/"
to_location=$to_location_top
cd $to_location
#dir_name=$(date +%Y%m%d_%H%M%S)
dir_name=$log_dir
rm -rf $to_location_top/$dir_name
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

# copy logs
while read -r sn; do
    echo "SN is $sn"
    if [ -d $from_location/$sn ]; then
        cp -r $from_location/$sn $to_location/$stage/
    else
        echo "log for SN $sn stage $stage does not exist"
    fi
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

parse_result="parse_result_$(date +%m%d%Y_%H%M%S).xlsx"
echo "runnning the parse script, output is $parse_result"
cp $to_location_top/mfg_parse.pl $to_location
cd $to_location
./mfg_parse.pl $fa_opt $parse_result $test_name $mfg_err_code

cp $to_location/$parse_result $to_location_top/../
echo the temporary dir: $to_location_top$dir_name can be removed
#rm -rf $to_location_top/$dir_name
