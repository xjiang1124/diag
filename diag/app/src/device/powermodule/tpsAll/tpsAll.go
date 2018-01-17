package tpsAll

type TpsAll interface {
//    ReadVboot(devName string) (integer uint64, dec uint64, err int)
//    ReadPout(devName string) (integer uint64, dec uint64, err int)
//    ReadVout(devName string) (integer uint64, dec uint64, err int)
//    ReadIout(devName string) (integer uint64, dec uint64, err int)
//    ReadPin(devName string) (integer uint64, dec uint64, err int)
//    ReadVin(devName string) (integer uint64, dec uint64, err int)
//    ReadIin(devName string) (integer uint64, dec uint64, err int)
//    ReadTemp(devName string) (integer uint64, dec uint64, err int)
    ReadStatus(devName string) (status uint16, err int)
    DispStatus(devName string) (err int)
    SetVMargin(devName string, pct int) (err int)
    ReadByte(devName string, regAddr uint64) (data byte, err int)
    ReadWord(devName string, regAddr uint64) (data uint16, err int)
    WriteByte(devName string, regAddr uint64, data byte) (err int)
    WriteWord(devName string, regAddr uint64, data uint16) (err int)
    SendByte(devName string, data byte) (err int)
    ReadBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int)
    WriteBlock(devName string, regAddr uint64, dataBuf []byte) (byteCnt int, err int)
    ProgramVerifyNvm(devName string, fileName string, mode string, verbose bool) (err int)
    Info(devName string) (err int)
}
