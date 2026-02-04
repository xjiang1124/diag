#!/bin/bash

if [[ $MTP_TYPE != "MTP_MATERA" && $MTP_TYPE != "MTP_PANAREA" && $MTP_TYPE != "MTP_PONZA" ]]
then 
    source /home/diag/diag/scripts/turn_on_slot_legacy.sh
else 
    source /home/diag/diag/scripts/turn_on_slot_matera.sh
fi


