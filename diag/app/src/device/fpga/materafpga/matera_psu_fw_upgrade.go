package materafpga

import (
    "fmt"
    "os"
    "bufio"
    "time"
    //"unicode"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
    "hardware/i2cinfo"
)

const (
    //dps2100 Reg 0xD6
    EXIT_FIRMWARE_UPLOAD_MODE = 0x00
    FIRMWARE_UPLOAD_MODE      = 0x01

    //dps2100 Reg 0xD8
    FULL_IMAGE_RECEIVED         = 0x00
    FULL_IMAGE_NOT_RECEIVED_YET = 0x01
    BAD_IMAGE_RECEIVED          = 0x02
    IMAGE_NOT_SUPPORTED         = 0x04
)

const PSU_I2C_ADDR uint32 = 0x58


/***************************************************************************************************** 
*  GENERAL INFO:
*  
*  Code will drive i2c directly through the FPGA for OP codes 0xD6 and 0xD7
*  The main problem is 0xD7 requires a block write of 67 BYTES (1 op + 1 blck size + 64 data + 1 PEC)
*  The diag i2c driver and linux binary i2cset do not support block writes that large
* 
*  Those two op codes also require PEC to function.
* 
* 
*****************************************************************************************************/ 



/**********************************************************************
* 
* Get the BUS and MUX info to access I2C from the FPGA (not /dev/i2c)
* 
***********************************************************************/ 
func GetBusInfo(devName string) (bus uint32, mux uint32, err int) {
    if i2cinfo.CardType == "MTP_MATERA" {
        if devName == "PSU_1" {
            bus = 11
            mux = 0
        } else if devName == "PSU_2" {
            bus = 12
            mux = 0
        } else {
            fmt.Printf(" ERROR: Invalid Device Name %s\n", devName)
            err = errType.FAIL
            return
        }

    } else {
        fmt.Printf(" ERROR: This command is only supported on Lipari and Matera MTP.  CardType=%s\n", i2cinfo.CardType)
        err = errType.FAIL
        return  
    }
    return
}


func ReadFWuploadStatus(devName string) (data uint16, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    data, err = pmbus.ReadWord(devName, pmbus.MFR_SPECIFIC_D8)
    smbus.Close()
    return
}


func ReadFWuploadMode(devName string) (data uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    data, err = pmbus.ReadByte(devName, pmbus.MFR_SPECIFIC_D6)
    smbus.Close()
    return
}


func WriteFWuploadMode(devName string, data byte) (err int) {
    var bus, mux uint32
    wrData := []byte{}
    i2cAddr := []byte{ uint8(PSU_I2C_ADDR<<1) }
    var errGo error
    
    bus, mux, err = GetBusInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    wrData = append(wrData, pmbus.MFR_SPECIFIC_D6)
    wrData = append(wrData, data)

    pec, _ := pmbus.I2C_generate_pec(0x00, i2cAddr)
    pec, _  = pmbus.I2C_generate_pec(pec, wrData)
    wrData = append(wrData, pec)

    fmt.Printf(" Bus=%d Mux=%d\n", bus, mux)
    fmt.Printf("\n");
    for i:=0; i<len(wrData);i++ {
        fmt.Printf("%.02x ", wrData[i])
    }
    fmt.Printf("\n");

    _ , errGo = I2c_access( uint32(bus), uint32(mux), uint32(PSU_I2C_ADDR), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        err = errType.FAIL
        return
    }

    return
}


func BlockWriteCmdFWupload(devName string, BlockSize uint8, WriteTime uint16, dataSlice []uint8) (err int) { 
    var bus, mux uint32
    wrData := []byte{}
    i2cAddr := []byte{ uint8(PSU_I2C_ADDR<<1) }
    var errGo error
    
    bus, mux, err = GetBusInfo(devName)
    if err != errType.SUCCESS {
        return
    }

    wrData = append(wrData, pmbus.MFR_SPECIFIC_D7)
    wrData = append(wrData, BlockSize)
    wrData = append(wrData, dataSlice...)

    pec, _ := pmbus.I2C_generate_pec(0x00, i2cAddr)
    pec, _  = pmbus.I2C_generate_pec(pec, wrData)
    wrData = append(wrData, pec)

    fmt.Printf("\n");
    for i:=0; i<len(wrData);i++ {
        fmt.Printf("%.02x ", wrData[i])
    }
    fmt.Printf("\n");

    fmt.Printf(" Bus=%d Mux=%d\n", bus, mux)
    _ , errGo = I2c_access( uint32(bus), uint32(mux), uint32(PSU_I2C_ADDR), uint32(len(wrData)), wrData, 0 )
    if errGo != nil {
        err = errType.FAIL
        return
    } 

    time.Sleep(time.Duration(WriteTime) * time.Millisecond)

    return
}


