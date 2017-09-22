/*
 * Simulation code of pal_dev.c
 */

#include <string.h>
#include <stdio.h>
#include "../../include/cType.h"

//=======================================
// I2C API

typedef struct i2cInfo {
    uint8* pDevName;
    uint64 i2cIdx;
    uint64 devAddr;
} i2cInfo_t;

char* tempStr     = "QSFP_0_A0";

uint8 qsfp_0_a0[]      = "QSFP_0_A0";
uint8 qsfp_0_a2[]      = "QSFP_0_A2";
uint8 qsfp_1_a0[]      = "QSFP_1_A0";
uint8 qsfp_1_a2[]      = "QSFP_1_A2";
uint8 fru[]            = "FRU";
uint8 rtc[]            = "RTC";
uint8 temp_sensor[]    = "TEM_SENSOR";
uint8 vrm_capri_dvdd[] = "VRM_CAPRI_DVDD";
uint8 vrm_capri_avdd[] = "VRM_CAPRI_AVDD";
uint8 vrm_hbm[]        = "VRM_HBM";
uint8 vrm_arm[]        = "VRM_ARM";


i2cInfo_t i2cTbl[] = {
    {qsfp_0_a0     , 0x0,   0xA0},
    {qsfp_0_a2     , 0x0,   0xA2},
    {qsfp_1_a0     , 0x1,   0xA0},
    {qsfp_1_a2     , 0x1,   0xA2},
    {fru           , 0x2,   0xA0},
    {rtc           , 0x2,   0xA2},
    {temp_sensor   , 0x2,   0x98},
    {vrm_capri_dvdd, 0x2,   0xC4},
    {vrm_capri_avdd, 0x2,   0xC4},
    {vrm_hbm       , 0x2,   0x36},
    {vrm_arm       , 0x2,   0x38},
};

typedef struct i2cRegSim {
    uint64 offset;
    uint64 value;
    uint64 numByte;
} i2cRegSim_t;


i2cRegSim_t  tps53659RegSim[] = {
    {0x00, 0x00, 2}, // Page
    {0x01, 0x00, 2}, // Operation
    {0x02, 0x00, 2}, // on_off_config
    {0x20, 0x27, 2}, // VOUT_mode
    {0x21, 0xBF, 2}, // VOUT_command
    {0x25, 0x00, 2}, // VOUT_MARGIN_HIGH
    {0x26, 0x00, 2}, // VOUT_MARGIN_LOW
    {0x79, 0xA5, 2}, // STATUS_WORD
    {0x88, 0xF029, 2}, // READ_VIN
    {0x89, 0xD14F, 2}, // READ_IIN
    {0x8B, 0x6F, 2}, // READ_VOUT
    {0x8C, 0xD131, 2}, // READ_IOUT
    {0x8D, 0xD14D, 2}, // READ_TEMP_1
    {0x96, 0xD13C, 2}, // READ_POUT
    {0x97, 0xD145, 2}, // READ_PIN
    {0xAD, 0x59, 2}, // IC_DEVICE_ID
    {0xD4, 0xD139, 2}, // MFR_SPECIFIC_04
    {0xDB, 0xBF, 2}, // VOUT_command
};

i2cRegSim_t tps549a20RegArmSim[] = {
    {0x01, 0x00, 2}, // Operation
    {0x02, 0x00, 2}, // on_off_config
    {0x79, 0xBF, 2}, // STATUS_WORD
    {0xD4, 0xD139, 2}, // MFR_SPECIFIC_04
};

i2cRegSim_t tps549a20RegHbmSim[] = {
    {0x01, 0x00, 2}, // Operation
    {0x02, 0x00, 2}, // on_off_config
    {0x79, 0xA5, 2}, // STATUS_WORD
    {0xD4, 0xD139, 2}, // MFR_SPECIFIC_04
};

int get_reg_value(i2cRegSim_t *pRegTbl, uint64 tblSize, uint64 offset, uint8 *pData, uint64 numBytes) {
    for (int i = 0; i < tblSize; i++) {
        if (pRegTbl[i].offset == offset) {
            uint64 temp = pRegTbl[i].value;
            for (int j = 0; j < numBytes; j++) {
                pData[j] = (uint8) (temp & 0xFF);
                temp = temp >> 8;
            }
            return 0;
        }
    }
    return 0;
}

int get_i2c_info (i2cInfo_t *pI2cTbl, uint64 tblSize, uint8* pDevName, i2cInfo_t **pI2cInfo) {
    for (int i = 0; i < tblSize; i++) {
        if (strcmp(pI2cTbl[i].pDevName, pDevName) == 0) {
            *pI2cInfo = &(pI2cTbl[i]);
            return 0;
        }
    }
    return -1;
} 

int64 pal_i2c_read(uint8* pDevName, uint64 offset, uint8 *pData, uint64 numBytes) {
    i2cInfo_t *pI2cinfo;
    int ret;
    uint64 tblSize = sizeof(i2cTbl)/sizeof(i2cInfo_t);
    i2cRegSim_t *pI2cReg;

    ret = get_i2c_info (i2cTbl, tblSize, pDevName, &pI2cinfo);
    if (ret != 0) {
        return ret;
    }

    if ((strcmp(pI2cinfo->pDevName, "VRM_CAPRI_DVDD") == 0) ||
        (strcmp(pI2cinfo->pDevName, "VRM_CAPRI_AVDD") == 0)) {
        pI2cReg = tps53659RegSim;
        tblSize = sizeof(tps53659RegSim)/sizeof(i2cRegSim_t);
    }
    else if (strcmp(pI2cinfo->pDevName, "VRM_HBM") == 0) {
        pI2cReg = tps549a20RegHbmSim;
        tblSize = sizeof(tps549a20RegHbmSim)/sizeof(i2cRegSim_t);
    }
    else if (strcmp(pI2cinfo->pDevName, "VRM_ARM") == 0) {
        pI2cReg = tps549a20RegArmSim;
        tblSize = sizeof(tps549a20RegArmSim)/sizeof(i2cRegSim_t);
    }

    get_reg_value(pI2cReg, tblSize, offset, pData, numBytes);

    return 0;

}

/*
 * When numByte == 0, work as PMBus send byte command
 */
int64 pal_i2c_write(uint8* pDevName, uint64 offset, uint8 *data, uint64 numBytes){
    return 0;
}


//=======================================
// SPI API - CPLD

// Is there maximum number of byte?
uint64 pal_spi_read(uint64 offset, uint8 *data, uint64 numBytes);
uint64 pal_spi_write(uint64 offset, uint8 *data, uint64 numBytes);


//=======================================
// QSPI API - QSPI flash

// Is there maximum number of byte?
uint64 pal_qspi_read(uint64 offset, uint8 *data, uint64 numBytes);
uint64 pal_qspi_write(uint64 offset, uint8 *data, uint64 numBytes);

