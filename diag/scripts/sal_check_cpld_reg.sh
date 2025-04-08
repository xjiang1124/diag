#!/bin/bash  

slot=$1
echo "=========================================="
echo "Checking CPLD REG of slot $slot"

# Define the data structure as an associative array  
declare -A registers=(  
    # Format: HEX_OFFSET="start_bit end_bit expected_hex_value help_info;..."  
    # ["0x01"]="0 3 0x5 'Control Bit 1';6 7 0x1 'Status Bit 2'"  

    # HEX_OFFSET    start_bit   stop_bit    Expected_hex_value  Help_info
    ["0x01"]="      2           2           0x0                 'CPLD boot image: 0 CFG0, 1 CFG1'"  
    ["0x14"]="      0           3           0x7                 'PLL Lock'" 
    ["0x30"]="      0           7           0x0                 'Power/reset code'"  
    ["0x32"]="      0           7           0x0                 'Power fault'"  
    ["0x60"]="      0           7           0x0                 'Power failure code 01'"  
    ["0x61"]="      0           7           0x0                 'Power failure code 02'"  
    ["0x62"]="      7           7           0x0                 'JTAG Sequence failure'"  
    ["0xC0"]="      1           2           0x3                 'Ext clk buffer lock'"  
    # Add more registers and configurations as needed  
)  
  
SLAVE_ADDRESS="0x4a"  # Example slave address in hex  
  
# Function to mock reading register (replace with actual command to read hardware)  
read_register() {  
    local slave_addr="$1"  
    local offset="$2"  
    # Example: Replace with actual hardware read command.  
    #echo "$((RANDOM % 255))"  # Return a random value between 0-255 (8 bits)  
    reg_data=$(i2cget -y $((slot+2)) 0x4a $offset)
    echo $reg_data
}  
  
# Function to calculate bit mask  
calculate_mask() {  
    local start_bit="$1"  
    local end_bit="$2"  
    echo $(( ((1 << (end_bit - start_bit + 1)) - 1) << start_bit ))  
}  

mismatch="NO"

# Walk through registers and check values  
for hex_offset in "${!registers[@]}"; do  
    # Convert register offset from hex to decimal if needed for reading  
    offset=$((hex_offset))  
  
    # Read the register value once for efficiency  
    reg_value=$(read_register "$SLAVE_ADDRESS" "$offset")  
    #echo "reg_value: $reg_value"
  
    # Split the configurations for this offset  
    IFS=';' read -ra bit_configs <<< "${registers[$hex_offset]}"  
      
    # Check each bit configuration  
    for bit_config in "${bit_configs[@]}"; do  
        IFS=' ' read -r start_bit end_bit expected_hex_value help_info <<< "$bit_config"  

        #echo "$hex_offset $start_bit $end_bit $expected_hex_value $help_info"

        # Convert expected value from hex to decimal  
        expected_value=$((expected_hex_value))  
  
        # Extract the bits we need  
        mask=$(calculate_mask "$start_bit" "$end_bit")  
        #echo "mask $mask"
        actual_value=$(( (reg_value & mask) >> start_bit ))  
  
        # Print only if there is a mismatch  
        if [ "$actual_value" -ne "$expected_value" ]; then  
            printf "Mismatch at REG %s[%d:%d] %s: Read 0x%X, Expected 0x%X \n" \
                   "$hex_offset" "$end_bit" "$start_bit" "$help_info" "$actual_value" "$expected_value"  
            mismatch="YES"
        fi  
    done  
done  

if [[ $mismatch == "YES" ]]
then
    echo "Mismatch HAPPENED"
else
    echo "Mismatch not found"
fi

printf "\n------------------------------------\n"
echo "Dump I2C registers"
i2cdump -y $((slot+2)) 0x4a

