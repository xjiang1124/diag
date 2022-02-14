top_dir=$PWD
release_name=$(echo $branch_or_tag | awk -F'/' '{print $NF}')
asic_type=$(echo $asic_type)
jenkins_dir=/vol/hw/diag/mfg_release/jenkins
mfg_script_dir=${jenkins_dir}/${release_name}/mfg

## CLEAN UP JENKINS BUILDS
#rm -rf $jenkins_dir/*
#sync
## CLEAN UP PREVIOUS BUILD OF THIS RELEASE
mkdir -p $mfg_script_dir
sync
rm -rf $mfg_script_dir/*
sync
cp -r $top_dir/diag/mfg/* $mfg_script_dir/
sync
chmod 777 $mfg_script_dir/release/
sync

## COPY DIAG IMAGES
if [[ -z ${alternate_diag_image} ]]; then
    cp build/images/image_amd64_${asic_type}.tar $mfg_script_dir/release/image_amd64_${asic_type}_${release_name}.tar
    cp build/images/image_arm64_${asic_type}.tar $mfg_script_dir/release/image_arm64_${asic_type}_${release_name}.tar
else
    cp $(ls ${alternate_diag_image}/image_amd64_${asic_type}*.tar) $mfg_script_dir/release/image_amd64_${asic_type}_${release_name}.tar
    cp $(ls ${alternate_diag_image}/image_arm64_${asic_type}*.tar) $mfg_script_dir/release/image_arm64_${asic_type}_${release_name}.tar
fi

sed -i "s/MTP_ARM64_IMAGE = \".*\.tar\"/MTP_ARM64_IMAGE = \"image_arm64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
sed -i "s/MTP_AMD64_IMAGE = \".*\.tar\"/MTP_AMD64_IMAGE = \"image_amd64_${asic_type}_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py

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
    cp --preserve=timestamps /home/nabeel/ws/psdiag/diag/mfg/release/$f $mfg_script_dir/release
done

## CREATE SW PN LINKS
cd $mfg_script_dir/release
rm -f 90-*
for swpn in $(grep -o "90-....-[0-9A-Za-z]*" ../lib/libmtp_ctrl.py); do 
    img_src="/home/nabeel/ws/psdiag/diag/mfg/release"
    if [ -e $img_src/$swpn ]; then 
        fn=$(ls -l $img_src/$swpn | awk '{print $NF}'); 
        if [ ! -e $swpn ]; then
            cp --preserve=timestamps $img_src/$fn ./
            ln -s $fn $swpn
        fi
    fi
done

sync

echo "Release available at: ${jenkins_dir}/${release_name}"
