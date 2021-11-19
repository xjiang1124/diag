package main

import (
//    "flag"
    "common/spi"
    "common/diagEngine"
    "common/cli"
    "common/dcli"
    "common/errType"
    "common/misc"
    "config"
    "os"
    "time"
    "math/rand"
)

//========================================================
// Constant definition
const (
    // Each DSP should know it own name
    dspName = "MVL"
)

const MVL_ID = 0x115
const MVL_ID_REG = 0x3

func Mvl_Init() {
    //in case no EEPROM
}

func Mvl_AccHdl(argList []string) {
    var data uint32
    var data1 uint32
    var rc int = 0
    var ExtendedRegTest bool = true
    cardInfo := diagEngine.GetCardInfo()
    cardType := cardInfo.CardType

    // FIXME: after mgmt port init, the very first read will get junk value. 
    // adding a second read for a work around. Need to remove this after root cause
    spi.MvlRegRead(MVL_ID_REG, &data, 0x10)
    spi.MvlRegRead(MVL_ID_REG, &data1, 0x10)
    cli.Printf("d", "1st MVL_ID_REG = 0x%x", data)
    cli.Printf("d", "2nd MVL_ID_REG = 0x%x", data1)
    if (data >> 4) != MVL_ID {
        cli.Printf("d", "Marvell Chip ID first read Failed.  Read 0x%x  Expect 0x%x  Mask=0xFFF0", data, (MVL_ID<<4) )
    }
    if (data1 >> 4) != MVL_ID {
        dcli.Printf("e", "Marvell Chip ID Failed.  Read 0x%x  Expect 0x%x  Mask=0xFFF0", data1, (MVL_ID<<4) )
        rc = -1
    }

    //Strip off secure boot indicator in the rev if it's there
    spi.CpldRead(0x00, &data)
    if data > 0x80 {
        data = data - 0x80
    }
    // Check if the card under test has the MDIO Fix based on the CPLD Rev.  
    // If it doesn't skip the more stressful MDIO test to the Marvell Switch
    if (cardType == "NAPLES100" && data < 0x10) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES100IBM" && data < 0x06) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES100HPE" && data < 0x04) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES100DELL" && data < 0x04) {
        ExtendedRegTest = false;
    } else if (cardType == "ORTANO" && data < 0x02) {
        ExtendedRegTest = false;
    } else if (cardType == "ORTANO2" && data < 0x02) {
        ExtendedRegTest = false;
    } else if (cardType == "ORTANO2A" && data < 0x02) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES25" && data < 0x0C) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES25OCP" && data < 0x0B) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES25SWM" && data < 0x0F) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES25SWMDELL" && data < 0x05) {
        ExtendedRegTest = false;
    } else if (cardType == "NAPLES25SWM833" && data < 0x03) {
        ExtendedRegTest = false;
    } 

    if rc == 0 && ExtendedRegTest == true {
        rc = mwsr_reg_test(100)
    } else {
        dcli.Printf("i", "Skipping Extended MDIO Test due to CPLD Rev 0x%.02x\n", data)
    }   

    if rc == 0 {
        dcli.Println("i", "MVL acc test passed!")
        diagEngine.FuncMsgChan <- errType.SUCCESS
        
    } else {
        dcli.Println("e", "MVL acc test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    }
    return
}

func mwsr_reg_test(loopCnt int) (err int) {
    var registers = []uint32{ 0x0D, 0x0E, 0x0F }
    var pattern = []uint32{ 0xAAAA, 0x5555, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 }
    
    var data32 = make([]uint32, 3)
    var MVSW_GLBL1_MDIO_ADDR uint32 = 0x1B


    randNum := rand.New(rand.NewSource(time.Now().UnixNano()))
    
    dcli.Printf("i", "\n...\n")
    //There are 3 registers in global that have full 16-bit read/write access.  Run patterns 0xAAAA, 0x5555, and one random pattern though them
    for i:=0; i<loopCnt; i++ {
        pattern[2] = (randNum.Uint32() & 0xFFFF)
        err = spi.MvlRegWrite(registers[0], pattern[(i) % 3], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegWrite Failed.  err=%d\n", err); 
            err = -1
            return
        }
        err = spi.MvlRegWrite(registers[1], pattern[(i+1) % 3], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegWrite Failed.  err=%d\n", err); 
            err = -1
            return
        }
        err = spi.MvlRegWrite(registers[2], pattern[(i+2) % 3], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegWrite Failed.  err=%d\n", err);
            err = -1
            return
        }

        err = spi.MvlRegRead(registers[0], &data32[0], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegRead Failed.  err=%d\n", err);
            err = -1
            return
        }
        err = spi.MvlRegRead(registers[1], &data32[1], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegRead Failed.  err=%d\n", err);
            err = -1
            return
        }
        err = spi.MvlRegRead(registers[2], &data32[2], MVSW_GLBL1_MDIO_ADDR)
        if err != 0 {  
            dcli.Printf("e", " spi.MvlRegRead Failed.  err=%d\n", err);
            err = -1
            return
        }

        if data32[0] != pattern[(i) % 3] {
            dcli.Printf("e", " Data Compare Failed Reg=0x%x  WROTE/READ = 0x%x / 0x%x \n", registers[0], pattern[(i) % 3], data32[0]); 
            err = -1
            return 
        }
        if data32[1] != pattern[(i+1) % 3] {
            dcli.Printf("e", " Data Compare Failed Reg=0x%x  WROTE/READ = 0x%x / 0x%x \n", registers[1], pattern[(i+1) % 3], data32[1]); 
            err = -1
            return
        }
        if data32[2] != pattern[(i+2) % 3] {
            dcli.Printf("e", " Data Compare Failed Reg=0x%x  WROTE/READ = 0x%x / 0x%x \n", registers[2], pattern[(i+2) % 3], data32[2]); 
            err = -1
            return
        }

        //Test MDIO Device Address. Write register 0x0F of each port.  Will use random data.
        for j:=0x0;j<0x7;j++ {
            pattern[j] = (randNum.Uint32() & 0xFFFF)
            err = spi.MvlRegWrite(0x0F, pattern[j], uint32(0x10 + j))
            if err != 0 {  
                dcli.Printf("e", " spi.MvlRegWrite Failed.  err=%d\n", err); 
                err = -1
                return
            }
        }
        //Test MDIO Device Address by writing/reading register 0x0F of each port.  Will use random data.
        for j:=0x0;j<0x7;j++ {
            err = spi.MvlRegRead(0x0F, &data32[0], uint32(0x10 + j))
            if err != 0 {  
                dcli.Printf("e", " spi.MvlRegWrite Failed.  PORt=%d  err=%d\n", j,  err);
                err = -1
                return
            }
            if pattern[j] != data32[0] {
                dcli.Printf("e", " Data Compare Failed.  PORT=%d Reg=0x0F  WROTE/READ = 0x%x / 0x%x \n", j, pattern[j], data32[0]); 
                err = -1
                return
            }
        }

        for j:=0x0;j<0x7;j++ {
            err = spi.MvlRegWrite(0x0F, 0x9100, uint32(0x10 + j))
            if err != 0 {  
                dcli.Printf("e", " spi.MvlRegWrite Failed.  err=%d\n", err); 
                err = -1
                return
            }
        }
        if  i % 100 == 0 {
            dcli.Printf("i", ".")
        }
    }
    dcli.Printf("i", "\n")
    return
}


func Mvl_StubHdl(argList []string) {

    var data0, data1 uint32
    err := 0

    spi.MvlSmiRegWrite(0x16, 0x6, 0x3)
    misc.SleepInSec(1)
    spi.MvlSmiRegWrite(0x12, 0x18, 0x3)
    misc.SleepInSec(1)
    spi.MvlSmiRegWrite(0x10, 0x18, 0x3)
//    misc.SleepInSec(1)
//    spi.MvlSmiRegWrite(0x12, 0x18, 0x3)

    misc.SleepInSec(1)

    //check error counter
    spi.MvlSmiRegRead(0x11, &data0, 0x3)
    if (data0 & 0xFF) != 0 {
       dcli.Printf("e", "Port 3 stub test has error, counter reg 0x%x\n", data0)
       err = 1
    } else if data0 == 0 {
        dcli.Println("e", "Port 3 stub test has no packet")
        err = 1
    } else {
        dcli.Printf("i", "Port 3 stub test passed! 0x%x\n", data0)
    }
    spi.MvlSmiRegWrite(0x10, 0x0, 0x3)
    spi.MvlSmiRegWrite(0x12, 0x0, 0x3)
    spi.MvlSmiRegWrite(0x16, 0x0, 0x3)

    misc.SleepInSec(1)

    if os.Getenv("CARD_TYPE") == "NAPLES100" {
        spi.MvlSmiRegWrite(0x16, 0x6, 0x4)
        misc.SleepInSec(1)
        spi.MvlSmiRegWrite(0x12, 0x18, 0x4)
        misc.SleepInSec(1)
        spi.MvlSmiRegWrite(0x10, 0x18, 0x4)
    //    spi.MvlSmiRegWrite(0x12, 0x18, 0x4)

        misc.SleepInSec(1)

        spi.MvlSmiRegRead(0x11, &data1, 0x4)
        if (data1 & 0xFF) != 0 {
           dcli.Printf("e", "Port 4 stub test has error, counter reg 0x%x\n", data1)
           err = 1
        } else if data1 == 0 {
            dcli.Println("e", "Port 4 stub test has no packet")
            err = 1
        } else {
            dcli.Printf("i", "Port 4 stub test passed! 0x%x\n", data1)
        }

        spi.MvlSmiRegWrite(0x10, 0x0, 0x4)
        spi.MvlSmiRegWrite(0x12, 0x0, 0x4)
        spi.MvlSmiRegWrite(0x16, 0x0, 0x4)
        misc.SleepInSec(5)
    }

    dcli.Println("i", "MVL stub test cleanup")
    if err == 1 {
        dcli.Println("e", "MVL stub test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func Mvl_TrfHdl(argList []string) {
    var data uint32

    //get packet number, port mask
    //start traffic

    //check error counter
    if data != MVL_ID {
        dcli.Println("e", "MVL acc test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func Mvl_LedHdl(argList []string) {
    var data uint32

    //duration, port mask?

    spi.MvlRegRead(MVL_ID_REG, &data, 0x3)
    if data != MVL_ID {
        dcli.Println("e", "MVL acc test failed!")
        diagEngine.FuncMsgChan <- errType.FAIL
    } else {
        diagEngine.FuncMsgChan <- errType.SUCCESS
    }
    return
}

func main() {
    diagEngine.FuncMap = make(map[string]diagEngine.TestFn)
    diagEngine.FuncMap["ACC"]    = Mvl_AccHdl
    diagEngine.FuncMap["STUB"]    = Mvl_StubHdl
    diagEngine.FuncMap["TRF"]    = Mvl_TrfHdl
    diagEngine.FuncMap["LED"]    = Mvl_LedHdl

    dcli.Init("log_"+dspName+".txt", config.OutputMode)
    diagEngine.CardInfoInit(dspName)
    diagEngine.DspInfraInit()
    diagEngine.DspInfraMainLoop()
}
