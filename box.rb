from "registry.test.pensando.io:5000/pensando/diag:1.2"

user = getenv("USER")
group = getenv("GROUP_NAME")
uid = getenv("USER_UID")
gid = getenv("USER_GID")

if user != ""
  # add user
  run "groupadd -g #{gid} #{group}"
  run "useradd -l -u #{uid} -g #{gid} -m -s /bin/bash #{user}"

  run "echo 'sudo chown -R #{user} /psdiag/' >> /home/#{user}/.bash_profile"
  run "echo 'sudo chgrp -R #{user} /psdiag/' >> /home/#{user}/.bash_profile"

  run "echo '#{user} ALL=(root) NOPASSWD:ALL' > /etc/sudoers.d/#{user} && chmod 0440 /etc/sudoers.d/#{user}"
end


workdir "/psdiag"
#env GOPATH: "/psdiag/diag/app"
#env GOFLAGS: "-mod=vendor"

env GO111MODULE: "auto"
env GO111MODULE: "auto",
    LANG: "C.UTF-8"

#run "pip2.7 install redis IPython"

copy "entrypoint.sh", "/entrypoint.sh"
run "chmod +x /entrypoint.sh"

entrypoint "/entrypoint.sh"
