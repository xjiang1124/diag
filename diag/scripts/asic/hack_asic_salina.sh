chmod 775 $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so .

cd $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
rm -f *
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack

ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpcap.so.1 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
#TODO: libpcap.so*: cannot find in packaged salina image

echo "add more symbolic links for nic_x86_64.tar.gz"
#ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libzmq.so.5 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
ln -s $ASIC_LIB_BUNDLE/depend_libs/usr/local/lib/libzmq.so.3 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
#TODO: libzmq.so.5: cannot find in packaged salina image

ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libsodium.so.23 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
#TODO: libsodium.so.23: cannot find in packaged salina image
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpgm-5.2.so.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
#TODO: libpgm-5.2.so.0: cannot find in packaged salina image

#Need to source python 2.7 on matera mtp.  It is not natively installed on linux
if [[ $CARD_TYPE == "MTP_MATERA" ]] 
then
ln -s $ASIC_LIB_BUNDLE/depend_libs/lib64/libpython2.7.so.1.0 $ASIC_LIB_BUNDLE/depend_libs/mtp_hack
fi

#This file is for asic salina only
cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh/
head -n -6 .tclrc.diag.sal > .tclrc.diag.sal.new
