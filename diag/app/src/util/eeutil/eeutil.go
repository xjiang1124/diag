package main

import (
    "fmt"
    "flag"
    "os"
    "strings"
    "unicode"

    "common/cli"
    "common/errType"
    "common/misc"
    //"config"
    "hardware/hwdev"
    "hardware/hwinfo"
    "hardware/i2cinfo"
    "device/eeprom"
    "device/cpld/cpldSmb"
)


const NAPLES25SWM_PEN       string  = "68-0016-01 01"   //SWM Pesnando Sku
const NAPLES25SWM_PEN_TAA   string  = "68-0017-01 01"   //SWM Pesnando TAA Sku
const NAPLES25SWM_HPE_E     string  = "P26968-001"      //SWM HPE Enterprise
const NAPLES25SWM_HPE_E_TAA string  = "P46653-001"      //SWM HPE Enterprise TAA
const NAPLES25SWM_HPE_C     string  = "P41851-001"      //SWM HPE Cloud

const NAPLES25OCP_HPE_E   string  = "P37689-001"
const NAPLES25OCP_HPE_C   string  = "P41857-001"
const NAPLES25OCP_PEN     string  = "68-0010-01 01"
const NAPLES25OCP_DELL    string  = "68-0010"  
const MTPOCPADAPTER       string  = "73-0024-03"

const NAPLES100_HPE_E     string  = "P37692-001"      //Enterprise
const NAPLES100_HPE_C     string  = "P41854-001"      //Cloud
                                                      //
const NAPLES200_ORT_V2    string  = "68-0015-02 01"   //ORTANO Oracle
const NAPLES200_ORT_V2A   string  = "68-0026-01 01"   //ORTANO ADI Oracle
const NAPLES200_ORT_V2I   string  = "68-0029-01 02"   //ORTANO Interposer Oracle
const NAPLES200_PEN       string  = "68-0021-02 01"   //ORTANO Pensando
const NAPLES200_IBM       string  = "68-0028-01 01"   //ORTANO IBM
const NAPLES200_TAOR      string  = "68-0018-01 01"   //TAORMINA ORTANO Pensando
const NAPLES200_TAOR2     string  = "73-0040-03 A2"   //TAORMINA ORTANO Pensando (newer part number)
const NAPLES200_LIPARI    string  = "68-0032-01 01"   //LIPARI SWITCH ELBA
const NAPLES200_MTFUJI    string  = "73-21403-01"     //MTFUJI SWITCH ELBA


const LACONA16GB_HPE     string  = "P47927-001"
const LACONA32GB_HPE     string  = "P47930-001"

func init() {
    //procNameTemp := strings.Split(os.Args[0], "/")
    //procName := procNameTemp[len(procNameTemp)-1]
    //cli.Init("log_"+procName+".txt", config.OutputMode)
}

func dispInfo() {
    var outStr string
    var fmtStr = "%-15s"
    // Titles
    i2cTitle := []string {"DEV_NAME", "COMP", "BUS", "DEV_ADDR", "PAGE(PMBus)"}
    for _, title := range(i2cTitle) {
        outStr = outStr + fmt.Sprintf(fmtStr, title)
    }
    cli.Println("i", outStr)
    cli.Println("i", "-----------------------------------------------------------------------")

    for _, eeprom := range(hwinfo.EepromList) {
        i2cinfo.DispI2cInfo(eeprom)
    }
}

