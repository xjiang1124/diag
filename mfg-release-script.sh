top_dir=$PWD
release_name=$(echo $branch_or_tag | awk -F'/' '{print $NF}')
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
cp build/images/image_amd64_elba.tar $mfg_script_dir/release/image_amd64_elba_${release_name}.tar
cp build/images/image_arm64_elba.tar $mfg_script_dir/release/image_arm64_elba_${release_name}.tar
cp build/images/image_amd64_capri.tar $mfg_script_dir/release/image_amd64_capri_${release_name}.tar
cp build/images/image_arm64_capri.tar $mfg_script_dir/release/image_arm64_capri_${release_name}.tar

sed -i "s/MTP_ARM64_IMAGE = \".*\.tar\"/MTP_ARM64_IMAGE = \"image_arm64_elba_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py
sed -i "s/MTP_AMD64_IMAGE = \".*\.tar\"/MTP_AMD64_IMAGE = \"image_amd64_elba_${release_name}\.tar\"/g" $mfg_script_dir/lib/libmfg_cfg.py

## PRUNING
rm -rf $mfg_script_dir/scripts

## TAR THE MFG SCRIPTS
cd $jenkins_dir
rm -f ${release_name}.tar.gz
tar czf ${release_name}.tar.gz ${release_name}/*

## COPY NIC IMAGES
image_files=$(grep "_img" ${mfg_script_dir}/lib/libmfg_cfg.py | grep \".*\" | grep -v "#" | cut -d"=" -f2 | cut -d'"' -f2 | sort | uniq)
for f in $image_files; do
    cp /home/nabeel/ws/psdiag/diag/mfg/release/$f $mfg_script_dir/release
done

sync

