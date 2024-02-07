#################################################
################### DOCKER ######################
#################################################
CUR_DIR:=$(shell pwd)
CUR_USER:=$(shell whoami)
CUR_TIME:=$(shell date +%Y-%m-%d_%H.%M.%S)
CONTAINER_NAME:=${CUR_USER}_${CUR_TIME}
REGISTRY = registry.test.pensando.io:5000
DIAG_CONTAINER_VERSION:=1.1
DIAG_CONTAINER:=${REGISTRY}/pensando/diag:${DIAG_CONTAINER_VERSION}
SHELL_IMAGE_NAME="pensando/diag:shell"


# get a shell with the dependencies image loaded, with the host filesystem mounted.
ifeq ($(USER),)
docker/shell:
	docker run -it --rm --sysctl net.ipv6.conf.all.disable_ipv6=1 -e "GOPATH=/psdiag/diag/app" --privileged --name ${CONTAINER_NAME} -v $(CUR_DIR):/psdiag -v /vol/hw:/vol/hw -w /psdiag ${DIAG_CONTAINER} bash
else
docker/shell: docker/build-shell-image
	docker run -it --user ${CUR_USER} --rm --sysctl net.ipv6.conf.all.disable_ipv6=1 -e "GOPATH=/psdiag/diag/app" --privileged --name ${CONTAINER_NAME} -v $(CUR_DIR):/psdiag -v /vol/hw:/vol/hw -w /psdiag ${SHELL_IMAGE_NAME}
endif

docker/build-shell-image: docker/install_box
	if [ "x${NO_PULL}" = "x" ]; then docker pull ${DIAG_CONTAINER}; fi
	BOX_INCLUDE_ENV="USER USER_UID USER_GID GROUP_NAME HOST_HOSTNAME HOST_WORKSPACE" USER_UID=$$(id -u) USER_GID=$$(id -g) GROUP_NAME=$$(id -gn) HOST_HOSTNAME=$$(hostname) HOST_WORKSPACE=$$(git rev-parse --show-toplevel) box -t ${SHELL_IMAGE_NAME} box.rb

docker/install_box:
	@if [ ! -x /usr/local/bin/box ]; then echo "Installing box, sudo is required"; curl -sSL box-builder.sh | sudo bash; fi

# make a test image for CI run.
docker/build: docker/install_box
	BOX_INCLUDE_ENV="FLATTEN" FLATTEN=1 box -n -t ${DIAG_CONTAINER} box-build.rb

docker/push-build:
	docker push ${DIAG_CONTAINER}

pull-assets:
	bash build/scripts/pull-assets.sh
