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
cd /vol/hw/diag/mfg_release/prog/
for f in $image_files; do
    rsync -aPtv --relative $f ${dest_folder}
done

## TAR THE FW IMAGES
cd ${dest_folder}/..
tar cf fw.tar release/ --strip-components=1