func WriteFirmware(filename string, psuNumber int) (err error) {
    fileData := []uint8{}
    ImageInformation := []byte{}
    ModelName := []byte{}
    var BlockSize uint8
    var WriteTime uint16
    var devName string
    var errT int
    var data8 uint8
    var data16 uint16

    fmt.Printf("Opening file %s\n", filename)
    fmt.Printf("PSUNumber=%d\n", psuNumber)

    if psuNumber == 0 {
        devName = "PSU_1" 
    } else if psuNumber == 1 {
        devName = "PSU_2" 
    } else {
        fmt.Printf("ERROR: PSU number passed to function need to be 0 or 1.  You passed %d\n", psuNumber)
        return
    }


    f, err := os.Open(filename)
    if err != nil {
        fmt.Printf(" Failed to open filename=%s.   ERR=%s\n", filename, err)
        return
    }
    defer f.Close()

    fmt.Printf(" Programming Image %s to CPLD flash\n", filename)

    scanner := bufio.NewScanner(f)
    scanner.Split(bufio.ScanBytes)

    // Use For-loop.
    for scanner.Scan() {
        b := scanner.Bytes()
        fileData = append(fileData, b[0])
    }
    fmt.Printf(" Length File Data = %d\n", len(fileData))

    ImageInformation = append(fileData[2:10])
    ModelName = append(fileData[10:21])
    BlockSize = fileData[28]
    WriteTime = (uint16(fileData[30]) | (uint16(fileData[31]<<8)))

    fmt.Printf("Image Information='%s'\n", string(ImageInformation))
    fmt.Printf("ModelName        ='%s'\n", string(ModelName))
    fmt.Printf("FW MAJOR BIT       -> 0x%x\n", fileData[23])
    fmt.Printf("FW MINOR PRIMARY   -> 0x%x\n", fileData[24])
    fmt.Printf("FW MINOR SECONDARY -> 0x%x\n", fileData[25])
    fmt.Printf("BLOCK SIZE -> 0x%x\n", BlockSize)
    fmt.Printf("WRITE TIME -> 0x%x\n", WriteTime)

    //ENTER FIRMWARE UPDATE MODE
    errT =  WriteFWuploadMode(devName, EXIT_FIRMWARE_UPLOAD_MODE) 
    if errT != errType.SUCCESS {
        cli.Printf("e", "Device %s Failed to Write %.02x to MFG_FWUPLOAD_MODE", devName, FIRMWARE_UPLOAD_MODE)
        return
    }
    time.Sleep(time.Duration(1000) * time.Millisecond)
    data8, errT = ReadFWuploadMode(devName)
    fmt.Printf(" FWUPLOAD MODE=%d (EXPECT 0x00)\n", data8)

    errT =  WriteFWuploadMode(devName, FIRMWARE_UPLOAD_MODE) 
    if errT != errType.SUCCESS {
        cli.Printf("e", "Device %s Failed to Write %.02x to MFG_FWUPLOAD_MODE", devName, FIRMWARE_UPLOAD_MODE)
        return
    }
    time.Sleep(time.Duration(500) * time.Millisecond)

    for j:=0;j<10;j++ {
        //check if it went into updat emode
        data8, errT = ReadFWuploadMode(devName)
        if errT != errType.SUCCESS {
            cli.Printf("e", "Device %s Failed to Read MFG_FWUPLOAD_MODE", devName)
            return
        }
        if data8 == FIRMWARE_UPLOAD_MODE {
            fmt.Printf("j=%d,  FIRMWARE_UPLOAD_MODE=%x\n", j, data8)
            break
        }
    }

    data16, _ = ReadFWuploadStatus(devName)
    fmt.Printf(" FW Upload Status=%.02x\n", data16)

    for i:=0;i<len(fileData);i+=int(BlockSize) {
        var offset int = i
        errT = BlockWriteCmdFWupload(devName, BlockSize, WriteTime, fileData[offset:(offset+int(BlockSize))])
        if errT != errType.SUCCESS {
            cli.Printf("e", "Device %s FWUPLOAD Function failed", devName)
            //Attempt to take the PSU out of fwupdate mode and put it back it normal operating mode
            WriteFWuploadMode(devName, EXIT_FIRMWARE_UPLOAD_MODE) 
            return
        }
        data16, _ = ReadFWuploadStatus(devName)
        fmt.Printf(" FW Upload Status=%.02x\n", data16)
        
        fmt.Printf(".")
    }

    data16, _ = ReadFWuploadStatus(devName)
    fmt.Printf(" FW Upload Status=%.02x\n", data16)
    time.Sleep(time.Duration(1000) * time.Millisecond)
    data16, _ = ReadFWuploadStatus(devName)
    fmt.Printf(" FW Upload Status=%.02x\n", data16)
    time.Sleep(time.Duration(1000) * time.Millisecond)
    errT =  WriteFWuploadMode(devName, EXIT_FIRMWARE_UPLOAD_MODE) 
    if errT != errType.SUCCESS {
        cli.Printf("e", "Device %s Failed to Write %.02x to MFG_FWUPLOAD_MODE", devName, EXIT_FIRMWARE_UPLOAD_MODE)
        return
    }

    return
}

