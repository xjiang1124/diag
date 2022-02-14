package pcf85263a

const (
    SECONDS_100TH uint64 = 0x00
    SECONDS uint64 = 0x01
    MINUTES uint64 = 0x02
    HOURS uint64 = 0x03
    DAYS uint64 = 0x04
    WEEKDAYS uint64 = 0x05
    MONTHS uint64 = 0x06
    YEARS uint64 = 0x07
    SECOND_ALARM1 uint64 = 0x08
    MINUTE_ALARM1 uint64 = 0x09
    HOUR_ALARM1 uint64 = 0x0A
    DAY_ALARM1 uint64 = 0x0B
    MONTH_ALARM1 uint64 = 0x0C
    MINUTE_ALARM2 uint64 = 0x0D
    HOUR_ALARM2 uint64 = 0x0E
    WEEKDAY_ALARM uint64 = 0x0F
    ALARM_ENABLES uint64 = 0x10
    TSR1_SECONDS uint64 = 0x11
    TSR1_MINUTES uint64 = 0x12
    TSR1_HOURS uint64 = 0x13
    TSR1_DAYS uint64 = 0x14
    TSR1_MONTHS uint64 = 0x15
    TSR1_YEARS uint64 = 0x16
    TSR2_SECONDS uint64 = 0x17
    TSR2_MINUTES uint64 = 0x18
    TSR2_HOURS uint64 = 0x19
    TSR2_DAYS uint64 = 0x1A
    TSR2_MONTHS uint64 = 0x1B
    TSR2_YEARS uint64 = 0x1C
    TSR3_SECONDS uint64 = 0x1D
    TSR3_MINUTES uint64 = 0x1E
    TSR3_HOURS uint64 = 0x1F
    TSR3_DAYS uint64 = 0x20
    TSR3_MONTHS uint64 = 0x21
    TSR3_YEARS uint64 = 0x22
    TSR_MODE uint64 = 0x23
    OFFSET uint64 = 0x24
    OSCILLATOR uint64 = 0x25
    BATT_SW uint64 = 0x26
    PIN_IO uint64 = 0x27
    FUNCTION uint64 = 0x28
    INTA_ENA uint64 = 0x29
    INTB_ENA uint64 = 0x2A
    FLAGS uint64 = 0x2B
    RAM_BYTE uint64 = 0x2C
    WATCHDOG uint64 = 0x2D
    STOP_ENA uint64 = 0x2E
    RESET uint64 = 0x2F
)

type reg_struct struct {
    regname    string
    regaddr    uint64 
}

var rtc_reg = []reg_struct {
    reg_struct {
        regname: "SECONDS_100TH",
        regaddr: SECONDS_100TH,
    },
    reg_struct {
        regname: "SECONDS",
        regaddr: SECONDS,
    },
    reg_struct {
        regname: "MINUTES",
        regaddr: MINUTES,
    },
    reg_struct {
        regname: "HOURS",
        regaddr: HOURS,
    },
    reg_struct {
        regname: "DAYS",
        regaddr: DAYS,
    },
    reg_struct {
        regname: "WEEKDAYS",
        regaddr: WEEKDAYS,
    },
    reg_struct {
        regname: "MONTHS",
        regaddr: MONTHS,
    },
    reg_struct {
        regname: "YEARS",
        regaddr: YEARS,
    },
    reg_struct {
        regname: "SECOND_ALARM1",
        regaddr: SECOND_ALARM1,
    },
    reg_struct {
        regname: "MINUTE_ALARM1",
        regaddr: MINUTE_ALARM1,
    },
    reg_struct {
        regname: "HOUR_ALARM1",
        regaddr: HOUR_ALARM1,
    },
    reg_struct {
        regname: "DAY_ALARM1",
        regaddr: DAY_ALARM1,
    },
    reg_struct {
        regname: "MONTH_ALARM1",
        regaddr: MONTH_ALARM1,
    },
    reg_struct {
        regname: "MINUTE_ALARM2",
        regaddr: MINUTE_ALARM2,
    },
    reg_struct {
        regname: "HOUR_ALARM2",
        regaddr: HOUR_ALARM2,
    },
    reg_struct {
        regname: "WEEKDAY_ALARM",
        regaddr: WEEKDAY_ALARM,
    },
    reg_struct {
        regname: "ALARM_ENABLES",
        regaddr: ALARM_ENABLES,
    },
    reg_struct {
        regname: "TSR1_SECONDS",
        regaddr: TSR1_SECONDS,
    },
    reg_struct {
        regname: "TSR1_MINUTES",
        regaddr: TSR1_MINUTES,
    },
    reg_struct {
        regname: "TSR1_HOURS",
        regaddr: TSR1_HOURS,
    },
    reg_struct {
        regname: "TSR1_DAYS",
        regaddr: TSR1_DAYS,
    },
    reg_struct {
        regname: "TSR1_MONTHS",
        regaddr: TSR1_MONTHS,
    },
    reg_struct {
        regname: "TSR1_YEARS",
        regaddr: TSR1_YEARS,
    },
    reg_struct {
        regname: "TSR2_SECONDS",
        regaddr: TSR2_SECONDS,
    },
    reg_struct {
        regname: "TSR2_MINUTES",
        regaddr: TSR2_MINUTES,
    },
    reg_struct {
        regname: "TSR2_HOURS",
        regaddr: TSR2_HOURS,
    },
    reg_struct {
        regname: "TSR2_DAYS",
        regaddr: TSR2_DAYS,
    },
    reg_struct {
        regname: "TSR2_MONTHS",
        regaddr: TSR2_MONTHS,
    },
    reg_struct {
        regname: "TSR2_YEARS",
        regaddr: TSR2_YEARS,
    },
    reg_struct {
        regname: "TSR3_SECONDS",
        regaddr: TSR3_SECONDS,
    },
    reg_struct {
        regname: "TSR3_MINUTES",
        regaddr: TSR3_MINUTES,
    },
    reg_struct {
        regname: "TSR3_HOURS",
        regaddr: TSR3_HOURS,
    },
    reg_struct {
        regname: "TSR3_DAYS",
        regaddr: TSR3_DAYS,
    },
    reg_struct {
        regname: "TSR3_MONTHS",
        regaddr: TSR3_MONTHS,
    },
    reg_struct {
        regname: "TSR3_YEARS",
        regaddr: TSR3_YEARS,
    },
    reg_struct {
        regname: "TSR_MODE",
        regaddr: TSR_MODE,
    },
    reg_struct {
        regname: "OFFSET",
        regaddr: OFFSET,
    },
    reg_struct {
        regname: "OSCILLATOR",
        regaddr: OSCILLATOR,
    },
    reg_struct {
        regname: "BATT_SW",
        regaddr: BATT_SW,
    },
    reg_struct {
        regname: "PIN_IO",
        regaddr: PIN_IO,
    },
    reg_struct {
        regname: "FUNCTION",
        regaddr: FUNCTION,
    },
    reg_struct {
        regname: "INTA_ENA",
        regaddr: INTA_ENA,
    },
    reg_struct {
        regname: "INTB_ENA",
        regaddr: INTB_ENA,
    },
    reg_struct {
        regname: "FLAGS",
        regaddr: FLAGS,
    },
    reg_struct {
        regname: "RAM_BYTE",
        regaddr: RAM_BYTE,
    },
    reg_struct {
        regname: "WATCHDOG",
        regaddr: WATCHDOG,
    },
    reg_struct {
        regname: "STOP_ENA",
        regaddr: STOP_ENA,
    },
    reg_struct {
        regname: "RESET",
        regaddr: RESET,
    },
}

