#!/bin/bash
Help()
{
   echo "Fetch mfg log and generate diag FA"
   echo
   echo "Usage: $0 [options]"
   echo "options:"
   echo "-c, --card        Card type"
   echo "-s, --stage       Stage(s), comma separated"
   echo "-f, --faopt       FA option: first/last/all/first_run/last_run/all_run"
   echo "-l, --snfile      SN file"
   echo "-d, --dlogdir     Directory to store logs"
   echo "-e, --slogdir     Directory where original logs are stored"
   echo "-r, --remote      Mfg logs are stored remotely"
   echo "-k, --keep        Keep extracted logs after running parser"
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
src_log_dir=
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
    -d|--dlogdir)
    log_dir="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -e|--slogdir)
    src_log_dir="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -r|--remote)
    is_remote=1
    shift # past argument
    ;;
    #-------------
    -k|--keep)
    keep_log=1
    shift # past argument
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
echo $src_log_dir
if [ -z "$src_log_dir" ]; then
    echo "Option -e not specified, using default dir name mfg_log"
    src_log_dir="mfg_log"
fi
if [ -z "$is_remote" ]; then
    echo "Option -r not specified, copying logs locally"
fi
if [ -z "$keep_log" ]; then
    echo "Option -k not specified, delete log dir after running parser"
fi

# limit the number of SNs to parse
num_sn=$(cat "$sn_file" | wc -l)
echo "num_sn=$num_sn"
#if [ "$num_sn" -gt 100 ]; then
#    echo "Please only parse up to 100 SNs at a time"
#    exit
#fi

card_type_orig=$card_type
card_type=$(echo $card_type | awk '{print toupper($0)}')
echo $card_type
if [ ! $is_remote ]; then
    if [[ ! -d "/${src_log_dir}/${card_type}" ]]; then
        card_type=$card_type_orig
    fi
else
    if sshpass -p 'pensando' ssh mfg@hw-mftg-data '[ ! -d "/${src_log_dir}/${card_type}" ]'; then
        card_type=$card_type_orig
    fi
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
passing_log_file="${cwd}/sn_list_passing_log${timestamp}.txt"
rm -f $missing_log_file $existing_log_file $passing_log_file

function run_parse {
    local sn=$1
    local type=$2
    echo "In run_parse"
    if [[ $type =~ "NAPLES" ]]; then
        echo "Capri card"
        cp $to_loc_top/mfg_parse_capri.pl $to_loc/$card_type/mfg_parse.pl
    else
        cp $to_loc_top/mfg_parse.pl $to_loc/$card_type
    fi
    cd $to_loc/$card_type
    ./mfg_parse.pl $fa_opt $card_type $test_name $mfg_err_code
}

function run_convert {
    #stage=$1
    #txt_path=$2
    parse_result="${cwd}/parse_result_${timestamp}_${log_dir}.xlsx"
    echo "Done with runnning the parse script, output is $parse_result"
    cp $to_loc_top/convert.pl $to_loc/$card_type
    cd $to_loc/$card_type
    ./convert.pl $fa_opt $parse_result $missing_log_file $passing_log_file
}

to_loc_top="${cwd}/scripts/"
to_loc=$to_loc_top
dir_name=$log_dir
rm -rf ${to_loc_top}${dir_name}
mkdir -p ${to_loc_top}${dir_name}
to_loc+=$dir_name

