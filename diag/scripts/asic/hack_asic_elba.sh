chmod 775 $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so .

# Check if directory exists before proceeding
if [[ ! -d "$ASIC_LIB_BUNDLE/depend_libs/mtp_hack" ]]
then
    echo "ERROR: Directory $ASIC_LIB_BUNDLE/depend_libs/mtp_hack does not exist"
    exit 1
fi

cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
rm -f *
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
echo "add more symbolic links for nic_x86_64.tar.gz"
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libzmq.so.5 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libsodium.so.23 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpgm-5.2.so.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack

#Need to source python 2.7 on matera mtp.  It is not natively installed on linux
if [[ $CARD_TYPE == "MTP_MATERA" || $CARD_TYPE == "MTP_PANAREA" || $CARD_TYPE == "MTP_PONZA" ]]
then
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
fi

if [[ $CARD_TYPE != "MTP_PANAREA" && $CARD_TYPE != "MTP_PONZA" ]]
then
cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh/
head -n -6 .tclrc.diag.elb > .tclrc.diag.elb.new
fi