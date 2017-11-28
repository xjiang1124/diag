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
}