# generate a file to list SNs with no log
# copy logs
# run parser for each SN
while read -r sn; do
    echo "SN is $sn"
    #declare -A sn_paths
    sn_path_exists=0
    for i in "${stages[@]}"
    do
        echo "stage=$i"
        case $i in
            "DL")
            from_loc="/${src_log_dir}/$card_type/DL/${sn}"
            ;;
            "SWI")
            from_loc="/${src_log_dir}/$card_type/SWI/${sn}"
            ;;
            "FST")
            from_loc="/${src_log_dir}/$card_type/FST/${sn}"
            ;;
            "P2C")
            from_loc="/${src_log_dir}/$card_type/P2C/${sn}"
            ;;
            "4C-L")
            from_loc="/${src_log_dir}/$card_type/4C/4C-L/${sn}"
            ;;
            "4C-H")
            from_loc="/${src_log_dir}/$card_type/4C/4C-H/${sn}"
            ;;
            "2C-L")
            from_loc="/${src_log_dir}/$card_type/2C/2C-L/${sn}"
            ;;
            "2C-H")
            from_loc="/${src_log_dir}/$card_type/2C/2C-H/${sn}"
            ;;
            *)
            echo "Invalid stage $i"
            exit
            ;;
        esac
        if [ ! $is_remote ]; then
            if [ -d ${from_loc} ]; then
                echo "$from_loc exists"
                sn_path_exists=1
                mkdir -p $to_loc/$card_type/$i
                cp -r $from_loc $to_loc/$card_type/$i/
            else
                echo "$from_loc does not exist"
            fi
        else
            mkdir -p $to_loc/$card_type/$i
            sshpass -p 'pensando' rsync -r mfg@hw-mftg-data:$from_loc $to_loc/$card_type/$i/
            if [ $? -eq 0 ]; then
                echo "$from_loc exists"
                sn_path_exists=1
            else
                echo "$from_loc does not exist"
            fi
        fi
    done

    if [ $sn_path_exists -eq 0 ]; then
        echo "any log for SN $sn does not exist"
        echo $sn >> $missing_log_file
        continue
    else
        echo $sn >> $existing_log_file
    fi

    echo "untar the log files"
    for stage in "${stages[@]}";
    do
        if [ $stage == "FST" ]; then
            summary_file="test_fst.log"
        else
            summary_file="mtp_test.log"
        fi
        if [ -d $to_loc/$card_type/$stage/$sn ]; then
            cd $to_loc/$card_type/$stage/$sn
            #find ./ -name '*.tar.gz' -exec sh -c 'dir=$(dirname "$0"); tar -xf "${0}" -C "${dir}"; done' {} \;
            find ./ -name '*.tar.gz' -exec sh -c 'dir=$(dirname "$0"); tar -xf "${0}" -C "${dir}";' {} \;
            cd $to_loc/$card_type
            if [[ "$fa_opt" == *"RUN"* ]]; then
                find ./$stage -name $summary_file | xargs grep -anHE "$sn NIC_DIAG_REGRESSION_TEST_[FAIL|PASS]" >> $to_loc/$card_type/testresult.txt
            else
                find ./$stage -name $summary_file | xargs grep -anH "$sn NIC_DIAG_REGRESSION_TEST_FAIL" >> $to_loc/$card_type/testresult.txt
            fi
        fi
    done
    #cat $to_loc/$card_type/testresult.txt
    run_parse $sn $card_type
    #cat $to_loc/$card_type/logs_fail.txt

    for stage in "${stages[@]}";
    do
        if [[ "$fa_opt" != *"RUN"* ]]; then
            if grep -q "${stage}\/$sn" $to_loc/$card_type/logs_fail.txt; then
                echo "failure log for SN $sn exists in stage $stage"
            else
                echo "failure log for SN $sn does not exist in stage $stage"
            fi
        fi
        if [ ! $keep_log ]; then
            rm -rf $to_loc/$card_type/$stage/$sn
        fi
    done
    if ! grep -q "$sn NIC_DIAG_REGRESSION_TEST_FAIL" $to_loc/$card_type/testresult.txt; then
        echo $sn >> $passing_log_file
    fi
    rm $to_loc/$card_type/testresult.txt
    rm $to_loc/$card_type/logs_fail.txt
done < "${cwd}/${sn_file}"

if [ ! -f $existing_log_file ]; then
    exit
fi

#cp $parse_result $to_loc_top/../
run_convert
rm -f ${existing_log_file} ${missing_log_file} ${passing_log_file}
echo "The parsing result is $parse_result"
echo "the temporary dir: $to_loc_top$dir_name can be removed"
