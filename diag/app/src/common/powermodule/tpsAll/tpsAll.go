package tpsAll

type TpsAll interface {
    ReadPout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadVout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadIout(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadPin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadVin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadIin(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
    ReadTemp(i2cIdx uint32, devAddr uint32, channel uint32) (integer uint32, dec uint32, err int)
}
