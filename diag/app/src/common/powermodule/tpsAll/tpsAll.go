package tpsAll

type TpsAll interface {
    ReadVboot(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadPout(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadVout(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadIout(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadPin(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadVin(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadIin(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadTemp(devName string, channel byte) (integer uint32, dec uint32, err int)
    ReadStatus(devName string, channel byte) (status uint16, err int)
}
