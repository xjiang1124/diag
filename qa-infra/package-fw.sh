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
image_files=$(grep "_img" ${mfg_script_dir}/lib/libmfg_cfg.py | grep \".*\" | grep -v "#" | grep -v "image_a" | cut -d"=" -f2 | cut -d'"' -f2 | sort | uniq)
for f in $image_files; do
    cp --preserve=timestamps /vol/hw/diag/mfg_release/prog/$f ${dest_folder}
done

## CREATE SW PN LINKS
cd ${dest_folder}
rm -f 90-*
for swpn in $(grep -o "90-....-[0-9A-Za-z]*" ${mfg_script_dir}/lib/libmtp_ctrl.py); do 
    img_src="/vol/hw/diag/mfg_release/prog"
    if [ -e $img_src/$swpn ]; then 
        fn=$(ls -l $img_src/$swpn | awk '{print $NF}'); 
        if [ ! -e $swpn ]; then
            cp --preserve=timestamps $img_src/$fn ./
            ln -s $fn $swpn
        fi
    fi
done

## TAR THE FW IMAGES
cd ${dest_folder}/..
tar cf fw.tar release/ --strip-components=1
