package dmutex

import (
    "fmt"
    "testing"
)

func TestLockUnlock(t *testing.T) {
   Lock("QSFP_0_A0")
   fmt.Println("Locked")
   Unlock("QSFP_0_A0")
   fmt.Println("Unlocked")
//    TestLock()
}

