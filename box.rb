from "registry.test.pensando.io:5000/pensando/nic:1.56"

workdir "/psdiag"

copy "entrypoint.sh", "/entrypoint.sh"
run "chmod +x /entrypoint.sh"

entrypoint "/entrypoint.sh"
