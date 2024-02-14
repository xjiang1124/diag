#!/bin/sh

# prepare env
# TODO: is it the final location?
mkdir -p /psdiag/lib/third-party
cp /vol/hw/diag/regression/qa_regression/psdiag_xin/diag/lib/third-party/libftd2xx.a /psdiag/lib/third-party/

make pull-assets

# debugging purpose to show where we are
pwd & ls -ltr

#sudo apt update

go mod init

exec "$@"
