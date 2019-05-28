#!/bin/bash

enroll_puf () {
    cd $DIAG_HOME/diag/scripts/asic/
    tclsh ./esec_prog.tcl -sn $SN -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
}

hsm_sign_ek () {
    cd $DIAG_HOME/diag/tools/pki
    cp $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt .

    python ./client_diag.py -k certs/client.key.pem -c certs/client-bundle.cert.pem  -t certs/rootca.cert.pem -b enrico.dev.pensando.io:12267 -sn $SN -pn $PN -mac $MAC -pdn $BRD_NAME -mid $MTP -s $DIAG_HOME/diag/tools/barco/otp_files/

    cp signed_ek.pub.bin signed_ek.pub.org.bin
    dd if=/dev/zero of=signed_ek.pub.bin bs=1 count=1 seek=1411
    crc32 ./signed_ek.pub.bin
    echo "SIGNING EK PASSED"
}

check_sign_ek () {
    cd $DIAG_HOME/diag/tools/pki
    openssl x509 -in signed_ek.pub.org.bin -inform DER -text -noout
}

sign_ek_crc () {
    cd $DIAG_HOME/diag/tools/pki
    crc32 ./signed_ek.pub.bin
}

gen_otp () {
    cp $DIAG_HOME/diag/python/esec/OTP_content_CM.txt $DIAG_HOME/diag/tools/barco/otp_files/
    cd $DIAG_HOME/diag/tools/barco/otp_files
    cp $DIAG_HOME/diag/tools/pki/signed_ek.pub.bin chipcert.der

    python ../generate_otp.py --algo 'ecdsa_p384' --esecboot="secure" --frksize 32 --cm_input OTP_content_CM.txt --output OTP_cm

    python ../generate_otp.py --algo 'ecdsa_p384' --hostboot="secure" --frksize 32 --sm_input OTP_content_SM.txt --output OTP_sm

    cp OTP_cm.mif OTP_cm.hex
    cp OTP_sm.mif OTP_sm.hex

    cp *hex ~/diag/asic/asic_src/ip/cosim/tclsh/images/
    echo "GEN OTP PASSED"
}

otp_init () {
    cd $DIAG_HOME/diag/scripts/asic/
    tclsh ./esec_prog.tcl -sn $SN -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
}

img_prog () {
    cd $DIAG_HOME/diag/scripts/asic/
    tclsh ./esec_prog.tcl -stage IMG_PROG -slot $SLOT -fw_ptr images/esecure_fw_ptr.hex.txt -esec_1 images/esecure_firmware_packed.hex -esec_2 images/esecure_firmware_packed.hex -host_1 images/boot_nonsec_packed.hex -host_2 images/boot_nonsec_packed.hex
}

cleanup () {
    echo "Cleaning up"
    rm $DIAG_HOME/diag/python/esec/OTP*txt
    rm $DIAG_HOME/diag/tools/pki/pub_ek.tcl.txt
    rm $DIAG_HOME/diag/tools/pki/signed_ek.pub.bin
    rm $DIAG_HOME/diag/tools/pki/signed_ek.pub.org.bin
    rm $DIAG_HOME/diag/tools/barco/otp_files/OTP_content_CM.txt
    rm $DIAG_HOME/diag/tools/barco/otp_files/OTP_cm*
    rm $DIAG_HOME/diag/tools/barco/otp_files/OTP_sm*
    rm $DIAG_HOME/diag/tools/barco/otp_files/OTP_full*
    rm $DIAG_HOME/diag/tools/barco/otp_files/*frk
    rm $DIAG_HOME/diag/tools/barco/otp_files/*pk
    rm $DIAG_HOME/diag/tools/barco/otp_files/chipcert.der
    rm $ASIC_SRC/ip/cosim/tclsh/images/OTP*hex

    echo "Clean up done"
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
    -cleanup|--cleanup)
    CLEANUP=TRUE
    shift # past argument
    ;;
    #-------------
    -ek_crc|--ek_crc)
    EK_CRC=TRUE
    shift # past argument
    ;;
    #-------------
    -ek_check|--ek_check)
    EK_CHECK=TRUE
    shift # past argument
    ;;
    #-------------
    -img_prog|--img_prog)
    IMG_PROG=TRUE
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

if [[ $EK_CRC == TRUE ]]
then
    sign_ek_crc
fi

if [[ $EK_CHECK == TRUE ]]
then
    check_sign_ek
fi

if [[ $IMG_PROG == TRUE ]]
then
    img_prog
fi

if [[ $CLEANUP == TRUE ]]
then
    cleanup
fi

