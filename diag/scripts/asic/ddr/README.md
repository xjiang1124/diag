Documentation for How to Use rcfgsToText.py

First, set the environment for ipython to run

tcsh
setenv AWS /home/$USER
setenv AWSD /vol/dump/$USER
 
setenv ASIC_SRC $AWS/workspace/asic
setenv ASIC_GEN $AWSD/workspace/asic
setenv ASIC_COMMON /home/asic
source $ASIC_COMMON/templates/cshrc_include
setenv ASIC_GEN_X86_64 $AWSD/workspace/giglio_amd64
setenv ASIC_GEN_ARM64 $AWSD/workspace/giglio_arm64
 
 
cd ~/workspace/asic/ip/cosim/giglio/ddr/regconfig/ginestra-D5/5600


Then, run ipython:

ipython


Run the two commands:

run ../../gen_overlay_uboot_ddr5_tables.py ginestra_D5

run ~/workspace/asic/ip/cosim/giglio/ddr/regconfig/ginestra-D5/5600/rcfgsToText.py ginestra_D5


It should generate 3 files titled "CTLgenFunc.tcl", "PIgenFunc.tcl", and "PHYgenFunc.tcl".
