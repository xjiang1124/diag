from "registry.test.pensando.io:5000/pensando/nic:1.56"

workdir "/psdiag"
env GOPATH: "/psdiag/diag/app"
#env GOFLAGS: "-mod=vendor"

run "pip2.7 install redis IPython"

copy "entrypoint.sh", "/entrypoint.sh"
run "chmod +x /entrypoint.sh"

entrypoint "/entrypoint.sh"
