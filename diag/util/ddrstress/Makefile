TOP_DIR=../../../
include $(TOP_DIR)/build/common.mk

all:
	@mkdir -p ${GOPATH}/pkg/linux_$(ARCH)/cbin/
	cp stressapptest_arm $(GOPATH)/bin/linux_$(ARCH)/cbin/
clean:
	-rm -f $(GOPATH)/bin/linux_$(ARCH)/cbin/stressapptest_arm

