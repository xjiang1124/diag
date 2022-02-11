from "ubuntu:18.04"

run "apt update"
run "DEBIAN_FRONTEND=noninteractive apt install -y build-essential curl gcc-aarch64-linux-gnu python-pip git rsync sudo"

run "pip install redis IPython pyyaml"

run "curl -o /usr/bin/asset-pull http://pm.test.pensando.io/tools/asset-pull && chmod +x /usr/bin/asset-pull"
run "curl -o /usr/bin/asset-push http://pm.test.pensando.io/tools/asset-push && chmod +x /usr/bin/asset-push"
run "curl -sSL http://pm.test.pensando.io/tools/go1.12.12.linux-amd64.tar.gz | tar xz -C /usr/local/"

env GOPATH: "/psdiag/diag/app",
    PATH: "/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:/usr/local/go/bin:/go/bin"

flatten