func eepromTlbInit(uut string, pn string, update bool, dev string) (err int) {

    if pn == MTPOCPADAPTER || eeprom.CustType == "MTPOCPADAPTER" {
        // OCP Adapter, CARD_TYPE not supported in env!
        eeprom.CustType = "MTPOCPADAPTER"
        eeprom.CardType = "MTPOCPADAPTER"
        eeprom.EepromTbl = eeprom.MtpOcpAdapTbl
        fmt.Printf(" OCP Adapter\n");
        return 0
    }

    var cardType string
    var mtpType string

    //UUT NONE ASSUMES YOU ARE ON ARM OR YOU NEED TO PROGRAM AN MTP
    //IF UUT IS ENTERED YOU ARE ON THE MTP PROGRAMMING FROM THE SMBUS SIDE
    if (uut == "UUT_NONE") {
        cardType = os.Getenv("CARD_TYPE")
    } else {
        cardType = os.Getenv(uut)
    }
    eeprom.CardType = cardType


    if (strings.Contains(cardType, "MTP")) {
        mtpType = os.Getenv("MTP_TYPE")
        if ( mtpType == "MTP_TURBO_ELBA" ) {
            eeprom.EepromTbl = eeprom.MtpTurboTbl
        } else if ( mtpType == "MTP_MATERA" || mtpType == "MTP_PANAREA") {
            eeprom.CustType = "MTP_MATERA"
            eeprom.EepromTbl = nil
            if strings.Contains(dev, "FRU") || strings.Contains(dev, "MB") {
                eeprom.EepromTlvs = eeprom.MtpMateraMbTlvs
            } else if strings.Contains(dev, "IOB") {
                eeprom.EepromTlvs = eeprom.MtpMateraIobTlvs
            } else if strings.Contains(dev, "FPIC") {
                eeprom.EepromTlvs = eeprom.MtpMateraFpicTlvs
            } else {
                cli.Println("e", "Not supported MTP_TYPE", mtpType, "devName", dev)
                return errType.FAIL
            }
        } else {
            eeprom.EepromTbl = eeprom.MtpTbl
        }
    } else {
        eeprom.EepromTbl = eeprom.Naples100Tbl
        if eeprom.HpeNaples == 1 {
            eeprom.EepromExtTbl = eeprom.HpeTbl
        }
        if (eeprom.HpeSwm == 1 || (cardType == "NAPLES25SWM")) && eeprom.HpeAlom != true {
            //This card support multiple part numbers which unfortunately do not use the same formated table.  
            //Need to sort out which table to use based on the part number the user provided 
            if update == true {
                //FOR NOW JUST MAKE THEM ENTER A PART NUMBER, BUT WE CAN DIG THIS OUT OF A PROGRAMMED FRU...
                if pn == "" {
                    cli.Println("e", "For Programming Naples25 SWM, you must enter a part number")
                    return -1;
                }
                if pn[0:5] == NAPLES25SWM_HPE_E[0:5] {          //ENTERPRISE
                    eeprom.EepromTbl = eeprom.HpeTblSWM
                    eeprom.EepromExtTbl = eeprom.HpeTblSWMext
                    eeprom.HpeSwm = 1  
                    fmt.Printf(" HPE 25 SWM\n");
                } else if pn[0:5] == NAPLES25SWM_HPE_E_TAA[0:5] {  //ENTERPRISE TAA
                    eeprom.EepromTbl = eeprom.HpeTblSWMTAA
                    eeprom.EepromExtTbl = eeprom.HpeTblSWMTAAext
                    eeprom.HpeSwm = 1  
                    fmt.Printf(" HPE 25 SWM TAA\n");
                } else if pn[0:5] == NAPLES25SWM_HPE_C[0:5] {   //CLOUD
                    eeprom.EepromTbl = eeprom.HpeTblSWMCLOUD
                    eeprom.EepromExtTbl = eeprom.HpeTblSWMCLOUDext
                    eeprom.HpeSwm = 1  
                    fmt.Printf(" HPE 25 SWM CLOUD\n");
                } else if pn[0:7] == NAPLES25SWM_PEN_TAA[0:7] {      
                    eeprom.EepromTbl = eeprom.PenTblSWMTAA
                    eeprom.HpeSwm = 2  
                    eeprom.CustType = "PENSWM"
                    //NO EXTENDED TABLE (Product Information Area)
                    fmt.Printf(" PEN SWM TAA\n");
                } else if pn[0:7] == NAPLES25SWM_PEN[0:7] {   
                    eeprom.EepromTbl = eeprom.PenTblSWM
                    eeprom.HpeSwm = 2  
                    eeprom.CustType = "PENSWM"
                    //NO EXTENDED TABLE (Product Information Area)
                    fmt.Printf(" PEN SWM\n");
                } else {
                    cli.Println("e", "Invalid Part Number '",pn,"' Entered For Programming Naples25 SWM")
                    return -1;
                }
            } 
        }
        if eeprom.HpeOcp == 1 || eeprom.DellOcp == 1 || (cardType == "NAPLES25OCP") {
            if update == true {
                if pn == "" {
                    cli.Println("e", "For Programming Naples25OCP HPE, you must enter a part number")
                    return -1;
                }
                if pn[0:5] == NAPLES25OCP_HPE_E[0:5] {          //ENTERPRISE
                    eeprom.EepromTbl = eeprom.HpeTblOCP
                    eeprom.EepromExtTbl = eeprom.HpeTblOCPext
                    eeprom.HpeOcp = 1
                    fmt.Printf(" HPE OCP ENTERPRISE\n");
                } else if pn[0:5] == NAPLES25OCP_HPE_C[0:5] {   
                    eeprom.EepromTbl = eeprom.HpeTblOCPcloud
                    eeprom.EepromExtTbl = eeprom.HpeTblOCPcloudext
                    eeprom.HpeOcp = 1
                    fmt.Printf(" HPE OCP CLOUD\n");
                } else if pn[0:6] == NAPLES25OCP_DELL[0:6] {
                    eeprom.CustType = "DELLOCP"
                    eeprom.EepromTbl = eeprom.DellTblOcp
                    eeprom.DellOcp = 1
                } else {
                    cli.Println("e", "Invalid Part Number '", pn,"' Entered For Programming Naples25 OCP")
                    return -1;
                }
            } 
        }
        if eeprom.HpeAlom == true {
            eeprom.EepromTbl = eeprom.HpeAlomTblAll
        }
        if (cardType == "VOMERO2") {
            eeprom.CustType = "ORACLE"
            eeprom.EepromTbl = eeprom.Vomero2Tbl
        }
        if (cardType == "ORTANO") {
            eeprom.CustType = "ORTANO"
            eeprom.EepromTbl = eeprom.OrtanoTbl
            
        }
        if (cardType == "MTFUJI") {
            eeprom.EepromTbl = eeprom.MtFujiElba
            eeprom.CustType = "PENORTANO"
        }
        if (cardType == "ORTANO2") {
            if update == true {
                if pn == "" {
                    cli.Println("e", "For Programming ORTANO2, you must enter a part number")
                    return -1;
                }
                if pn[0:7] == NAPLES200_ORT_V2[0:7] {
                    eeprom.EepromTbl = eeprom.OrtanoTbl_V2
                    eeprom.CustType = "ORTANO"
                } else if pn[0:7] == NAPLES200_PEN[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_IBM[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoIBMTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_TAOR[0:7] || pn[0:7] == NAPLES200_TAOR2[0:7]{      
                    eeprom.EepromTbl = eeprom.OrtanoTaorminaTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_LIPARI[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoLipariTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_MTFUJI[0:7] {      
                    eeprom.EepromTbl = eeprom.MtFujiElba
                    eeprom.CustType = "PENORTANO"
                } else {
                    cli.Println("e", "Invalid Part Number '", pn,"' Entered For Programming an Ortano Card")
                    return -1;
                }
            }
        }
        if (cardType == "ORTANO2I") {
            if update == true {
                if pn == "" {
                    cli.Println("e", "For Programming ORTANO2I, you must enter a part number")
                    return -1;
                }
                if pn[0:7] == NAPLES200_ORT_V2I[0:7] {
                    eeprom.EepromTbl = eeprom.OrtanoITbl_V2
                    eeprom.CustType = "ORTANO"
                } else if pn[0:7] == NAPLES200_PEN[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_IBM[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoIBMTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_TAOR[0:7] || pn[0:7] == NAPLES200_TAOR2[0:7]{      
                    eeprom.EepromTbl = eeprom.OrtanoTaorminaTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_LIPARI[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoLipariTbl
                    eeprom.CustType = "PENORTANO"
                } else {
                    cli.Println("e", "Invalid Part Number '", pn,"' Entered For Programming an Ortano Card")
                    return -1;
                }
            }
        }
        if (cardType == "ORTANO2A") {   //Ortano2 with analog devices VRM's (ADI)
            if update == true {
                if pn == "" {
                    cli.Println("e", "For Programming ORTANO2, you must enter a part number")
                    return -1;
                }
                if pn[0:7] == NAPLES200_ORT_V2A[0:7] {
                    eeprom.EepromTbl = eeprom.OrtanoATbl_V2
                    eeprom.CustType = "ORTANO"
                } else if pn[0:7] == NAPLES200_PEN[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
                    eeprom.CustType = "PENORTANO"
                } else if pn[0:7] == NAPLES200_IBM[0:7] {      
                    eeprom.EepromTbl = eeprom.OrtanoIBMTbl
                    eeprom.CustType = "PENORTANO"
                } else {
                    cli.Println("e", "Invalid Part Number '", pn,"' Entered For Programming an Ortano Card")
                    return -1;
                }
            }
        }
        if (cardType == "NAPLES100IBM") {
            eeprom.CustType = "IBM"
            eeprom.EepromTbl = eeprom.Naples100IBMTbl
        }
        if (cardType == "NAPLES100HPE") {
            eeprom.CustType = "HPE"
            eeprom.EepromTbl = eeprom.Naples100HPETbl
            if update == true {
                if pn == "" {
                    cli.Println("e", "For Programming Naples100HPE, you must enter a part number")
                    return -1;
                }
                if pn[0:5] == NAPLES100_HPE_E[0:5] {          //ENTERPRISE
                    eeprom.EepromTbl = eeprom.Naples100HPETbl
                    fmt.Printf(" HPE 100 ENTERPRISE\n");
                } else if pn[0:5] == NAPLES100_HPE_C[0:5] {   
                    eeprom.EepromTbl = eeprom.Naples100HPECLOUDTbl
                    eeprom.CustType = "HPE100CLOUD"
                    fmt.Printf(" HPE 100 CLOUD\n");
                } else {
                    cli.Println("e", "Invalid Part Number '", pn,"' Entered For Programming Naples100HPE")
                    return -1;
                }
            } 
        }
        if (cardType == "NAPLES25SWM833") {
            eeprom.CustType = "PENSWM"
            eeprom.EepromTbl = eeprom.PenTblSWM833Mhz
        }
        if (cardType == "LACONA") {
            eeprom.CustType = "LACONA"
            eeprom.EepromTbl = eeprom.HpeTblLACONA
            eeprom.EepromExtTbl = eeprom.HpeTblLACONAext
            eeprom.HpeLacona = 1
        }
        if (cardType == "LACONA32") {
            eeprom.CustType = "LACONA"
            eeprom.EepromTbl = eeprom.HpeTblLACONA32G
            eeprom.EepromExtTbl = eeprom.HpeTblLACONA32Gext
            eeprom.HpeLacona = 1
        }
        if (cardType == "LACONADELL") {
            eeprom.CustType = "LACONADELL"
            eeprom.EepromTbl = eeprom.LaconaDELLTbl
        }
        if (cardType == "LACONA32DELL") {
            eeprom.CustType = "LACONA32DELL"
            eeprom.EepromTbl = eeprom.Lacona32DELLTbl
        }
        if (cardType == "POMONTEDELL") {
            eeprom.CustType = "POMONTEDELL" 
            eeprom.EepromTbl = eeprom.Pomonte100DELLTbl
        }
        if (cardType == "NAPLES25SWMDELL") {
            eeprom.CustType = "DELLSWM"
            eeprom.EepromTbl = eeprom.DellTblSWM
        }
        if (cardType == "NAPLES100DELL") {
            eeprom.CustType = "DELLNAPLES100"
            eeprom.EepromTbl = eeprom.Naples100DELLTbl
        }
        if (cardType == "LIPARI") {
            eeprom.CustType = "LIPARI"
            eeprom.EepromTbl = nil 
            if strings.Contains(dev, "FRU") || strings.Contains(dev, "CPU") {
                eeprom.EepromTlvs = eeprom.LipariCpuTlvs
            } else if strings.Contains(dev, "SWITCH") {
                eeprom.EepromTlvs = eeprom.LipariSwitchTlvs
            } else {
                cli.Println("e", "eepromTlbInit(): Not supported CardType", cardType, "devName", dev)
                return errType.FAIL
            }
        }
    }

    return(0)
}

/*
 * Some card type have multiple part numbers. 
 * Need to scan the programmed FRU for the part number so the correct table is loaded
 * 
 */
func eepromDispTableFix(uut string, devName string, bus uint32, devAddr byte) (err int) {
    var cardType string

    //UUT NONE ASSUMES YOU ARE ON ARM OR YOU NEED TO PROGRAM AN MTP
    //IF UUT IS ENTERED YOU ARE ON THE MTP PROGRAMMING FROM THE SMBUS SIDE
    if (uut == "UUT_NONE") {
        cardType = os.Getenv("CARD_TYPE")
    } else {
        cardType = os.Getenv(uut)
    }

    if (cardType == "MTP") {
        cli.Println("i", "Display MTP EEPROM:")
        return(0)
    } else if (eeprom.HpeSwm == 1 || (cardType == "NAPLES25SWM")) && eeprom.HpeAlom != true {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25SWM_HPE_E[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.HpeTblSWM
            eeprom.EepromExtTbl = eeprom.HpeTblSWMext
            eeprom.HpeSwm = 1
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25SWM_HPE_E_TAA[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.HpeTblSWMTAA
            eeprom.EepromExtTbl = eeprom.HpeTblSWMTAAext
            eeprom.HpeSwm = 1
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25SWM_HPE_C[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.HpeTblSWMCLOUD
            eeprom.EepromExtTbl = eeprom.HpeTblSWMCLOUDext
            eeprom.HpeSwm = 1
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25SWM_PEN[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.PenTblSWM
            eeprom.CustType = "PENSWM"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25SWM_PEN_TAA[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.PenTblSWMTAA
            eeprom.CustType = "PENSWM"
            return(0)
        }
        cli.Println("e", "Unable to determine naples25 SWM fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "NAPLES100HPE") {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES100_HPE_E[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.Naples100HPETbl
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES100_HPE_C[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.Naples100HPECLOUDTbl
            return(0)
        }

        cli.Println("e", "Unable to determine naples100 HPE fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "NAPLES25OCP") {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25OCP_DELL)
        if rc == errType.SUCCESS {
            eeprom.CustType = "DELLOCP"
            eeprom.EepromTbl = eeprom.DellTblOcp
            eeprom.DellOcp = 1
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25OCP_HPE_E[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.HpeTblOCP
            eeprom.EepromExtTbl = eeprom.HpeTblOCPext
            eeprom.HpeOcp = 1
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES25OCP_HPE_C[0:5])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.HpeTblOCPcloud
            eeprom.EepromExtTbl = eeprom.HpeTblOCPcloudext
            eeprom.HpeOcp = 1
            return(0)
        }
        cli.Println("e", "Unable to determine Naples25 OCP fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "ORTANO2") {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_ORT_V2[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoTbl_V2
            eeprom.CustType = "ORTANO"
            return(0)
        } 
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_PEN[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_IBM[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoIBMTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_TAOR[0:7])  //Taormina with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoTaorminaTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_TAOR2[0:7])  //Taormina with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoTaorminaTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_LIPARI[0:7])  //Lipari Switch with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoLipariTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
    } else if (cardType == "MTFUJI") {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_MTFUJI[0:7])  //MtFuji switch with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.MtFujiElba
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        cli.Println("e", "Unable to determine Ortano fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "ORTANO2I") {
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_ORT_V2I[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoITbl_V2
            eeprom.CustType = "ORTANO"
            return(0)
        } 
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_PEN[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoTaorminaTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_IBM[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoIBMTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_TAOR[0:7])  //Taormina with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_TAOR2[0:7])  //Taormina with Elba's
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        cli.Println("e", "Unable to determine Ortano fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "ORTANO2A") {   //Ortano2 with analog devices VRM's (ADI)
        rc := hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_ORT_V2A[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoATbl_V2
            eeprom.CustType = "ORTANO"
            return(0)
        } 
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_PEN[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoPensandoTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        rc = hwdev.EepromMatchSearchFruPN(devName, bus, devAddr, NAPLES200_IBM[0:7])
        if rc == errType.SUCCESS {
            eeprom.EepromTbl = eeprom.OrtanoIBMTbl
            eeprom.CustType = "PENORTANO"
            return(0)
        }
        cli.Println("e", "Unable to determine Ortano ADI fru type.  Please program it with a valid part number")
        return -1;
    } else if (cardType == "UUT_NONE") {
        cli.Println("e", "Empty slot!")
        return(-1)
    } else {
        //All not handled cardType leave to hwdev.EepromDisp to determine
        //Since many cardType don't need to handle here,
        //e.g.: LACONA, POMONTE, NAPLES25, NAPLES100DELL, etc.
        return(0)
    }

    return(0)
}

func main() {
    devNamePtr := flag.String("dev",    "FRU",      "Device name")
    infoPtr    := flag.Bool  ("info",   false,      "Display device info")
    dispPtr    := flag.Bool  ("disp",   false,      "Display eeprom content")
    updatePtr  := flag.Bool  ("update", false,      "Update eeprom")
    verifyPtr  := flag.Bool  ("verify", false,      "Verify eeprom checksums")
    erasePtr   := flag.Bool  ("erase",  false,      "Erase all fields")
    dumpPtr    := flag.Bool  ("dump",    false,     "Dump FRU")
    macPtr     := flag.String("mac",    "",         "MAC address")
    snPtr      := flag.String("sn",     "",         "Serial number")
    sn2Ptr     := flag.String("pcbsn",  "",         "Serial number in product info area")
    pnPtr      := flag.String("pn",     "",         "Part number")
    pn2Ptr     := flag.String("pcbpn",  "",         "Part number in product info area")
    mfgDatePtr := flag.String("date",   "",         "Manufacturing date")
    fieldPtr   := flag.String("field",  "all",      "Display specific eeprom field")
    valuePtr   := flag.String("value",  "",         "value to be updated in eeprom field")
    uutPtr     := flag.String("uut",    "UUT_NONE", "Target UUT")
    majorPtr   := flag.String("maj",    "",         "Hardware major reversion")
    hpePtr     := flag.Bool  ("hpe",    false,      "HPE eeprom operation option")
    hpeSwmPtr  := flag.Bool  ("hpeSwm", false,      "HPE SWM eeprom operation option")
    hpeAlomPtr := flag.Bool  ("hpeAlom",false,      "HPE ALOM eeprom operation option")
    hpeOcpPtr  := flag.Bool  ("hpeOcp", false,      "HPE OCP eeprom operation option")
    DellOcpPtr := flag.Bool  ("DellOcp", false,     "Dell OCP eeprom operation option")
    custTypePtr:= flag.String("custType", "pensando", "Customerized eeeprom operation option")
    numBytesPtr:= flag.Int   ("numBytes",0,         "Number of bytes to be dumped")
    fpoPtr     := flag.Bool  ("fpo",    false,      "First time power on")
    skuPtr     := flag.String("sku",    "",         "SKU")
    skuModePtr := flag.Bool  ("skuMode",false,      "SKU mode")
    dpnPtr     := flag.String("dpn",    "",         "Diagnostic Part number")
    fnamePtr   := flag.String("fn",     "eeprom",   "file name for eeprom dump")
    flag.Parse()

    devName := strings.ToUpper(*devNamePtr)
    mac := strings.ToUpper(*macPtr)
    sn := strings.ToUpper(*snPtr)
    pn := strings.ToUpper(*pnPtr)
    sn2 := strings.ToUpper(*sn2Ptr)
    pn2 := strings.ToUpper(*pn2Ptr)
    date := strings.ToUpper(*mfgDatePtr)
    field := strings.ToUpper(*fieldPtr)
    value := strings.ToUpper(*valuePtr)
    uut := strings.ToUpper(*uutPtr)
    major := strings.ToUpper(*majorPtr)
    numBytes := *numBytesPtr
    fixHpe := 1
    custType := strings.ToUpper(*custTypePtr)
    sku := strings.ToUpper(*skuPtr)
    dpn := strings.ToUpper(*dpnPtr)
    fname := *fnamePtr

    lock, _ := hwinfo.PreUutSetup(uut)
    defer hwinfo.PostUutClean(lock)
    eeprom.CustType = custType
    if *hpeAlomPtr {
        defer hwdev.SelSmbFromAdaptor(uut, false)  //Set mux back to SMB when done
    }

    if *hpePtr == true {
        eeprom.HpeNaples = 1
    }

    if *hpeSwmPtr == true {
        eeprom.HpeSwm = 1
    }

    if *hpeAlomPtr == true {
        eeprom.HpeAlom = true
    }

    if *hpeOcpPtr == true {
        eeprom.HpeOcp = 1
    }

    if *DellOcpPtr == true {
        eeprom.DellOcp = 1
    }

    if len(uut) < 5 {
        cli.Println("e", "Invalid UUT.  UUT Needs to be UUT_NONE or UUT_#.", devName)
        return
    }
    if unicode.IsDigit(rune(uut[4])) == false &&  uut != "UUT_NONE" {
        cli.Println("e", "Invalid UUT.  UUT Needs to be UUT_NONE or UUT_#.  You Entered %s", devName, uut)
        return
    }

    if uut != "UUT_NONE" {
        i2cinfo.SwitchI2cTbl(uut)
    }

    hwdev.SelSmbFromAdaptor(uut, *hpeAlomPtr)

    if pn == MTPOCPADAPTER || custType == "MTPOCPADAPTER" || devName == "FRU_ADAP" {
        devName = "FRU_ADAP"
        pn = MTPOCPADAPTER
        custType = "MTPOCPADAPTER"
    }

    iInfo, err := i2cinfo.GetI2cInfo(devName)
    if err != errType.SUCCESS {
        cli.Println("e", "Failed to obtain I2C info of", devName)
        return
    }

    if *infoPtr == true {
        dispInfo()
        return
    }

    var found bool
    if *skuModePtr == false {
        found, _ = eeprom.CardInListNew(pn, false)
        if !found {
            rc := eepromTlbInit(uut, pn, *updatePtr, devName)
            if rc != 0 {
                cli.Println("e", "eepromTlbInit Failed\n")
                return
            }
        }
    }

    //cli.Println("i", "card IS in eeprom.CardInListNew, PN =", pn)
    info, _ := i2cinfo.GetI2cInfo(devName)
    if ((info.Flag & i2cinfo.FLAG_16BIT_EEPROM) != 0) {
        eeprom.I2cAddr16 = true
    } else {
        eeprom.I2cAddr16 = false
    }

    if *dispPtr == true {
        //Try to sort out which FRU table to load for cards that have multiple part numbers and table formats (like HPE SWM, HPE SWM CLOUD, HPE SWM TAA)
        if (os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE") || (os.Getenv("CARD_TYPE") != "MTP") {
            isTlv := false
            if (uut == "UUT_NONE") {
                isTlv, _ = eeprom.CardInListTlv(devName)
            } else {
                // TO-DO: check if uut eeprom is tlv-format based on uutType
                //        Ortano2: non-tlv
                //        Salina nic: likely to be tlv-based
            }
            if isTlv == true {
                err = hwdev.EepromDisplayTlvs(devName, field, *fpoPtr)
                if err != errType.SUCCESS {
                    cli.Println("e", "Failed to display tlv-based eeprom! CARD_TYPE:", os.Getenv("CARD_TYPE"), "dvName:", devName)
                }
                return
            }

            err = hwdev.EepromDisplayNew(devName, iInfo.Bus, iInfo.DevAddr, field, *fpoPtr)
            if err == errType.SUCCESS {
                return
            }
            if err != errType.PN_NOT_SUPPORT {
                return
            }
        }
        cli.Println("i", "Legacy FRU table")

        if pn != MTPOCPADAPTER && custType != "MTPOCPADAPTER" && devName != "FRU_ADAP" {
            err = eepromDispTableFix(uut, devName, iInfo.Bus, iInfo.DevAddr) 
            if err != errType.SUCCESS {
                cli.Println("e", "Failed to read P/N to load the correct FRU table")
                return
            }
        }
        hwdev.EepromDisp(devName, iInfo.Bus, iInfo.DevAddr, field)
        return
    }

    if *erasePtr == true {
        eeprom.Erase = true
        if numBytes == 0 {
            cli.Println("e", "You need to set the number of bytes to erase..failed to execute erase command", devName)
            return;
        }
    } else {
        eeprom.Erase = false
    }

    if *updatePtr == true || eeprom.Erase == true {
        // FIXME: Skip for ALOM
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" && eeprom.HpeAlom == false && eeprom.HpeSwm == 0 && eeprom.CustType != "DELLSWM" {
            fmt.Println("On MTP")
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd & 0xFD
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x2)
        }

        if eeprom.Erase == true && (devName != "CPLD_FRU") {
            cli.Printf("i", "Erasing %s Addr 0 -  0x%x\n", devName, numBytes)
            hwdev.EepromErase(devName, iInfo.Bus, iInfo.DevAddr, numBytes)
        } 

        if *updatePtr == true {
            misc.SleepInUSec(1000)
            cli.Printf("i", "Programming/Updating Fru\n")
            if (os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE") || (os.Getenv("CARD_TYPE") != "MTP") {
                isTlv, _ := eeprom.CardInListTlv(devName)
                if isTlv == true {
                    if field == "ALL" {
                        hwdev.EepromUpdateTlvs(devName, sn, pn, sn2, pn2, mac, date)
                    } else {
                        hwdev.EepromUpdateTlvField(devName, field, value)
                    }
                    misc.SleepInUSec(500000)
                    return
                }

                var identifier string
                if *skuModePtr == true {
                    identifier = sku
                } else {
                    identifier = pn
                }
                //cli.Printf("i", "skuMode: %t, identifier: %s, dpn: %s\n", *skuModePtr, identifier, dpn)
                found, _ = eeprom.CardInListNew(identifier, *skuModePtr)
                if found == true {
                    hwdev.EepromUpdateNew(devName, iInfo.Bus, iInfo.DevAddr, sn, pn, sku, mac, date, dpn, *skuModePtr)
                    misc.SleepInUSec(500000)
                    return
                } else {
                    if *skuModePtr == true {
                        cli.Println("e", "The SKU '", sku,"' is not supported for this card type")
                        return
                    }
                }
            }
            if mac != "" && eeprom.HpeAlom == false {
                hwdev.EepromUpdateMac(devName, iInfo.Bus, iInfo.DevAddr, mac)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if sn != "" {
                hwdev.EepromUpdateSn(devName, iInfo.Bus, iInfo.DevAddr, sn)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if pn != "" {
                hwdev.EepromUpdatePn(devName, iInfo.Bus, iInfo.DevAddr, pn)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if date != "" {
                hwdev.EepromUpdateDate(devName, iInfo.Bus, iInfo.DevAddr, date)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            if major != "" {
                hwdev.EepromUpdateMajor(devName, iInfo.Bus, iInfo.DevAddr, major)
                misc.SleepInUSec(500000)
                fixHpe = 0
            }
            //Fix Naples25 HPE that are mispgorammed...option for FAE
            if fixHpe > 0 && *hpePtr == true {
                fmt.Printf(" FIXING NAPLES25 HPE\n")
                hwdev.EepromFixNaples25HPE(devName, iInfo.Bus, iInfo.DevAddr)
                //hwdev.EepromErase(devName, iInfo.Bus, iInfo.DevAddr, 256)
            }

            //No Checksum on MTP eeprom
            if !(os.Getenv("CARD_TYPE") == "MTP" && uut == "UUT_NONE") {
                rc := hwdev.EepromVerifyCSUM(devName, iInfo.Bus, iInfo.DevAddr, false)
                if rc != 0 {
                    os.Exit(-1)
                } else {
                    os.Exit(0)
                }
            }
        }

        // FIXME
        if os.Getenv("CARD_TYPE") == "MTP" && uut != "UUT_NONE" && eeprom.HpeAlom == false && eeprom.HpeSwm == 0 && eeprom.CustType != "DELLSWM" {
            rd, _ := cpldSmb.ReadSmb("CPLD", 0x21)
            rd = rd | 0x2
            _ = cpldSmb.WriteSmb("CPLD", 0x21, rd)
        } else {
            CpldWrite(0x1, 0x6)
        }
        return
    }

    if *dumpPtr == true {
        if numBytes <= 0 || numBytes >= 2048 {
            cli.Println("e", "Please set a valid number [1 - 2047] of bytes to dump!", devName)
            return;
        }
        isTlv, _ := eeprom.CardInListTlv(devName)
        if isTlv == true {
            eeprom.DumpEepromTlvs(devName, numBytes, fname, true)
            misc.SleepInUSec(500000)
            return
        } else {
            hwdev.EepromDump(devName, iInfo.Bus, iInfo.DevAddr, numBytes, fname, true)
        }

        return
    }

    if *verifyPtr == true {
        rc := hwdev.EepromVerifyCSUM(devName, iInfo.Bus, iInfo.DevAddr, true)
        if rc != 0 {
            os.Exit(-1)
        } else {
            os.Exit(0)
        }

    }

    flag.Usage()
}
