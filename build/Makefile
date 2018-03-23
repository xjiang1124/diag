include common.mk
include path.mk

#BUILD_DIR = $(shell pwd)
TOP_DIR = "$(shell dirname $(BUILD_DIR))"

.PHONY: all

all: amd64 arm64

c_amd64:
	@for p in $(COMMON_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

c_arm64:
	@for p in $(COMMON_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

#c_arm_32_build:
#	@for p in $(COMMON_C_SRC_DIR); do \
#		echo "==> Build $$p ..."; \
#		$(MAKE) -Wl,-no-pie -e ARCH=arm CC=$(CC_ARM_32) -C $(TOP_DIR)/diag/lib/$$p || exit 1; \
#	done

go_arm64_1:
	@for p in $(COMMON_SRC_DIR); do \
	        echo "==> Build $$p ..."; echo $(notdir $(addprefix /, $$p)); \
		env GOOS=linux GOARCH=arm64 CGO_ENABLED=1 CGO_LDFLAGS="$(TOP_DIR)/diag/app/pkg/linux_arm64/clib/libi2csim.a $(TOP_DIR)/diag/app/pkg/linux_arm64/clib/libi2c.a" CC=$(CC_ARM_64) $(GO_BUILD) -o $(GOBIN)/arm64/$$p $$p || exit 1; \
	done

#arm_32_go_build:
#	@for p in $(COMMON_SRC_DIR); do \
#		echo "==> Build $$p ..."; echo $(notdir $(addprefix /, $$p)); \
#		env GOOS=linux GOARM=7 GOARCH=arm CGO_ENABLED=1 CC=$(CC_ARM_32) $(GO_BUILD) -x --ldflags '-linkmode=external -extldflags "-no-pie"' -o $(GOBIN)/arm32/$$p $$p || exit 1; \
#	done

go_amd64_1:
	@for p in $(COMMON_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		env CGO_LDFLAGS="$(TOP_DIR)/diag/app/pkg/linux_amd64/clib/libi2csim.a $(TOP_DIR)/diag/app/pkg/linux_amd64/clib/libi2c.a" $(GO_BUILD) -o $(GOBIN)/linux_amd64/$$p $$p || exit 1; \
	done
#	@echo $(SRC);go build $(LDFLAGS) $(SRC)

go_amd64:
	@for p in $(COMMON_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=amd64  || exit 1; \
	done
	@for p in $(AMD64_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=amd64  || exit 1; \
	done

go_arm64:
	@for p in $(COMMON_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=arm64  || exit 1; \
	done
	@for p in $(ARM64_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=arm64  || exit 1; \
	done

amd64:
	@for p in $(COMMON_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=amd64  || exit 1; \
	done
	@for p in $(AMD64_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=amd64  || exit 1; \
	done
	cd $(BUILD_DIR)
	scripts/packaging.sh

arm64:
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(COMMON_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=arm64  || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_LIB_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		cd $(TOP_DIR)/diag/app/src/$$p; \
		$(MAKE) ARCH=arm64  || exit 1; \
	done
	cd $(BUILD_DIR)
	scripts/packaging.sh arm64

test:
	@for p in $(GO_TEST_DIR); do \
		echo "==> Build $$p ..."; \
		$(GO_TEST) $$p || exit 1; \
	done
#	@echo $(SRC);go build $(LDFLAGS) $(SRC)

c_amd64-clean:
	rm -f $(GOPATH)/pkg/linux_amd64/clib/*

c_arm64-clean:
	rm -f $(GOPATH)/pkg/linux_arm64/clib/*

go_amd64-clean:
	rm -rf $(GOPATH)/bin/linux_amd64/*
	include $(TOP_DIR)/build/common.mk

go_arm64-clean:
	rm -rf $(GOPATH)/bin/linux_arm64/*
	
amd64-clean:
	rm -rf $(GOPATH)/pkg/linux_amd64/clib/*
	rm -rf $(GOPATH)/bin/linux_amd64/*
	rm -rf $(BUILD_DIR)/images/*amd64*

arm64-clean:
	rm -rf $(GOPATH)/pkg/linux_arm64/*
	rm -rf $(GOPATH)/bin/linux_arm64/*
	rm -rf $(BUILD_DIR)/images/*arm64*
										
