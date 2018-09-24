#!/bin/bash
top_dir=$PWD
export GOPATH=${top_dir}/diag/app
export GOBIN=${top_dir}/diag/app/bin
export LD_LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/
export LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/

mkdir -p ${top_dir}/diag/app/pkg/linux_amd64/common/
mkdir -p ${top_dir}/diag/app/pkg/linux_arm64/common/

cd build
make amd64
make arm64

cp images/* /vol/hw/diag/diag_images/jenkins/


