#!/bin/bash
top_dir=$PWD
export GOPATH=${top_dir}/diag/app
export GOBIN=${top_dir}/diag/app/bin
export LD_LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/
export LIBRARY_PATH=${top_dir}/diag/app/pkg/linux_amd64/common/
cd build
make c_build
make build
