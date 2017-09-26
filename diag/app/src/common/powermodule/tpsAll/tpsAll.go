package tpsAll

type TpsAll interface {
    ReadVboot(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadPout(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadVout(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadIout(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadPin(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadVin(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadIin(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadTemp(devName string, channel byte) (integer uint64, dec uint64, err int)
    ReadStatus(devName string, channel byte) (status uint16, err int)
}
