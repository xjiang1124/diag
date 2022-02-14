chmod 775 $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so .

cd $ASIC_LIB_BUNDLE/asic_lib/
cp -f $ASIC_LIB_BUNDLE/depend_libs/lib64/libJudy.so.1 .
cp -f $ASIC_LIB_BUNDLE/depend_libs/lib64/libtcl8.5.so .
cp -f $ASIC_LIB_BUNDLE/depend_libs/lib64/libgmpxx.so.4 .
cp -f $ASIC_LIB_BUNDLE/depend_libs/lib64/libcrypto.so.10 .

cd $ASIC_LIB_BUNDLE/asic_src/ip/cosim/tclsh/
head -n -5 .tclrc.diag > .tclrc.diag.new
