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
if [[ -z $branch_or_tag ]]; then
    release_name=jobd
else
    release_name=$(echo $branch_or_tag | awk -F'/' '{print $NF}')
fi
mfg_script_dir=${working_dir}/${release_name}/${mfg_folder}

## CLEAN UP PREVIOUS BUILD OF THIS RELEASE
mkdir -p $mfg_script_dir
sync
rm -rf $mfg_script_dir/*
rm -f ${working_dir}/${release_name}/*.tar.gz
sync
cp -r $top_dir/diag/${mfg_folder}/* $mfg_script_dir/
sync
mkdir -p $mfg_script_dir/release/
chmod 777 $mfg_script_dir/release/
if [[ ${mfg_folder} == "mfg_taormina" || ${mfg_folder} == "mfg_lipari" ]]; then
	mkdir $mfg_script_dir/tftpboot/
	chmod 777 $mfg_script_dir/tftpboot/
fi
sync

## COPY DIAG IMAGES
if [[ ${release_name} == "jobd" ]]; then
    echo "Using diag images from jobd build instead"
elif [[ -z ${alternate_diag_image} ]]; then
    cp build/images/image_amd64_${asic_type}.tar $mfg_script_dir/release/image_amd64_${asic_type}_${release_name}.tar
    cp build/images/image_arm64_${asic_type}.tar $mfg_script_dir/release/image_arm64_${asic_type}_${release_name}.tar
else
    cp $(ls ${alternate_diag_image}/image_amd64_${asic_type}*.tar) $mfg_script_dir/release/image_amd64_${asic_type}_${release_name}.tar
    cp $(ls ${alternate_diag_image}/image_arm64_${asic_type}*.tar) $mfg_script_dir/release/image_arm64_${asic_type}_${release_name}.tar
fi

if [[ ${mfg_folder} == "mfg_taormina" ]]; then
    sed -i "s/AMD64_IMG\[\"ELBA\"\] = \".*\.tar\"/AMD64_IMG\[\"ELBA\"\] = \"image_amd64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    sed -i "s/ARM64_IMG\[\"ELBA\"\] = \".*\.tar\"/ARM64_IMG\[\"ELBA\"\] = \"image_arm64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
else
    # sed -i "s/arm64_img\[\".*ELBA\"\] = \".*\.tar\"/arm64_img\[\".*ELBA\"\] = \"image_arm64_elba_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    # sed -i "s/amd64_img\[\".*ELBA\"\] = \".*\.tar\"/amd64_img\[\".*ELBA\"\] = \"image_amd64_elba_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    # sed -i "s/arm64_img\[\".*CAPRI\"\] = \".*\.tar\"/arm64_img\[\".*CAPRI\"\] = \"image_arm64_capri_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    # sed -i "s/amd64_img\[\".*CAPRI\"\] = \".*\.tar\"/amd64_img\[\".*CAPRI\"\] = \"image_amd64_capri_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    sed -i "s/MTP_ARM64_IMAGE = \".*\.tar\"/MTP_ARM64_IMAGE = \"image_arm64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
    sed -i "s/MTP_AMD64_IMAGE = \".*\.tar\"/MTP_AMD64_IMAGE = \"image_amd64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
fi

## COPY PYTHON PACKAGES
if [[ ${mfg_folder} == "mfg_taormina" ]]; then
    mkdir $mfg_script_dir/release/packages
    cp --preserve=timestamps -r /vol/hw/diag/mfg_release/prog/packages/ $mfg_script_dir/release/
fi

## PRUNING
rm -rf $mfg_script_dir/scripts

## TAR THE MFG SCRIPTS
cd $working_dir
rm -f ${release_name}.tar.gz
tar czf ${release_name}.tar.gz ${release_name}/*
mv ${release_name}.tar.gz ${release_name}/

echo "Script package available at: ${working_dir}/${release_name}"
