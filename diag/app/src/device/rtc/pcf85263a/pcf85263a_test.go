package pcf85263a

import (
    "testing"
    "common/errType"
)

func TestReadVout(t *testing.T) {
    year, month, day, hour, minute, second, err := ReadTime("RTC")
    if err != errType.SUCCESS {
        t.Error (
            "Error code wrong",
            "expected", 0,
            "Received", err,
        )
    }

    if year != 89 {
        t.Error (
            "year",
            "expected", 89,
            "Received", year,
        )
    }

    if month != 7 {
        t.Error (
            "month",
            "expected", 7,
            "Received", month,
        )
    }

    if day != 15 {
        t.Error (
            "day",
            "expected", 15,
            "Received", day,
        )
    }

    if hour != 17 {
        t.Error (
            "hour",
            "expected", 17,
            "Received", hour,
        )
    }

    if minute != 45 {
        t.Error (
            "hour",
            "expected", 45,
            "Received", minute,
        )
    }

    if second != 23 {
        t.Error (
            "hour",
            "expected", 23,
            "Received", minute,
        )
    }

}
