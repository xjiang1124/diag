#!/bin/bash

enroll_puf () {
    cd $DIAG_HOME/diag/scripts/asic/
    tclsh ./esec_prog.tcl -sn slot$SLOT -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
}

hsm_sign_ek () {
    cd $DIAG_HOME/diag/tools/pki
    cp $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt .

    python ./client_diag.py -k certs/client.key.pem -c certs/client-bundle.cert.pem  -t certs/rootca.cert.pem -b enrico.dev.pensando.io:12267 -sn $SN -pn $PN -mac $MAC -pdn $BRD_NAME -mid $MTP

    dd if=/dev/zero of=signed_ek.pub.bin bs=1 count=1 seek=1411
    crc32 ./signed_ek.pub.bin
}

gen_otp () {
    cd ~/diag/tools/barco/otp_files
    cp ~/diag/tools/pki/signed_ek.pub.bin chipcert.der

    python ../generate_otp.py --algo 'ecdsa_p384' --esecboot="secure" --frksize 32 --cm_input OTP_content_CM.txt --output OTP_cm

    python ../generate_otp.py --algo 'ecdsa_p384' --hostboot="secure" --frksize 32 --sm_input OTP_content_SM.txt --output OTP_sm

    cp OTP_cm.mif OTP_cm.hex
    cp OTP_sm.mif OTP_sm.hex

    cp *hex ~/diag/asic/asic_src/ip/cosim/tclsh/images/
    echo "GEN OTP PASSED"
}

otp_init () {
    cd $DIAG_HOME/diag/scripts/asic/
    tclsh ./esec_prog.tcl -sn slot$SLOT -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
}

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    #-------------
    -slot|--slot)
    SLOT="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -sn|--sn)
    SN="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -pn|--pn)
    PN="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -mac|--mac)
    MAC="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -brd_name|--board_name)
    BRD_NAME="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -mtp|--MTP)
    MTP="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -enroll_puf|--enroll_puf)
    ENROLL_PUF=TRUE
    shift # past argument
    ;;
    #-------------
    -sign_ek|--sign_ek)
    SIGN_EK=TRUE
    shift # past argument
    ;;
    #-------------
    -gen_otp|--gen_otp)
    GEN_OTP=TRUE
    shift # past argument
    ;;
    #-------------
    -otp_init|--otp_init)
    OTP_INIT=TRUE
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

echo "SLOT:     ${SLOT}"
echo "SN:       ${SN}"
echo "PN:       ${PN}"
echo "MAC:      ${MAC}"
echo "BRD_NAME: ${BRD_NAME}"
echo "MTP:      ${MTP}"

if [[ $ENROLL_PUF == TRUE ]]
then
    enroll_puf
fi

if [[ $SIGN_EK == TRUE ]]
then
    hsm_sign_ek
fi

if [[ $GEN_OTP == TRUE ]]
then
    gen_otp
fi

if [[ $OTP_INIT == TRUE ]]
then
    otp_init
fi

