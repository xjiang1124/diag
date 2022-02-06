#!/bin/sh

curl -o /usr/bin/asset-pull http://pm.test.pensando.io/tools/asset-pull && chmod +x /usr/bin/asset-pull
asset-pull --help

# debugging purpose to show where we are
pwd & ls

exec "$@"
