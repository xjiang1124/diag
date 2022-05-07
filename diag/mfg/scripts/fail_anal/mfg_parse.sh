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

card_type_orig=$card_type
card_type=$(echo $card_type | awk '{print toupper($0)}')
echo $card_type
if [[ ! -d "/mfg_log/${card_type}" ]]; then
    card_type=$card_type_orig
fi
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
existing_log_file="${cwd}/sn_list_existing_log${timestamp}.txt"
rm -f $missing_log_file $existing_log_file

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
            ;;
            "SWI")
            from_loc="/mfg_log/$card_type/SWI/${sn}"
            ;;
            "FST")
            from_loc="/mfg_log/$card_type/FST/${sn}"
            ;;
            "P2C")
            from_loc="/mfg_log/$card_type/P2C/${sn}"
            ;;
            "4C-L")
            from_loc="/mfg_log/$card_type/4C/4C-L/${sn}"
            ;;
            "4C-H")
            from_loc="/mfg_log/$card_type/4C/4C-H/${sn}"
            ;;
            *)
            echo "Invalid stage $i"
            exit
            ;;
        esac
        if [ -d ${from_loc} ]; then
            echo "$from_loc exists"
            sn_path_exists=1
            mkdir -p $to_loc/$card_type/$i
            cp -r $from_loc $to_loc/$card_type/$i/
        else
            echo "$from_loc does not exist"
        fi
    done

    if [ $sn_path_exists -eq 0 ]; then
        echo "any log for SN $sn does not exist"
        echo $sn >> $missing_log_file
    else
        echo $sn >> $existing_log_file
    fi
done < "${cwd}/${sn_file}"

if [ ! -f $existing_log_file ]; then
    exit
fi

function run_parse {
    #stage=$1
    #txt_path=$2
    parse_result="${cwd}/parse_result_${timestamp}_${log_dir}.xlsx"
    echo "runnning the parse script, output is $parse_result"
    #if [ "$stage" == "FST" ]; then
    #    cp $to_loc_top/mfg_parse_fst.pl $to_loc/$card_type/mfg_parse.pl
    #else
    #    cp $to_loc_top/mfg_parse.pl $to_loc/$card_type
    #fi
    cp $to_loc_top/mfg_parse.pl $to_loc/$card_type
    cd $to_loc/$card_type
    ./mfg_parse.pl $fa_opt $parse_result $test_name $mfg_err_code

    # grep each SN in logs_fail.txt
    while read -r sn; do
        echo "SN is $sn"
        for stage in "${stages[@]}"
        do
            if grep -q "${stage}\/$sn" $to_loc/$card_type/logs_fail.txt; then
                echo "failure log for SN $sn exists in stage $stage"
            else
                echo "failure log for SN $sn does not exist in stage $stage"
                echo $sn >> $missing_log_file
            fi
        done
    done < "${existing_log_file}"
}

echo "untar the log files"
# untar
cd $to_loc/$card_type
#rm ./testresult.txt
find ./ -name '*.tar.gz' -exec sh -c 'echo $0; dir=$(dirname "$0"); tar -xf "${0}" -C "${dir}"; done' {} \;
cd $to_loc/$card_type
while read -r sn; do
    #echo "SN is $sn"
    for stage in "${stages[@]}"
    do
        #echo "stage=$stage"
        case $stage in
            "DL")
            if [ -d ./$stage ]; then
                #find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP DL Test Complete" > ./$stage/testresult.txt
                find ./$stage -name "mtp_test.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt
            fi
            ;;
            "SWI")
            if [ -d ./$stage ]; then
                #find ./$stage -name "mtp_test.log" | xargs grep -anH -A11 "MTP Software Install Test Complete" > ./$stage/testresult.txt
                find ./$stage -name "mtp_test.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt
            fi
            ;;
            "FST")
            if [ -d ./$stage ]; then
                find ./$stage -name "test_fst.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt
            fi
            ;;
            "P2C")
            if [ -d ./$stage ]; then
                find ./$stage -name "mtp_test.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt
            fi
            ;;
            "4C-L")
            if [ -d ./$stage ]; then
                find ./$stage -name "mtp_test.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt
            fi
            ;;
            "4C-H")
            if [ -d ./$stage ]; then
                find ./$stage -name "mtp_test.log" | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> ./testresult.txt

            fi
            ;;
            *)
            echo "Invalid stage $stage"
            exit
            ;;
        esac
    done
done < "../../../${sn_file}"
run_parse

#cp $parse_result $to_loc_top/../
rm -f ${existing_log_file}
echo "The parsing result is $parse_result"
echo the temporary dir: $to_loc_top$dir_name can be removed
#rm -rf $to_loc_top/$dir_name
