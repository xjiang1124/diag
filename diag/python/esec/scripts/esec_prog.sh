#!/bin/bash

get_asic_type () {
    c_type=$1

    if [[ $c_type == "ORTANO"        || \
          $c_type == "ORTANO2"       || \
          $c_type == "ORTANO2A"      || \
          $c_type == "ORTANO2AC"     || \
          $c_type == "ORTANO2I"      || \
          $c_type == "ORTANO2S"      || \
          $c_type == "LACONA32DELL"  || \
          $c_type == "LACONA32"      || \
          $c_type == "POMONTEDELL"   || \
          $c_type == "POMONTE"       || \
          $c_type == "PENSANDO"
        ]]
    then
        echo "ELBA"
    elif [[ $c_type == "GINESTRA_D4"        || \
            $c_type == "GINESTRA_D5"
        ]]
    then
        echo "GIGLIO"
    elif [[ $c_type == "MALFA"        || \
            $c_type == "POLLARA"      || \
            $c_type == "LINGUA"       || \
            $c_type == "LENI"         || \
            $c_type == "LENI48G"
        ]]
    then
        echo "SALINA"
    else
        echo "CAPRI"
    fi

}

enroll_puf () {
    cd $DIAG_HOME/diag/scripts/asic/

    asic_type=$(get_asic_type $card_type)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        tclsh ./esec_prog_elba.tcl -sn $SN -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
    elif [[ $asic_type == "GIGLIO" ]]
    then
        tclsh ./esec_prog_giglio.tcl -sn $SN -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
    elif [[ $asic_type == "SALINA" ]]
    then
        tclsh ./esec_prog_salina.tcl -sn $SN -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
    else
        tclsh ./esec_prog.tcl -sn $SN -slot $SLOT -fn "pub_ek.tcl.txt" -stage puf_enroll
    fi
}

hsm_sign_ek () {
    cd $DIAG_HOME/diag/tools/pki
    cp $DIAG_HOME/diag/asic/asic_src/ip/cosim/tclsh/pub_ek.tcl.txt .


    echo "python2.7 ./client_diag.py -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL -sn $SN -pn "$PN" -mac $MAC -pdn $CARD_TYPE -mid $MTP -s $DIAG_HOME/diag/tools/barco/otp_files/"

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        id="elba.v1"
    elif [[ $asic_type == "GIGLIO" ]]
    then
        id="giglio.v1"
    elif [[ $asic_type == "SALINA" ]]
    then
        id="salina.v1"
    else
        id="v1"
    fi
    CARD_TYPE=$(echo $CARD_TYPE | sed "s/_//")
    echo "id: $id"
    python2.7 ./client_diag.py -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL -sn $SN -pn "$PN" -mac $MAC -pdn $CARD_TYPE -mid $MTP -s $DIAG_HOME/diag/tools/barco/otp_files/ -id $id


    cp signed_ek.pub.bin signed_ek.pub.org.bin
    dd if=/dev/zero of=signed_ek.pub.bin bs=1 count=1 seek=1411
    crc32 ./signed_ek.pub.bin
    echo "SIGNING EK PASSED"
}

check_sign_ek () {
    echo "Check Signed EK"
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

    python2.7 ../generate_otp.py --algo 'ecdsa_p384' --esecboot="secure" --frksize 32 --cm_input OTP_content_CM.txt --output OTP_cm

    python2.7 ../generate_otp.py --algo 'ecdsa_p384' --hostboot="secure" --frksize 32 --sm_input OTP_content_SM.txt --output OTP_sm

    cp OTP_cm.mif OTP_cm.hex
    cp OTP_sm.mif OTP_sm.hex

    cp *hex ~/diag/asic/asic_src/ip/cosim/tclsh/images/
    echo "GEN OTP PASSED"
}

otp_init () {
    cd $DIAG_HOME/diag/scripts/asic/

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        tclsh ./esec_prog_elba.tcl -sn $SN -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
    elif [[ $asic_type == "GIGLIO" ]]
    then
        tclsh ./esec_prog_giglio.tcl -sn $SN -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
    elif [[ $asic_type == "SALINA" ]]
    then
        tclsh ./esec_prog_salina.tcl -sn $SN -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
    else
        tclsh ./esec_prog.tcl -sn $SN -slot $SLOT -stage otp_init -cm_file ./images/OTP_cm.hex -sm_file ./images/OTP_sm.hex
    fi
}

post_check () {
    cd $DIAG_HOME/diag/scripts/asic/

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        tclsh ./esec_prog_elba.tcl -stage POST_CHECK -slot $SLOT -sn $SN
    elif [[ $asic_type == "GIGLIO" ]]
    then
        tclsh ./esec_prog_giglio.tcl -stage POST_CHECK -slot $SLOT -sn $SN
    elif [[ $asic_type == "SALINA" ]]
    then
        tclsh ./esec_prog_salina.tcl -stage POST_CHECK -slot $SLOT -sn $SN
    else
        tclsh ./esec_prog.tcl -stage POST_CHECK -slot $SLOT -sn $SN
    fi
}

