#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    #-------------
    -sn_list|--sn_list)
    SN_LIST=${2^^}
    shift # past argument
    shift # past value
    ;;
    #-------------
    -cm|--cm)
    CM=${2^^}
    shift # past argument
    shift # past value
    ;;

    #-------------
    -verb|--verb)
    VERB=TRUE
    shift # past argument
    ;;

    #-------------
    --default)
    DEFAULT=YES
    shift # past argument
    ;;
    #-------------
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

SN_ARRAY=$(echo $SN_LIST | tr "," "\n")
for SN in $SN_ARRAY
do
    ./find_die_id_dl.sh -cm $CM -sn $SN
done
