echo $CARD_TYPE
if [[ $CARD_TYPE == "FORIO" ]] 
then
    ./diag.exe prbs.e.a.forio.tcl
else
    ./diag.exe prbs.e.a.tcl
fi