show_status () {
    cd $DIAG_HOME/diag/scripts/asic/

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        tclsh ./esec_prog_elba.tcl -stage SHOW_STS -slot $SLOT -sn $SN
    elif [[ $asic_type == "GIGLIO" ]]
    then
        tclsh ./esec_prog_giglio.tcl -stage SHOW_STS -slot $SLOT -sn $SN
    elif [[ $asic_type == "SALINA" ]]
    then
        tclsh ./esec_prog_salina.tcl -stage SHOW_STS -slot $SLOT -sn $SN
    else
        tclsh ./esec_prog.tcl -stage SHOW_STS -slot $SLOT -sn $SN
    fi
}

img_prog () {
    cd $DIAG_HOME/diag/scripts/asic/
    fw_ptr_img="images/esecure_fw_ptr.hex.txt"
    orcl_esec_img="images/orcl_esecure_firmware_v1_k0_packed.hex"
    orcl_host_img="images/orcl_boot_nonsec_v1_k0_packed.hex"
    generic_esec_img="images/esecure_firmware_packed.hex"
    generic_host_img="images/boot_nonsec_packed.hex"
    elba_esec_img="images/elba_esecure_firmware_m0_packed.hex"
    elba_host_img="images/elba_boot_nonsec_packed.hex"
    elba_ibm_esec_img="images/elba_ibm_esecure_firmware_m0_packed.hex"
    elba_ibm_host_img="images/elba_ibm_boot_nonsec_packed.hex"
    giglio_esec_img="images/giglio_firmware_cortex_m0_20181121_packed.hex"
    giglio_host_img="images/giglio_boot_nonsec_packed.hex"
    salina_esec_img="images/sal_softrom_cortex_m0.hex"
    salina_host_img="images/sal_pentrust_cortex_m0.hex"
    salina_nonsec_img="images/sal_boot_nonsec.hex"

    uut="UUT_$SLOT"
    card_type="${!uut}"

    asic_type=$(get_asic_type $card_type)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        echo "ELBA"
        tcl_file="./esec_prog_elba.tcl"
        if [[ $PN == *"68-0028"* ]];then
            esec_img=$elba_ibm_esec_img
            host_img1=$elba_ibm_host_img
        else 
            esec_img=$elba_esec_img
            host_img1=$elba_host_img
        fi
        host_img2=$elba_ibm_host_img
    elif [[ $asic_type == "GIGLIO" ]]
    then
        echo "GIGLIO"
        tcl_file="./esec_prog_giglio.tcl"
        esec_img=$giglio_esec_img
        host_img1=$giglio_host_img
        host_img2=$giglio_host_img
    elif [[ $asic_type == "SALINA" ]]
    then
        echo "SALINA"
        tcl_file="./esec_prog_salina.tcl"
        fw_ptr_img="images/esecure_fw_ptr.hex"
        esec_img=$salina_esec_img
        host_img1=$salina_host_img
        host_img2=$salina_nonsec_img
    else
        echo "CAPRI"
        tcl_file="./esec_prog.tcl"
        if [[ $card_type = "VOMERO2" ]]
        then
            esec_img=$orcl_esec_img
            host_img1=$orcl_host_img
            host_img2=$orcl_host_img
        else
            esec_img=$generic_esec_img
            host_img1=$generic_host_img
            host_img2=$generic_host_img
        fi
    fi
    echo "slot: $SLOT; esec_img: $esec_img; host_img1: $host_img1; host_img2: $host_img2; card_type: $card_type"

    tclsh $tcl_file -stage IMG_PROG -slot $SLOT -fw_ptr $fw_ptr_img -esec_1 $esec_img -esec_2 $esec_img -host_1 $host_img1 -host_2 $host_img2
}

dice_img_prog () {
    cd $DIAG_HOME/diag/scripts/asic/
    fw_ptr_img="images/esecure_fw_ptr.hex"
    pentrust="images/sal_pentrust_cortex_m0.hex"
    nonesec="images/sal_boot_nonsec.hex"

    uut="UUT_$SLOT"
    card_type="${!uut}"

    asic_type=$(get_asic_type $card_type)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "SALINA" ]]
    then
        echo "SALINA"
        tcl_file="./esec_prog_salina.tcl"
        pentrust_img=$pentrust
        non_esec_img=$nonesec
    else
        echo "Not valid call for non-SALINA cards"
        exit 0
    fi

    echo "slot: $SLOT; pentrust_img  $pentrust; non_esec_img $nonesec; card_type: $card_type" 
    tclsh $tcl_file -stage DICE_IMG_PROG -slot $SLOT -fw_ptr $fw_ptr_img -pentrust_1 $pentrust -pentrust_2 $pentrust -non_esec_1 $non_esec_img -non_esec_2 $non_esec_img
}

