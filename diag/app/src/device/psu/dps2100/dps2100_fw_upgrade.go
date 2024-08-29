package dps2100

import (
    "fmt"
    "os"
    "bufio"
    "strconv"
    "strings"
    //"unicode"
    "common/cli"
    "common/errType"
    "protocol/pmbus"
    "protocol/smbus"
    "hardware/i2cinfo"
    //"device/fpga/liparifpga"
)


func WriteFWuploadMode(devName string, data byte) (revision uint16, err int) {
    err = pmbus.Open(devName)
    if err != errType.SUCCESS {
        return
    }
    err = pmbus.WriteByte(devName, MFR_FWUPLOAD_MODE, data)
    pmbus.Close()
    return
}


func ReadFWuploadMode(devName string) (data uint8, err int) {
    err = smbus.Open(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to open device", devName)
        return
    }
    data, err = pmbus.ReadByte(devName, MFR_FWUPLOAD_MODE)
    smbus.Close()
    return
}

func WriteFWupload(devName string, dataSlice []uint8) (err int) { 
    var iInfo i2cinfo.I2cInfo
    var bus, mux uint32
    wrData := []byte{}
    

    if i2cinfo.CardType == "LIPARI" {
        iInfo, err = i2cinfo.GetI2cInfo(devName)
        if err != errType.SUCCESS {
            cli.Println("e", "Failed to obtain I2C info of", devName)
            return
        }

        strArr := strings.Split(iInfo.HubName, "_")
        tmp, _ := strconv.Atoi(strArr[0])
        bus = uint32(tmp)
        tmp, _ = strconv.Atoi(strArr[1])
        mux = uint32(tmp)
    } else if i2cinfo.CardType == "MTP_MATERA" {
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
    wrData = append(wrData, MFR_FWUPLOAD)
    wrData = append(wrData, dataSlice...)


    fmt.Printf(" Bus=%d Mux=%d\n", bus, mux)
    fmt.Printf("\n");
    for i:=0; i<len(wrData);i++ {
        fmt.Printf("%.02x ", wrData[i])
    }
    fmt.Printf("\n");

    /*
    mfgId, errGo = taorfpga.I2c_access( uint32(iInfo.Bus - 1), uint32(iInfo.HubPort), uint32(iInfo.DevAddr), uint32(len(wrData)), wrData, MFG_ID_BLK_SIZE + 1 )
    if errGo != nil {
        err = errType.FAIL
        return
    }
    if len(mfgId) != MFG_ID_BLK_SIZE + 1 {
        err = errType.FAIL
        cli.Printf("e", "%s Length of MfgID is wrong.   Len=%d.  Expect=%d", devname, len(mfgId), MFG_ID_BLK_SIZE + 1)
    }
    for i:=0; i<(MFG_ID_BLK_SIZE + 1); i++ {
        if expected[i] != mfgId[i] {
            err = errType.FAIL
            cli.Printf("e", "%s: MFG ID is wrong.  Expected[%d]=%.02x     Read[%d]=%.02x", devname, i, expected[i], mfgId[i])
        }
    }*/
    return
}


func WriteFirmware(filename string, psuNumber int) (err error) {
    fileData := []uint8{}
    ImageInformation := []byte{}
    ModelName := []byte{}
    var BlockSize uint8
    var WriteTime uint16
    var devName string

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


    WriteFWupload(devName, fileData[0:64])


    for i:=0;i<len(fileData);i+=int(BlockSize) {
        fmt.Printf(".")
    }

    return
}

