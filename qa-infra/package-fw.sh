top_dir=$PWD
asic_type=$(echo $asic_type)
mfg_folder="mfg"
if [[ ${asic_type} == "taormina" ]]; then
	asic_type="elba"
	mfg_folder="mfg_taormina"
fi
if [[ ${asic_type} == "lipari" ]]; then
	asic_type="elba"
	mfg_folder="mfg_lipari"
fi
if [[ -z ${working_dir} ]]; then
    working_dir=/psdiag
fi
mfg_script_dir=${working_dir}/diag/${mfg_folder}
dest_folder=${working_dir}/release/
mkdir -p ${dest_folder}


## COPY NIC IMAGES
image_files=$(grep -e "_img" -e "_dtb" ${mfg_script_dir}/lib/libmfg_cfg.py | grep \".*\" | grep -v "#" | grep -v "image_a" | cut -d"=" -f2 | cut -d'"' -f2 | sort | uniq)
for f in $image_files; do
    cd /vol/hw/diag/mfg_release/prog/
    if [[ -e $f ]]; then
        rsync -aPtv --relative $f ${dest_folder}
    else
        # try finding it in vulcano release folder
        cd /vol/hw/diag/mfg_release/
        g=$(find . \
        -path "*$f" \
        -print \
        -quit \
        )
        if [[ -z $g ]]; then
           echo "========================================"
           echo " Missing file $g"
           echo "========================================"
           continue
        fi
        # vulcano directory is organized as "CARD_TYPE/IMAGE".
        # We dont need to copy the CARD_TYPE folder to MTP, so flatten it
        g=$(echo $g | sed "s/^\.\///g") # sanitize `find` results starting the path with "./"
        cd ${g%%/*}  					# go into the directory to keep --relative honest
        g=$(echo $g | cut -d'/' -f2-)   # strip CARD_TYPE directory
        rsync -aPtv --relative $g ${dest_folder}
        if [[ $? != 0 ]]; then
           echo "========================================"
           echo " Missing file $g"
           echo "========================================"
        fi
    fi
done

## TAR THE FW IMAGES
cd ${dest_folder}/..
tar cf fw.tar release/ --strip-components=1