efuse_prog () {
    cd $DIAG_HOME/diag/tools/pki

    echo "python2.7 ./client_diag.py -k $CLIENT_KEY -c $CLIENT_CERT -t $TRUST_ROOTS -b $BACKEND_URL -sn $SN -pn "$PN" -mac $MAC -pdn $CARD_TYPE -mid $MTP -s $DIAG_HOME/diag/tools/barco/otp_files/ -hsm_rn -n 256"

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" || $asic_type == "GIGLIO" ]]
    then
        id="elba.v1"
    elif [[ $asic_type == "SALINA" ]]
    then
        id="salina.v1"
    else
        id="v1"
    fi
    python2.7 ./client_diag.py -k $CLIENT_KEY -c $CLIENT_CERT  -t $TRUST_ROOTS -b $BACKEND_URL -sn $SN -pn "$PN" -mac $MAC -pdn $CARD_TYPE -mid $MTP -s $DIAG_HOME/diag/tools/barco/otp_files/ -id $id -hsm_rn -n 256

    cd $DIAG_HOME/diag/scripts/asic/
    uut="UUT_$SLOT"
    card_type="${!uut}"

    asic_type=$(get_asic_type $CARD_TYPE)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" ]]
    then
        echo "ELBA"
        tcl_file="./esec_prog_elba.tcl"
    elif [[ $asic_type == "GIGLIO" ]]
    then
        echo "GIGLIO"
        tcl_file="./esec_prog_giglio.tcl"
    elif [[ $asic_type == "SALINA" ]]
    then
        echo "SALINA"
        tcl_file="./esec_prog_salina.tcl"
    else
        echo "Unsupported card type $card_type"
        return 1
    fi
    echo "slot: $SLOT; sn: $SN"

    echo "quit before efuse prog"
    return 0

    tclsh $tcl_file -stage EFUSE_PROG -slot $SLOT -sn $SN
#    if [[ $card_type == "ORTANO" ]]
#    then
#        tclsh ./esec_prog_elba.tcl -stage IMG_PROG -slot $SLOT -fw_ptr $fw_ptr_img -esec_1 $esec_img -esec_2 $esec_img -host_1 $host_img -host_2 $host_img
#    else
#        tclsh ./esec_prog.tcl -stage IMG_PROG -slot $SLOT -fw_ptr $fw_ptr_img -esec_1 $esec_img -esec_2 $esec_img -host_1 $host_img -host_2 $host_img
#    fi
}

efuse_test () {
    cd $DIAG_HOME/diag/scripts/asic/

    asic_type=$(get_asic_type $card_type)
    echo "asic_type: $asic_type"

    if [[ $asic_type == "ELBA" || $asic_type == "GIGLIO" || $asic_type == "SALINA" ]]
    then
        echo "Skip efuse test for Elba cards"
    else
        tclsh ./esec_prog.tcl -stage EFUSE_TEST -slot $SLOT
    fi
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
    rm $ASIC_SRC/ip/cosim/tclsh/images/entropy*.txt
    rm $ASIC_SRC/ip/cosim/tclsh/images/uds_csr_der.crt*
    rm $ASIC_SRC/ip/cosim/tclsh/images/uds_csr_der.crt.tmp*

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
    -card_type|--card_type)
    CARD_TYPE="$2"
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
    -k|--client_key)
    CLIENT_KEY="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -c|--client_cert)
    CLIENT_CERT="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -t|--trust_roots)
    TRUST_ROOTS="$2"
    shift # past argument
    shift # past value
    ;;
    #-------------
    -b|--backend_url)
    BACKEND_URL="$2"
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
    -dice_img_prog|--dice_img_prog)
    DICE_IMG_PROG=TRUE
    shift # past argument
    ;;
    #-------------
    -efuse_prog|--efuse_prog)
    EFUSE_PROG=TRUE
    shift # past argument
    ;;
    #-------------
    -post_check|--post_check)
    POST_CHECK=TRUE
    shift # past argument
    ;;
    #-------------
    -show_sts|--show_sts)
    SHOW_STS=TRUE
    shift # past argument
    ;;

    #-------------
    -efuse_test|--efuse_test)
    EFUSE_TEST=TRUE
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

echo "SLOT:        ${SLOT}"
echo "SN:          ${SN}"
echo "PN:          ${PN}"
echo "MAC:         ${MAC}"
echo "CARD_TYPE:   ${CARD_TYPE}"
echo "MTP:         ${MTP}"
echo "CLIENT_KEY:  ${CLIENT_KEY}"
echo "CLIENT_CERT: ${CLIENT_CERT}"
echo "TRUST_ROOTS: ${TRUST_ROOTS}"
echo "BACKEND_URL: ${BACKEND_URL}"

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

if [[ $POST_CHECK == TRUE ]]
then
    post_check
fi

if [[ $SHOW_STS == TRUE ]]
then
    show_status
fi

if [[ $IMG_PROG == TRUE ]]
then
    img_prog
fi

if [[ $DICE_IMG_PROG == TRUE ]]
then
    dice_img_prog
fi

if [[ $EFUSE_PROG == TRUE ]]
then
    efuse_prog
fi

if [[ $EFUSE_TEST == TRUE ]]
then
    efuse_test
fi

if [[ $CLEANUP == TRUE ]]
then
    cleanup
fi

