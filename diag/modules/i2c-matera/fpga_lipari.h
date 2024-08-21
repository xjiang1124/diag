#ifndef __FPGA_LIPARI__
#define __FPGA_LIPARI__

#define FPGA0_NUM_I2C_CONTROLLERS   19
#define FPGA1_NUM_I2C_CONTROLLERS   0
#define NUM_I2C_CONTROLLERS   (FPGA0_NUM_I2C_CONTROLLERS + \
                FPGA1_NUM_I2C_CONTROLLERS)
#define AMD_FPGA_I2C          "AMD_FPGA_I2C"
#define AMD_FPGA_ELBA         "AMD_FPGA_ELBA"
#define I2C_PRESCALE_LOW_VAL  0x7C
#define I2C_PRESCALE_HIGH_VAL 0x0

#define PCI_VENDOR_ID_AMD_FPGA      0x1dd8
#define PCI_DEVICE_ID_AMD_FPGA_I2C  0x000b
#define PCI_DEVICE_ID_AMD_FPGA_ELBA 0x000b

#define I2C_MUX_OFFSET              20
#define FPGA0_I2C_ADDRESS_START     0x400
#define FPGA1_I2C_ADDRESS_START     2560
#define FPGA0_I2C_REGISTERS_ADDRESS_SIZE  32
#define FPGA1_I2C_REGISTERS_ADDRESS_SIZE  64

#define GEN_SHOW(name, reg_offset, start_off, end_off) \
static ssize_t name##_show(struct device *dev, \
                struct device_attribute *attr, char *buf) \
{ \
    unsigned int reg_val; \
\
    reg_val = ioread32((char*)(fpga_membase) + reg_offset); \
    return sprintf(buf, "%02X", get_bits(reg_val,start_off,end_off)); \
}

#define GEN_STORE(name, reg_offset, start_off, end_off) \
static ssize_t name##_store(struct device *dev, \
                struct device_attribute *attr, const char *buf, size_t len) \
{ \
    unsigned long val; \
    unsigned int  reg_val; \
    int ret; \
\
    ret = kstrtoul(buf, 0, &val); \
    if (ret < 0) \
        return ret; \
\
    reg_val = ioread32((char*)(fpga_membase) + reg_offset); \
    iowrite32(update_bits(reg_val,val,start_off,end_off),(char*)(fpga_membase) + reg_offset); \
    return len; \
}
int ocores_i2c_probe(struct pci_dev *pdev, void* base, int instance,
                            int controller_id, uint32_t i2c_start_addr,
                            uint32_t i2c_register_range);
int ocores_i2c_remove(struct pci_dev *pdev,
                             int controller_id);
#endif
