package main

import (
    //"fmt"
    "flag"
    "device/mtpCpld"
)

func main() {
 
    jtagRstPtr  		:= flag.Bool("jtag-rst",		false, "Jtag reset")
    jtagEnaPtr  		:= flag.Bool("jtag-ena",		false, "Jtag enable")
    jtagWrPtr   		:= flag.Bool("jtag-wr",			false, "Jtag write")
    jtagRdPtr   		:= flag.Bool("jtag-rd",			false, "Jtag read")
    slotPtr     		:= flag.Uint("slot",			0x0,   "UUT slot number")
    addrPtr     		:= flag.Uint64("addr",			0x0,   "Register address")
    dataPtr     		:= flag.Uint("data",			0x0,   "Write data")
    ssePtr     			:= flag.Uint("sse",				0x2,   "Size and security bit, set bit 1 indicates 2 bytes access")
    mtpCpldRdPtr 			:= flag.Bool("mtpCpld-rd",			false, "CPLD register read")
    mtpCpldWrPtr 			:= flag.Bool("mtpCpld-wr",			false, "CPLD register write")
    instPtr     		:= flag.Uint("inst",			0x0,   "CPLD instance")
//    mtpCpldIdPtr  			:= flag.Bool("mtpCpld-id",			false, "CPLD ID read")
    mtpCpldFlashRdPtr  	:= flag.Bool("mtpCpld-flash-rd", 	false, "CPLD flash read into an output file")
    mtpCpldFlashProgPtr   	:= flag.Bool("mtpCpld-flash-prog",	false, "CPLD flash program")
    outPutPtr     		:= flag.String("output",    	"",    "Output file name")
    inPutPtr     		:= flag.String("input",    		"",    "Input file name")
    mvlRdPtr  			:= flag.Bool("mvl-rd", 			false, "Marvell switch register read")
    mvlWrPtr  			:= flag.Bool("mvl-wr", 			false, "Marvell switch register write")
    phyPtr     			:= flag.Uint("phy",				0x0,   "Marvell switch phy address")
    flag.Parse()

    slot := *slotPtr
    addr := *addrPtr
    data := *dataPtr
    sse  := *ssePtr
    inst := *instPtr
    phy  := *phyPtr
    
    
    if *jtagRstPtr == true {
        mtpCpld.JtagRest(slot)
        return
    }

    if *jtagEnaPtr == true {
        mtpCpld.JtagEnable(slot)
        return
    }
    
    if *jtagWrPtr == true {
        mtpCpld.JtagWrite(slot, addr, data, sse)
        return
    }

    if *jtagRdPtr == true {
        mtpCpld.JtagRead(slot, addr, sse)
        return
    }
    
    if *mtpCpldWrPtr == true {
        mtpCpld.CpldWrite(uint8(addr), uint8(data))
        return
    }
        
    if *mtpCpldRdPtr == true {
        mtpCpld.CpldRead(uint8(addr))
        return
    }

    if *mtpCpldFlashRdPtr == true {
        mtpCpld.CpldFlashRead(inst, *outPutPtr)
        return
    }
 
    if *mtpCpldFlashProgPtr == true {
        mtpCpld.CpldFlashProg(inst, *inPutPtr)
        return
    }
 
    if *mvlWrPtr == true {
        mtpCpld.MvlWrite(inst, phy, uint(addr), data)
        return
    }
        
    if *mvlRdPtr == true {
        mtpCpld.MvlRead(inst, phy, uint(addr))
        return
    }
}

