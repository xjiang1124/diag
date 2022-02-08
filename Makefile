#################################################
################### DOCKER ######################
#################################################
CUR_DIR:=$(shell pwd)
SW_DIR:=$(shell dirname ${CUR_DIR})
CUR_USER:=$(shell whoami)
CUR_TIME:=$(shell date +%Y-%m-%d_%H.%M.%S)
CONTAINER_NAME:=${CUR_USER}_${CUR_TIME}
REGISTRY = registry.test.pensando.io:5000
DIAG_CONTAINER_VERSION:=1.0
DIAG_CONTAINER:=${REGISTRY}/pensando/diag:${DIAG_CONTAINER_VERSION}

# get a shell with the dependencies image loaded, with the host filesystem mounted.
docker/shell: docker/install_box
	docker run -it --rm --sysctl net.ipv6.conf.all.disable_ipv6=1 -e "GOPATH=/psdiag/diag/app" --privileged --name ${CONTAINER_NAME} -v $(CUR_DIR):/psdiag -v /vol/hw:/vol/hw -w /psdiag ${DIAG_CONTAINER} bash

docker/install_box:
	@if [ ! -x /usr/local/bin/box ]; then echo "Installing box, sudo is required"; curl -sSL box-builder.sh | sudo bash; fi

# make a test image for CI run.
docker/build: docker/install_box
	BOX_INCLUDE_ENV="FLATTEN" FLATTEN=1 box -n -t ${DIAG_CONTAINER} box-build.rb

docker/push-build:
	docker push ${DIAG_CONTAINER}
