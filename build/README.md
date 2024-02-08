#========================
# Build command format
# If asic is not specified, will build images for all ASICs
# If asiclib is not specified, will build with stable nic.tar.gz (asic parameter has to be specified)
make <amd64|arm64> [asic=<asic_type>] [asiclib=<stable|latest]

#========================
# Examples

# Build for all ASICs
make amd64
make arm64

# Build for Elba with stable version of nic.tar.gz
make amd64 asic=elba

# Build for Elba with latest version of nic.tar.gz
make amd64 asic=elba asiclib=latest
