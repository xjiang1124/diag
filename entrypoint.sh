#!/bin/sh

curl -o /usr/bin/asset-pull http://pm.test.pensando.io/tools/asset-pull && chmod +x /usr/bin/asset-pull
asset-pull --help

# prepare env
# TODO: is it the final location?
mkdir -p /psdiag/lib/third-party
cp /vol/hw/diag/regression/qa_regression/psdiag_xin/diag/lib/third-party/libftd2xx.a /psdiag/lib/third-party/

rm -f /etc/yum.repos.d/endpoint.repo
yum install -y gcc-aarch64-linux-gnu

# debugging purpose to show where we are
pwd & ls

exec "$@"
