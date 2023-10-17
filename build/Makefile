include common.mk
include path.mk

#BUILD_DIR = $(shell pwd)
TOP_DIR = "$(shell dirname $(BUILD_DIR))"
MKDIR_P = mkdir -p
.PHONY: all

all: amd64 arm64

c_amd64:
	$(MKDIR_P) $(GOPATH)/pkg/linux_amd64/clib
	$(MKDIR_P) $(GOPATH)/bin/linux_amd64/cbin
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

c_arm64:
	$(MKDIR_P) -p $(GOPATH)/pkg/linux_arm64/clib/
	$(MKDIR_P) -p $(GOPATH)/bin/linux_arm64/cbin/
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

c_arm:
	$(MKDIR_P) -p $(GOPATH)/pkg/linux_arm/clib/
	$(MKDIR_P) -p $(GOPATH)/bin/linux_arm/cbin/
	@for p in $(COMMON_C_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        $(MAKE) -e ARCH=arm CC=$(CC_ARM) -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
	@for p in $(ARM64_C_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        $(MAKE) -e ARCH=arm CC=$(CC_ARM) -C $(TOP_DIR)/diag/$$p || exit 1; \
    done


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

go_arm:
	@for p in $(COMMON_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        cd $(TOP_DIR)/diag/app/src/$$p; \
        $(MAKE) ARCH=arm  || exit 1; \
    done
	@for p in $(ARM_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        cd $(TOP_DIR)/diag/app/src/$$p; \
        $(MAKE) ARCH=arm  || exit 1; \
    done


amd64:
	$(MKDIR_P) $(GOPATH)/pkg/linux_amd64/clib
	$(MKDIR_P) $(GOPATH)/bin/linux_amd64/cbin
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "===> Build $$p"; \
		$(MAKE) -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
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
	cd $(BUILD_DIR)
	scripts/packaging.sh amd64 ${asic} ${asiclib}

arm64:
	$(MKDIR_P) -p $(GOPATH)/pkg/linux_arm64/clib/
	$(MKDIR_P) -p $(GOPATH)/bin/linux_arm64/cbin/
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Build $$p ..."; \
		$(MAKE) -e ARCH=arm64 CC=$(CC_ARM_64) -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
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
	cd $(BUILD_DIR)
	scripts/packaging.sh arm64 ${asic} ${asiclib}

arm:
	$(MKDIR_P) -p $(GOPATH)/pkg/linux_arm/clib/
	$(MKDIR_P) -p $(GOPATH)/bin/linux_arm/cbin/
	@for p in $(COMMON_C_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        $(MAKE) -e ARCH=arm CC=$(CC_ARM) -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
	@for p in $(ARM_C_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        $(MAKE) -e ARCH=arm CC=$(CC_ARM) -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
	@for p in $(COMMON_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        cd $(TOP_DIR)/diag/app/src/$$p; \
        $(MAKE) ARCH=arm  || exit 1; \
    done
	@for p in $(ARM_SRC_DIR); do \
        echo "==> Build $$p ..."; \
        cd $(TOP_DIR)/diag/app/src/$$p; \
        $(MAKE) ARCH=arm  || exit 1; \
    done
	cd $(BUILD_DIR)
	scripts/packaging.sh arm ${asic}

test:
	@for p in $(GO_TEST_DIR); do \
		echo "==> Build $$p ..."; \
		$(GO_TEST) $$p || exit 1; \
	done

c_amd64-clean:
	rm -f $(GOPATH)/pkg/linux_amd64/clib/*
	rm -f $(GOPATH)/bin/linux_amd64/cbin/*
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

c_arm64-clean:
	rm -f $(GOPATH)/pkg/linux_arm64/clib/*
	rm -f $(GOPATH)/bin/linux_arm64/cbin/*
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

c_arm-clean:
	rm -f $(GOPATH)/pkg/linux_arm/clib/*
	rm -f $(GOPATH)/bin/linux_arm/cbin/*
	@for p in $(COMMON_C_SRC_DIR); do \
        echo "==> Clean $$p ..."; \
        $(MAKE) clean -e ARCH=arm -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
	@for p in $(ARM_C_SRC_DIR); do \
        echo "==> Clean $$p ..."; \
        $(MAKE) clean -e ARCH=arm -C $(TOP_DIR)/diag/$$p || exit 1; \
    done


go_amd64-clean:
	rm -rf $(GOPATH)/bin/linux_amd64/*

go_arm64-clean:
	rm -rf $(GOPATH)/bin/linux_arm64/*

go_arm-clean:
	rm -rf $(GOPATH)/bin/linux_arm/*


amd64-clean:
	rm -rf $(GOPATH)/pkg/linux_amd64/clib/*
	rm -rf $(GOPATH)/bin/linux_amd64/*
	rm -rf $(BUILD_DIR)/images/*amd64*
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(AMD64_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=amd64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done

arm64-clean:
	rm -rf $(GOPATH)/pkg/linux_arm64/*
	rm -rf $(GOPATH)/bin/linux_arm64/*
	rm -rf $(BUILD_DIR)/images/*arm64*
	@for p in $(COMMON_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
	@for p in $(ARM64_C_SRC_DIR); do \
		echo "==> Clean $$p ..."; \
		$(MAKE) clean -e ARCH=arm64 -C $(TOP_DIR)/diag/$$p || exit 1; \
	done
arm-clean:
	rm -rf $(GOPATH)/pkg/linux_arm/*
	rm -rf $(GOPATH)/bin/linux_arm/*
	rm -rf $(BUILD_DIR)/images/*arm*
	@for p in $(COMMON_C_SRC_DIR); do \
        echo "==> Clean $$p ..."; \
        $(MAKE) clean -e ARCH=arm -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
	@for p in $(ARM64_C_SRC_DIR); do \
        echo "==> Clean $$p ..."; \
        $(MAKE) clean -e ARCH=arm -C $(TOP_DIR)/diag/$$p || exit 1; \
    done
				

