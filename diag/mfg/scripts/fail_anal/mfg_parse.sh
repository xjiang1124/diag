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
stages=(`echo $stage | sed 's/,/\n/g'`)
for i in "${stages[@]}"
do
    echo "stage=$i"
done

fa_opt=$(echo $fa_opt | awk '{print toupper($0)}')
echo $fa_opt

timestamp=$(date +%m%d%Y_%H%M%S)
missing_log_file="${cwd}/sn_list_missing_log${timestamp}.txt"
rm -f $missing_log_file

to_loc_top="${cwd}/scripts/"
to_loc=$to_loc_top
dir_name=$log_dir
rm -rf ${to_loc_top}${dir_name}
mkdir -p ${to_loc_top}${dir_name}
to_loc+=$dir_name

# generate a file to list SNs with no log
# copy logs
while read -r sn; do
    echo "SN is $sn"
    #declare -A sn_paths
    sn_path_exists=0
    for i in "${stages[@]}"
    do
        echo "stage=$i"
        case $i in
            "DL")
            from_loc="/mfg_log/$card_type/DL/${sn}"
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                #sn_paths[$i] = 1
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
            ;;
            "SWI")
            from_loc="/mfg_log/$card_type/SWI/${sn}"
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                #sn_paths[$i] = 1
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
            ;;
            "P2C")
            from_loc="/mfg_log/$card_type/P2C/${sn}"
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                #sn_paths[$i] = 1
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
            ;;
            "4C-L")
            from_loc="/mfg_log/$card_type/4C/4C-L/${sn}"
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                #sn_paths[$i] = 1
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
            ;;
            "4C-H")
            from_loc="/mfg_log/$card_type/4C/4C-H/${sn}"
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                #sn_paths[$i] = 1
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
            ;;
            *)
            echo "Invalid stage $i"
            exit
            ;;
        esac
    done

    if [ ! $sn_path_exists ]; then
        echo "any log for SN $sn does not exist"
        echo $sn >> $missing_log_file
    fi
done < "${cwd}/${sn_file}"

function run_parse {
    stage=$1
    txt_path=$2
    parse_result="${cwd}/parse_result_${stage}_${timestamp}.xlsx"
    echo "runnning the parse script for stage $stage, output is $parse_result"
    cp $to_loc_top/mfg_parse.pl $to_loc/$card_type
    cd $to_loc/$card_type
    ./mfg_parse.pl $fa_opt $parse_result $txt_path $test_name $mfg_err_code

    # grep each SN in logs_fail.txt
    while read -r sn; do
        echo "SN is $sn"
        if grep -q $sn $to_loc/$card_type/$stage/logs_fail.txt; then
            echo "failure log for SN $sn exists in stage $stage"
        else
            echo "failure log for SN $sn does not exist in stage $stage"
            echo $sn >> $missing_log_file
        fi
    done < "${cwd}/${sn_file}"
}

echo "untar the log files"
# untar
cd $to_loc/$card_type
find ./ -name '*.tar.gz' -exec sh -c 'dir=$(dirname "$0"); tar -xf "${0}" -C "${dir}"; done' {} \;
cd $to_loc/$card_type
for stage in "${stages[@]}"
do
    echo "stage=$stage"
    case $stage in
        "DL")
        if [ -d ./$stage ]; then
            find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP DL Test Complete" > ./$stage/testresult.txt
            run_parse $stage $to_loc/$card_type/$stage
        fi
        ;;
        "SWI")
        if [ -d ./$stage ]; then
            find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP Software Install Test Complete" > ./$stage/testresult.txt
            run_parse $stage $to_loc/$card_type/$stage
        fi
        ;;
        "P2C")
        if [ -d ./$stage ]; then
            find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP Diag Regression Test Complete" > ./$stage/testresult.txt
            run_parse $stage $to_loc/$card_type/$stage
        fi
        ;;
        "4C-L")
        if [ -d ./$stage ]; then
            find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP Diag Regression Test Complete" > ./$stage/testresult.txt
            run_parse $stage $to_loc/$card_type/$stage
        fi
        ;;
        "4C-H")
        if [ -d ./$stage ]; then
            find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP Diag Regression Test Complete" > ./$stage/testresult.txt
            run_parse $stage $to_loc/$card_type/$stage
        fi
        ;;
        *)
        echo "Invalid stage $stage"
        exit
        ;;
    esac
done

#cp $parse_result $to_loc_top/../
echo the temporary dir: $to_loc_top$dir_name can be removed
#rm -rf $to_loc_top/$dir_name
