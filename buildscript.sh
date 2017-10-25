#!/bin/bash
top_dir=$PWD
export GOPATH=${top_dir}/diag/app
export GOBIN=${top_dir}/diag/app/bin
export LD_LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/
export LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/

mkdir -p ${top_dir}/diag/app/pkg/linux_amd64/common/
mkdir -p ${top_dir}/diag/app/pkg/linux_arm64/common/

cd build
make c_build
make build
#make test
make c_arm_64_build
make arm_64_go_build

