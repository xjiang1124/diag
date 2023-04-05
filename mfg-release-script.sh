top_dir=$PWD
release_name=$(echo $branch_or_tag | awk -F'/' '{print $NF}')
asic_type=$(echo $asic_type)
jenkins_dir=$(echo $working_dir)
mfg_folder="mfg"
if [[ ${asic_type} == "taormina" ]]; then
	asic_type="elba"
	mfg_folder="mfg_taormina"
fi
if [[ ${asic_type} == "lipari" ]]; then
	asic_type="elba"
	mfg_folder="mfg_lipari"
fi
if [[ -z ${jenkins_dir} ]]; then
	jenkins_dir=/vol/hw/diag/mfg_release/jenkins
fi
mfg_script_dir=${jenkins_dir}/${release_name}/${mfg_folder}

## CLEAN UP PREVIOUS BUILD OF THIS RELEASE
mkdir -p $mfg_script_dir
sync
rm -rf $mfg_script_dir/*
rm -f ${jenkins_dir}/${release_name}/*.tar.gz
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
cd $jenkins_dir
rm -f ${release_name}.tar.gz
tar czf ${release_name}.tar.gz ${release_name}/*
mv ${release_name}.tar.gz ${release_name}/

## COPY NIC IMAGES
image_files=$(grep "_img" ${mfg_script_dir}/lib/libmfg_cfg.py | grep \".*\" | grep -v "#" | grep -v "image_a" | cut -d"=" -f2 | cut -d'"' -f2 | sort | uniq)
for f in $image_files; do
    if [[ ${mfg_folder} == "mfg_taormina" || ${mfg_folder} == "mfg_lipari" ]]; then
        cp --preserve=timestamps /tftpboot/nabeel/$f $mfg_script_dir/tftpboot/
    else
        cp --preserve=timestamps /vol/hw/diag/mfg_release/prog/$f $mfg_script_dir/release
    fi
done

## CREATE SW PN LINKS
cd $mfg_script_dir/release
rm -f 90-*
for swpn in $(grep -o "90-....-[0-9A-Za-z]*" ../lib/libmtp_ctrl.py); do 
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
cd ${mfg_script_dir}
tar czf fw.tar.gz release/ --remove-files
mv fw.tar.gz ../
if [[ ${mfg_folder} == "mfg_taormina" || ${mfg_folder} == "mfg_lipari" ]]; then
	tar czf tftpboot.tar.gz tftpboot/ --remove-files
	mv tftpboot.tar.gz ../
fi

sync

echo "Release available at: ${jenkins_dir}/${release_name}"
