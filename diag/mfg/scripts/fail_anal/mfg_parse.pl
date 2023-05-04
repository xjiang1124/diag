#!/usr/bin/perl
use strict;
use warnings;
use Time::Local;
use Cwd;
use YAML::XS;

my $rev = "1.17.04282023";
my $fa_opt = shift;
my $card_type = shift;
my $test_name_opt = shift;
my $mfg_err_code_opt = shift;
my $yaml_file = "./temp.yaml";

if (defined $test_name_opt) {
    print "test name: $test_name_opt\n";
} else {
    $test_name_opt = "";
}
if (defined $mfg_err_code_opt) {
    print "mfg err code: $mfg_err_code_opt\n";
} else {
    $mfg_err_code_opt = "";
}
my $file_logs_all = "./testresult.txt";
my $failure_logs = "./logs_fail.txt";
my $pass_logs = "./logs_pass.txt";
my $log_path = cwd();

my $curr_sn = "";
my $curr_unixts = 0;
my $lastline = "";
my $debug_msgs = 0;

#system("rm $failure_logs $pass_logs $result_file");

my $num_failures = 0;

sub convert_ts {
    my ($ts) = @_;
    #format: 2021-11-27_16-44-31
    my ($date, $time) = split('_', $ts);
    if ($debug_msgs) { print "date: $date, time: $time\n"};
    my ($year, $mon, $mday) = split('-', $date);
    if ($debug_msgs) { print "year: $year, mon: $mon, mday: $mday\n"};
    my ($hour, $min, $sec) = split('-', $time);
    if ($debug_msgs) { print "hour: $hour, min: $min, sec: $sec\n"};
    my $unixts = timelocal($sec, $min, $hour, $mday, $mon-1, $year);
    if ($debug_msgs) { print "unixts: $unixts\n"};
    return $unixts;
}

sub count_num_of_failures {
    my ($fa_opt) = @_;
    my %failures_one_sn = ();
    $num_failures = 0;
    open(TR, '<', $file_logs_all) or die $!;
    open(TR2, '>', $failure_logs) or die $!;
    while(my $line = <TR>)
    {
        if($line =~ m/\.\/([\w-]+)\/(\w+)\/([0-9A-Z-]+)_(MTP|MTPS)\-([0-9]+)_(.*)\/(mtp_test|test_fst).log(.*)(\]:\s)(NIC-\d+)(\s\w+\s)(\w+)(\s)NIC_DIAG_REGRESSION_TEST_FAIL/)
        {
            my $toppath=$1;
            my $sn=$2;
            my $stage=$3;
            my $mtp=$5;
            my $ts=$6;
            my $slot=$10;
            my $sn2=$12;

            if ($debug_msgs) {
                print "toppath:  $toppath\n";
                print "folder sn:  $sn\n";
                print "card  sn2:  $sn2\n";
                print "stage:      $stage\n";
                print "ts:         $ts\n";
                print "slot:       $slot\n";
            }

            if ($sn eq $sn2)
            {
                if ($curr_sn eq "")
                {
                    $curr_sn = $sn2;
                    if ($debug_msgs) { print "first new SN: $curr_sn\n"};
                }

                my $unixts = convert_ts($ts);

                if ($fa_opt !~ m/ALL/) {
                    if ($curr_sn ne $sn2)
                    {
                        print TR2 $lastline;
                        $num_failures++;
                        $curr_sn = $sn2;
                        $curr_unixts = $unixts;
                        if ($debug_msgs) { print "A new SN: $curr_sn, curr_unixts: $curr_unixts\n"};
                        $lastline=$line;
                        next;
                    }

                    if (($fa_opt eq "FIRST" && $unixts < $curr_unixts) ||
                        ($fa_opt eq "LAST" && $unixts > $curr_unixts))
                    {
                        $curr_unixts = $unixts;
                        if ($debug_msgs) { print "new curr_unixts: $curr_unixts\n"};
                        $lastline=$line;
                    }
                } else {
                    if ($curr_sn ne $sn2)
                    {
                        #sort on unixts
                        foreach my $ts (sort keys %failures_one_sn) {
                            if ($debug_msgs) { printf "%-8s %s\n", $ts, $failures_one_sn{$ts}};
                            print TR2 $failures_one_sn{$ts};
                        }
                        %failures_one_sn = ();
                        $curr_sn = $sn2;
                        if ($debug_msgs) { print "A new SN: $curr_sn\n"};
                    }
                    $failures_one_sn{$unixts} = $line;
                    $num_failures++;
                }
            }
        }
    }
    if ($fa_opt !~ m/ALL/) {
        print TR2 $lastline;
        $num_failures++;
    } else {
        foreach my $ts (sort keys %failures_one_sn) {
            print TR2 $failures_one_sn{$ts};
        }
    }
    close(TR);
    close(TR2);
}

sub count_num_of_runs {
    my ($fa_opt) = @_;
    my %failures_one_sn = ();
    $num_failures = 0;
    open(TR, '<', $file_logs_all) or die $!;
    open(TR2, '>', $failure_logs) or die $!;
    while(my $line = <TR>)
    {
        if($line =~ m/\.\/([\w-]+)\/(\w+)\/([0-9A-Z-]+)_(MTP|MTPS)\-([0-9]+)_(.*)\/(mtp_test|test_fst).log(.*)(\]:\s)(NIC-\d+)\s\w+\s(\w+)\sNIC_DIAG_REGRESSION_TEST_(PASS|FAIL)/)
        {
            my $toppath=$1;
            my $sn=$2;
            my $stage=$3;
            my $mtp=$5;
            my $ts=$6;
            my $slot=$10;
            my $sn2=$11;

            if ($debug_msgs) {
                print "toppath:  $toppath\n";
                print "folder sn:  $sn\n";
                print "card  sn2:  $sn2\n";
                print "stage:      $stage\n";
                print "ts:         $ts\n";
                print "slot:       $slot\n";
            }

            if ($sn eq $sn2)
            {
                if ($curr_sn eq "")
                {
                    $curr_sn = $sn2;
                    if ($debug_msgs) { print "first new SN: $curr_sn\n"};
                }

                my $unixts = convert_ts($ts);

                if ($fa_opt !~ m/ALL/) {
                    if ($curr_sn ne $sn2)
                    {
                        print TR2 $lastline;
                        $num_failures++;
                        $curr_sn = $sn2;
                        $curr_unixts = $unixts;
                        if ($debug_msgs) { print "A new SN: $curr_sn, curr_unixts: $curr_unixts\n"};
                        $lastline=$line;
                        next;
                    }

                    if (($fa_opt eq "FIRST_RUN" && $unixts < $curr_unixts) ||
                        ($fa_opt eq "LAST_RUN" && $unixts > $curr_unixts))
                    {
                        $curr_unixts = $unixts;
                        if ($debug_msgs) { print "new curr_unixts: $curr_unixts\n"};
                        $lastline=$line;
                    }
                } else {
                    if ($curr_sn ne $sn2)
                    {
                        #sort on unixts
                        foreach my $ts (sort keys %failures_one_sn) {
                            if ($debug_msgs) { printf "%-8s %s\n", $ts, $failures_one_sn{$ts}};
                            print TR2 $failures_one_sn{$ts};
                        }
                        %failures_one_sn = ();
                        $curr_sn = $sn2;
                        if ($debug_msgs) { print "A new SN: $curr_sn\n"};
                    }
                    $failures_one_sn{$unixts} = $line;
                    $num_failures++;
                }
            }
        }
    }
    if ($fa_opt !~ m/ALL/) {
        print TR2 $lastline;
        $num_failures++;
    } else {
        foreach my $ts (sort keys %failures_one_sn) {
            print TR2 $failures_one_sn{$ts};
        }
    }
    close(TR);
    close(TR2);
}

if($fa_opt eq "LAST") {
    $curr_unixts = 0;
    count_num_of_failures($fa_opt);
} elsif($fa_opt eq "FIRST") {
    $curr_unixts = time();
    count_num_of_failures($fa_opt);
} elsif($fa_opt eq "ALL") {
    count_num_of_failures($fa_opt);
} elsif($fa_opt eq "LAST_RUN") {
    $curr_unixts = 0;
    count_num_of_runs($fa_opt);
} elsif($fa_opt eq "FIRST_RUN") {
    $curr_unixts = time();
    count_num_of_runs($fa_opt);
} elsif($fa_opt eq "ALL_RUN") {
    count_num_of_runs($fa_opt);
} else {
    print "unexpected fa_opt $fa_opt\n";
    exit(1);
}

my $curr_row = 0;
open(TR2, '<', $failure_logs) or die $!;

my %diag_fa_code;
#my $fa_table;
my @fa_row;
my $top_diag_fa_code = "";
my $all_test_msg = "";
my $all_l1_fails = "";
while(my $line = <TR2>)
{
    if($line =~ m/\.\/([\w-]+)\/(\w+)\/([0-9A-Z-]+)_(MTP|MTPS)\-([0-9]+)_(.*)\/(mtp_test|test_fst).log(.*)(\]:\s)NIC-(\d+)\s\w+\s(\w+)\sNIC_DIAG_REGRESSION_TEST_(PASS|FAIL)/)
    {
        my $toppath=$1;
        my $sn=$2;
        my $stage=$3;
        my $mtp=$4."-".$5;
        my $ts=$6;
        my $slot=$10;
        my $sn2=$11;
        my $result=$12;

        if ($debug_msgs) { print "\nThe SN we are looking at: $sn2, line: $line\n" };
        my $fulllogpath=$log_path."/".$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts;
        my $summaryfile=$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts."/"."mtp_test.log";
        my $mtpdiagfile=$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts."/"."mtp_diag.log";
        my $slotlogfile=$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts."/"."mtp_NIC-".$slot."_diag.log";
        if ($toppath eq "FST") {
            $summaryfile=$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts."/"."test_fst.log";
            $slotlogfile=$toppath."/".$sn2."/".$stage."_".$mtp."_".$ts."/"."diag_NIC-".$slot."_fst.log";
        }

        if ($debug_msgs) { print "summaryfile: $summaryfile\n" };
        if ($debug_msgs) { print "slotlogfile: $slotlogfile\n" };
        print "########################## $curr_row ###############################\n";
        printf "%-30s %-20s %-20s\n", "Failed sn: ".$sn2, "mtp: ".$mtp, "slot: ".$slot;
        @fa_row = ();
        $fa_row[$curr_row]{"SN"} = $sn2;
        $fa_row[$curr_row]{"Stage"} = $toppath;
        $fa_row[$curr_row]{"Date"} = $ts;
        $fa_row[$curr_row]{"MTP"} = $mtp;
        $fa_row[$curr_row]{"Slot"} = $slot;
        $fa_row[$curr_row]{"Rev"} = $rev;

        %diag_fa_code = ();
        $all_test_msg = "";
        if ($result eq "FAIL") {
            my $l1_failed = find_failure_code($fulllogpath, $sn2, $toppath, $stage, $ts, $slot);
            if ($stage ne "FST") {
                parse_fpga_and_ecc($summaryfile, $slotlogfile, $sn2, $ts, $l1_failed);
                parse_mtp_diag_file($mtpdiagfile);
            }

            my $diag_fa_code_str = "";
            foreach my $diag_fa_code (keys %diag_fa_code) {
                $diag_fa_code_str .= $diag_fa_code."\n";
            }
            if ($diag_fa_code_str ne "") {
                chomp($diag_fa_code_str);
                $fa_row[$curr_row]{"Detailed Diag FA Code"} = $diag_fa_code_str;
            }

            pick_top_diag_fa();
            $fa_row[$curr_row]{"Diag FA Code"} = $top_diag_fa_code;
        } else { 
            $fa_row[$curr_row]{"Diag FA Code"} = "PASS";
            $fa_row[$curr_row]{"Detailed Diag FA Code"} = "";
        }
        $fa_row[$curr_row]{"Err Msg"} = $all_test_msg;
        open(TR0, '>>', $yaml_file) or die $!;
        print TR0 Dump($fa_row[$curr_row]);
        close(TR0);        
        $curr_row++;
    }
}
close(TR2);

sub pick_top_diag_fa {
    if (%diag_fa_code == 0) {
        $top_diag_fa_code = "UNKNOWN";
        return;
    }

    if (exists $diag_fa_code{"2WAY_COMMUNICATION_FAILURE"}) {
        $top_diag_fa_code = "2WAY_COMMUNICATION_FAILURE";
        delete $diag_fa_code{"2WAY_COMMUNICATION_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"NIC_POWER_FAILURE_12V_LOST"}) {
        $top_diag_fa_code = "NIC_POWER_FAILURE_12V_LOST";
        delete $diag_fa_code{"NIC_POWER_FAILURE_12V_LOST"};
        return;
    }

    if (exists $diag_fa_code{"NIC_POWER_FAILURE_12V_NOT_UP"}) {
        $top_diag_fa_code = "NIC_POWER_FAILURE_12V_NOT_UP";
        delete $diag_fa_code{"NIC_POWER_FAILURE_12V_NOT_UP"};
        return;
    }

    if (exists $diag_fa_code{"NIC_POWER_FAILURE"}) {
        $top_diag_fa_code = "NIC_POWER_FAILURE";
        delete $diag_fa_code{"NIC_POWER_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"DDR_ECC_FAILURE"}) {
        $top_diag_fa_code = "DDR_ECC_FAILURE";
        delete $diag_fa_code{"DDR_ECC_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"DDR_ECC_FAILURE_AFTER_C92_UPGRADED"}) {
        $top_diag_fa_code = "DDR_ECC_FAILURE_AFTER_C92_UPGRADED";
        delete $diag_fa_code{"DDR_ECC_FAILURE_AFTER_C92_UPGRADED"};
        return;
    }

    if (exists $diag_fa_code{"DDR_INIT_FAILURE"}) {
        $top_diag_fa_code = "DDR_INIT_FAILURE";
        delete $diag_fa_code{"DDR_INIT_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_LOG_INCOMPLETE"} && exists $diag_fa_code{"RETEST_NEEDED"}) {
        $top_diag_fa_code = "RETEST_NEEDED";
        delete $diag_fa_code{"RETEST_NEEDED"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_OTHER"} && exists $diag_fa_code{"RETEST_NEEDED"}) {
        $top_diag_fa_code = "RETEST_NEEDED";
        delete $diag_fa_code{"RETEST_NEEDED"};
        return;
    }

    if (exists $diag_fa_code{"TEST_IGNORED"}) {
        $top_diag_fa_code = "TEST_IGNORED";
        delete $diag_fa_code{"TEST_IGNORED"};
        return;
    }

    if (exists $diag_fa_code{"L1_DDR_BIST"}) {
        $top_diag_fa_code = "L1_DDR_BIST";
        delete $diag_fa_code{"L1_DDR_BIST"};
        return;
    }

    if (exists $diag_fa_code{"ARM_DDR_BIST"}) {
        $top_diag_fa_code = "ARM_DDR_BIST";
        delete $diag_fa_code{"ARM_DDR_BIST"};
        return;
    }

    if (exists $diag_fa_code{"EDMA_FAILURE"}) {
        $top_diag_fa_code = "EDMA_FAILURE";
        delete $diag_fa_code{"EDMA_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"HV_EDMA_FAILURE"}) {
        if (exists $diag_fa_code{"LV_EDMA_FAILURE"}) {
            $top_diag_fa_code = "HV_LV_EDMA_FAILURE";
            delete $diag_fa_code{"HV_EDMA_FAILURE"};
            delete $diag_fa_code{"LV_EDMA_FAILURE"};
            return;
        } else {
            $top_diag_fa_code = "HV_EDMA_FAILURE";
            delete $diag_fa_code{"HV_EDMA_FAILURE"};
            return;
        }
    }

    if (exists $diag_fa_code{"LV_EDMA_FAILURE"}) {
        $top_diag_fa_code = "LV_EDMA_FAILURE";
        delete $diag_fa_code{"LV_EDMA_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"NCSI_LOOPBACK_MISSING"}) {
        $top_diag_fa_code = "NCSI_LOOPBACK_MISSING";
        delete $diag_fa_code{"NCSI_LOOPBACK_MISSING"};
        return;
    }

    if (exists $diag_fa_code{"SW_BOOT"}) {
        $top_diag_fa_code = "SW_BOOT";
        delete $diag_fa_code{"SW_BOOT"};
        return;
    }
    if (exists $diag_fa_code{"EFUSE_PROG"}) {
        $top_diag_fa_code = "EFUSE_PROG";
        delete $diag_fa_code{"EFUSE_PROG"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_L_VOLT_LOW"}) {
        $top_diag_fa_code = "VMARG_L_VOLT_LOW";
        delete $diag_fa_code{"VMARG_L_VOLT_LOW"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_L_BOOT_UBOOT"}) {
        $top_diag_fa_code = "VMARG_L_BOOT_UBOOT";
        delete $diag_fa_code{"VMARG_L_BOOT_UBOOT"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_H_BOOT_UBOOT"}) {
        $top_diag_fa_code = "VMARG_H_BOOT_UBOOT";
        delete $diag_fa_code{"VMARG_H_BOOT_UBOOT"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_L_CARD_REBOOTED"}) {
        $top_diag_fa_code = "VMARG_L_CARD_REBOOTED";
        delete $diag_fa_code{"VMARG_L_CARD_REBOOTED"};
        return;
    }
    if (exists $diag_fa_code{"VMARG_H_CARD_REBOOTED"}) {
        $top_diag_fa_code = "VMARG_H_CARD_REBOOTED";
        delete $diag_fa_code{"VMARG_H_CARD_REBOOTED"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_L_SSH_HUNG"}) {
        $top_diag_fa_code = "VMARG_L_SSH_HUNG";
        delete $diag_fa_code{"VMARG_L_SSH_HUNG"};
        return;
    }

    if (exists $diag_fa_code{"VMARG_H_SSH_HUNG"}) {
        $top_diag_fa_code = "VMARG_H_SSH_HUNG";
        delete $diag_fa_code{"VMARG_H_SSH_HUNG"};
        return;
    }

    if (exists $diag_fa_code{"CARD_REBOOTED"}) {
        $top_diag_fa_code = "CARD_REBOOTED";
        delete $diag_fa_code{"CARD_REBOOTED"};
        return;
    }

    if (exists $diag_fa_code{"NIC_UNRESP_SSH_HUNG"}) {
        $top_diag_fa_code = "NIC_UNRESP_SSH_HUNG";
        delete $diag_fa_code{"NIC_UNRESP_SSH_HUNG"};
        return;
    }

    if (exists $diag_fa_code{"CONSOLE_UNRESP"}) {
        $top_diag_fa_code = "CONSOLE_UNRESP";
        delete $diag_fa_code{"CONSOLE_UNRESP"};
        return;
    }

    if (exists $diag_fa_code{"PCIE_PLL_FAILURE(0x2e)"}) {
        $top_diag_fa_code = "PCIE_PLL_FAILURE(0x2e)";
        delete $diag_fa_code{"PCIE_PLL_FAILURE(0x2e)"};
        return;
    }

    if (exists $diag_fa_code{"CORE_PLL_FAILURE(0x2b)"}) {
        $top_diag_fa_code = "CORE_PLL_FAILURE(0x2b)";
        delete $diag_fa_code{"CORE_PLL_FAILURE(0x2b)"};
        return;
    }

    if (exists $diag_fa_code{"CPU_PLL_FAILURE(0x2c)"}) {
        $top_diag_fa_code = "CPU_PLL_FAILURE(0x2c)";
        delete $diag_fa_code{"CPU_PLL_FAILURE(0x2c)"};
        return;
    }

    if (exists $diag_fa_code{"FLASH_PLL_FAILURE(0x2d)"}) {
        $top_diag_fa_code = "FLASH_PLL_FAILURE(0x2d)";
        delete $diag_fa_code{"FLASH_PLL_FAILURE(0x2d)"};
        return;
    }

    for (keys %diag_fa_code) {
        if ($_ =~ "L1_TST_") {
            $top_diag_fa_code = "$_";
            delete $diag_fa_code{"$_"};
            return;
        }
    }

    if (exists $diag_fa_code{"PCIE_PRBS_FAILURE"}) {
        $top_diag_fa_code = "PCIE_PRBS_FAILURE";
        delete $diag_fa_code{"PCIE_PRBS_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"ETH_PRBS_FAILURE"}) {
        $top_diag_fa_code = "ETH_PRBS_FAILURE";
        delete $diag_fa_code{"ETH_PRBS_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_PCIe_LINKUP"}) {
        $top_diag_fa_code = "SNAKE_PCIe_LINKUP";
        delete $diag_fa_code{"SNAKE_PCIe_LINKUP"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_PCIe_TXDETECTRX"}) {
        $top_diag_fa_code = "SNAKE_PCIe_TXDETECTRX";
        delete $diag_fa_code{"SNAKE_PCIe_TXDETECTRX"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_PBM_ECC_FAILURE"}) {
        $top_diag_fa_code = "SNAKE_PBM_ECC_FAILURE";
        delete $diag_fa_code{"SNAKE_PBM_ECC_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_RAM_FAILURE"}) {
        $top_diag_fa_code = "SNAKE_RAM_FAILURE";
        delete $diag_fa_code{"SNAKE_RAM_FAILURE"};
        return;
    }

    if (exists $diag_fa_code{"RETEST_NEEDED"}) {
        $top_diag_fa_code = "RETEST_NEEDED";
        delete $diag_fa_code{"RETEST_NEEDED"};
        return;
    }

    if (exists $diag_fa_code{"TEMP_TRIP_FAILURE(0x50)"}) {
        $top_diag_fa_code = "TEMP_TRIP_FAILURE(0x50)";
        delete $diag_fa_code{"TEMP_TRIP_FAILURE(0x50)"};
        return;
    }

    if (exists $diag_fa_code{"ASIC_PIN_STATUS_2_FAILURE(0x28)"}) {
        $top_diag_fa_code = "ASIC_PIN_STATUS_2_FAILURE(0x28)";
        delete $diag_fa_code{"ASIC_PIN_STATUS_2_FAILURE(0x28)"};
        return;
    }

    if (exists $diag_fa_code{"CANNOT_READ_CPLD_STATUS_DUE_TO_SMBUS_ERR"}) {
        $top_diag_fa_code = "CANNOT_READ_CPLD_STATUS_DUE_TO_SMBUS_ERR";
        delete $diag_fa_code{"CANNOT_READ_CPLD_STATUS_DUE_TO_SMBUS_ERR"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_MX_LINKUP"}) {
        $top_diag_fa_code = "SNAKE_MX_LINKUP";
        delete $diag_fa_code{"SNAKE_MX_LINKUP"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_THROUGHPUT_LOW"}) {
        $top_diag_fa_code = "SNAKE_THROUGHPUT_LOW";
        delete $diag_fa_code{"SNAKE_THROUGHPUT_LOW"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_CNT_MISCOMPARE"}) {
        $top_diag_fa_code = "SNAKE_CNT_MISCOMPARE";
        delete $diag_fa_code{"SNAKE_CNT_MISCOMPARE"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_CRC_ERROR"}) {
        $top_diag_fa_code = "SNAKE_CRC_ERROR";
        delete $diag_fa_code{"SNAKE_CRC_ERROR"};
        return;
    }

    if (exists $diag_fa_code{"L1_CORE_DUMPED"}) {
        $top_diag_fa_code = "L1_CORE_DUMPED";
        delete $diag_fa_code{"L1_CORE_DUMPED"};
        return;
    }

    if (exists $diag_fa_code{"EMMC_ERR"}) {
        $top_diag_fa_code = "EMMC_ERR";
        delete $diag_fa_code{"EMMC_ERR"};
        return;
    }
    if (exists $diag_fa_code{"BOOT_GOLDFW"}) {
        $top_diag_fa_code = "BOOT_GOLDFW";
        delete $diag_fa_code{"BOOT_GOLDFW"};
        return;
    }
    if (exists $diag_fa_code{"BOOT_UBOOT"}) {
        $top_diag_fa_code = "BOOT_UBOOT";
        delete $diag_fa_code{"BOOT_UBOOT"};
        return;
    }

    if (exists $diag_fa_code{"INCORRECT_PN"}) {
        $top_diag_fa_code = "INCORRECT_PN";
        delete $diag_fa_code{"INCORRECT_PN"};
        return;
    }
    if (exists $diag_fa_code{"INCORRECT_SN"}) {
        $top_diag_fa_code = "INCORRECT_SN";
        delete $diag_fa_code{"INCORRECT_SN"};
        return;
    }
    if (exists $diag_fa_code{"INCORRECT_PN_REV"}) {
        $top_diag_fa_code = "INCORRECT_PN_REV";
        delete $diag_fa_code{"INCORRECT_PN_REV"};
        return;
    }
    if (exists $diag_fa_code{"PN_SW_MATCH_ERR"}) {
        $top_diag_fa_code = "PN_SW_MATCH_ERR";
        delete $diag_fa_code{"PN_SW_MATCH_ERR"};
        return;
    }
    if (exists $diag_fa_code{"RETREIVE_PN_FAIL"}) {
        $top_diag_fa_code = "RETREIVE_PN_FAIL";
        delete $diag_fa_code{"RETREIVE_PN_FAIL"};
        return;
    }
    if (exists $diag_fa_code{"CARD_RESET"}) {
        $top_diag_fa_code = "CARD_RESET";
        delete $diag_fa_code{"CARD_RESET"};
        return;
    }
    if (exists $diag_fa_code{"Bad_J2C_L1"}) {
        $top_diag_fa_code = "Bad_J2C_L1";
        delete $diag_fa_code{"Bad_J2C_L1"};
        return;
    }
    if (exists $diag_fa_code{"Bad_J2C_ECC"}) {
        $top_diag_fa_code = "Bad_J2C_ECC";
        delete $diag_fa_code{"Bad_J2C_ECC"};
        return;
    }
    if (exists $diag_fa_code{"Bad_J2C"}) {
        $top_diag_fa_code = "Bad_J2C";
        delete $diag_fa_code{"Bad_J2C"};
        return;
    }
    if (exists $diag_fa_code{"SNAKE_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "SNAKE_LOG_INCOMPLETE";
        delete $diag_fa_code{"SNAKE_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"SNAKE_LOG_EMPTY"}) {
        $top_diag_fa_code = "SNAKE_LOG_EMPTY";
        delete $diag_fa_code{"SNAKE_LOG_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"SNAKE_LOGFILE_NOT_EXIST"}) {
        $top_diag_fa_code = "SNAKE_LOGFILE_NOT_EXIST";
        delete $diag_fa_code{"SNAKE_LOGFILE_NOT_EXIST"};
        return;
    }
    if (exists $diag_fa_code{"L1_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "L1_LOG_INCOMPLETE";
        delete $diag_fa_code{"L1_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"L1_LOG_EMPTY"}) {
        $top_diag_fa_code = "L1_LOG_EMPTY";
        delete $diag_fa_code{"L1_LOG_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"NIC_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "NIC_LOG_INCOMPLETE";
        delete $diag_fa_code{"NIC_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"NIC_LOG_EMPTY"}) {
        $top_diag_fa_code = "NIC_LOG_EMPTY";
        delete $diag_fa_code{"NIC_LOG_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"NIC_TXT_INCOMPLETE"}) {
        $top_diag_fa_code = "NIC_TXT_INCOMPLETE";
        delete $diag_fa_code{"NIC_TXT_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"NIC_TXT_EMPTY"}) {
        $top_diag_fa_code = "NIC_TXT_EMPTY";
        delete $diag_fa_code{"NIC_TXT_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"ETH_PRBS_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "ETH_PRBS_LOG_INCOMPLETE";
        delete $diag_fa_code{"ETH_PRBS_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"ETH_PRBS_LOG_EMPTY"}) {
        $top_diag_fa_code = "ETH_PRBS_LOG_EMPTY";
        delete $diag_fa_code{"ETH_PRBS_LOG_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"ARM_L1_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "ARM_L1_LOG_INCOMPLETE";
        delete $diag_fa_code{"ARM_L1_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"ARM_L1_LOG_EMPTY"}) {
        $top_diag_fa_code = "ARM_L1_LOG_EMPTY";
        delete $diag_fa_code{"ARM_L1_LOG_EMPTY"};
        return;
    }
    if (exists $diag_fa_code{"CARD_SPACE_FULL"}) {
        $top_diag_fa_code = "CARD_SPACE_FULL";
        delete $diag_fa_code{"CARD_SPACE_FULL"};
        return;
    }

    if (exists $diag_fa_code{"PS48_ERROR"}) {
        $top_diag_fa_code = "PS48_ERROR";
        delete $diag_fa_code{"PS48_ERROR"};
        return;
    }
    if (exists $diag_fa_code{"OOB_MNIC_NOT_ENABLED"}) {
        $top_diag_fa_code = "OOB_MNIC_NOT_ENABLED";
        delete $diag_fa_code{"OOB_MNIC_NOT_ENABLED"};
        return;
    }
    if (exists $diag_fa_code{"KEY_PROG_CRC_ERR"}) {
        $top_diag_fa_code = "KEY_PROG_CRC_ERR";
        delete $diag_fa_code{"KEY_PROG_CRC_ERR"};
        return;
    }
    if (exists $diag_fa_code{"ELBA_SELF_POWER_CYCLE(0x50)"}) {
        $top_diag_fa_code = "ELBA_SELF_POWER_CYCLE(0x50)";
        delete $diag_fa_code{"ELBA_SELF_POWER_CYCLE(0x50)"};
        return;
    }
    if (exists $diag_fa_code{"PSU1_NOT_INSTALLED"}) {
        $top_diag_fa_code = "PSU1_NOT_INSTALLED";
        delete $diag_fa_code{"PSU1_NOT_INSTALLED"};
        return;
    }

    if (exists $diag_fa_code{"PSU2_NOT_INSTALLED"}) {
        $top_diag_fa_code = "PSU2_NOT_INSTALLED";
        delete $diag_fa_code{"PSU2_NOT_INSTALLED"};
        return;
    }

    if (exists $diag_fa_code{"PSU1_CORD_NOT_CONNECTED"}) {
        $top_diag_fa_code = "PSU1_CORD_NOT_CONNECTED";
        delete $diag_fa_code{"PSU1_CORD_NOT_CONNECTED"};
        return;
    }

    if (exists $diag_fa_code{"PSU2_CORD_NOT_CONNECTED"}) {
        $top_diag_fa_code = "PSU2_CORD_NOT_CONNECTED";
        delete $diag_fa_code{"PSU2_CORD_NOT_CONNECTED"};
        return;
    }

    if (exists $diag_fa_code{"SCAN_VERIFY"}) {
        $top_diag_fa_code = "SCAN_VERIFY";
        delete $diag_fa_code{"SCAN_VERIFY"};
        return;
    }

    if (exists $diag_fa_code{"MGMT_PORT_FAILURE_UNKNOWN"}) {
        $top_diag_fa_code = "MGMT_PORT_FAILURE_UNKNOWN";
        delete $diag_fa_code{"MGMT_PORT_FAILURE_UNKNOWN"};
        return;
    }

    if (exists $diag_fa_code{"ALL_SLOTS_FAIL"}) {
        $top_diag_fa_code = "ALL_SLOTS_FAIL";
        delete $diag_fa_code{"ALL_SLOTS_FAIL"};
        return;
    }
    if (exists $diag_fa_code{"SLOTS_5_1_FAIL"}) {
        $top_diag_fa_code = "SLOTS_5_1_FAIL";
        delete $diag_fa_code{"SLOTS_5_1_FAIL"};
        return;
    }
    if (exists $diag_fa_code{"SLOTS_10_6_FAIL"}) {
        $top_diag_fa_code = "SLOTS_10_6_FAIL";
        delete $diag_fa_code{"SLOTS_10_6_FAIL"};
        return;
    }
    if (%diag_fa_code) {
        foreach my $diag_fa_code (keys %diag_fa_code) {
            $top_diag_fa_code = $diag_fa_code;# get the first fa code
            return;
        }
    }
}

sub parse_snake_log {
    my ($logfile, $sn, $test_and_failure_code) = @_;
    my $log_complete = 0;
    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"SNAKE_LOGFILE_NOT_EXIST"} = 1;
        return;
    }
    my $test_err_msg = "";
    my $test_name = substr($test_and_failure_code, 0, index($test_and_failure_code, ' '));

    my $err_found = 0;
    while(my $line = <TR3>)
    {
        if($err_found == 0 && $line =~ m/ERROR :: Link should be up with \w+, it is \w+/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            my $line2 = <TR3>;
            $test_err_msg .= $line2;
            $diag_fa_code{"SNAKE_PCIe_LINKUP"} = 1;
            $err_found = 1;
        }
        if($line =~ m/MSG ::  PCIE: txdetectrx failed for lane/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_PCIe_TXDETECTRX"} = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: elb(.*)(_ecc_|correctable|uncorrectable)(.*)interrupt/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_RAM_FAILURE"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: elb(.*)(_mc)(.*)interrupt/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"DDR_ECC_FAILURE"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: elb_mx_sync_rst :(.*)sync failed/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_MX_LINKUP"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/At \w+ interface :: current BW : (\d+) is less than min expected BW/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_THROUGHPUT_LOW"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: elb_top_dump_cntrs_compare: (.*)!=expected/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_CNT_MISCOMPARE"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: CRC ERROR HAPPENED!/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_CRC_ERROR"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/(.*)ERROR :: (.*)/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_OTHER"} = 1;
            $err_found = 1;
        }
        if ($line =~ m/MSG :: Snake Done/) {
            $log_complete = 1;
        }
    }
    if (-e -z $logfile) {
        $diag_fa_code{"SNAKE_LOG_EMPTY"} = 1;
    } elsif ($log_complete == 0) {
        $diag_fa_code{"SNAKE_LOG_INCOMPLETE"} = 1;
    }
    $all_test_msg .= "############### $test_and_failure_code ###############\n"."log file: ".$log_path."/".$logfile."\n\n";
    if ($test_err_msg ne "") {
        $all_test_msg .= $test_err_msg;
    } else {
        if (! exists $diag_fa_code{"SNAKE_LOG_EMPTY"}) {
            $diag_fa_code{"NO_ERR_IN_SNAKE_LOG"} = 1;
        }
    }
    close(TR3);
}

sub parse_l1_log {
    my ($logfile, $sn, $test_and_failure_code) = @_;
    my $log_complete = 0;
    my $subtest_start = 0;
    my @lines_saved;
    my $j2c_err_logged = 0;
    my $health_check_test = 0;

    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"L1_LOGFILE_NOT_EXIST"} = 1;
        return;
    }
    my $test_err_msg = "";
    while(my $line = <TR3>)
    {
        if (@lines_saved >= 25) {
            shift @lines_saved;
        }
        push(@lines_saved, $line);
        if($line =~ m/#FAIL#\s+(\w+)\s+\d+:\d+/) {
            if ($1 eq "elb_l1_ddr_bist") {
                $diag_fa_code{"L1_DDR_BIST"} = 1;
            } else {
                $all_l1_fails .= "_".uc($1);
            }
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
        }
        if($line =~ m/(.*)MSG ::.*HEALTH CHECK Started ===/) {
            $health_check_test = 1;
        }
        if($line =~ m/(.*)MSG ::.*HEALTH CHECK Done===/) {
            $health_check_test = 0;
        }
        if($line =~ m/(.*)MSG ::.*Started ===/) {
            $subtest_start = 1;
        }
        if($line =~ m/(.*)MSG ::.*Done===/) {
            $subtest_start = 0;
        }
        if ($subtest_start && ($line =~ m/ERROR ::/)) {
            if ($health_check_test && ($line =~ m/ERROR ::.*FAILED:/)) {
                $test_err_msg .= $lines_saved[-4].$lines_saved[-3].$lines_saved[-2].$lines_saved[-1];
            } else {
                $test_err_msg .= $line;
            }
        }
        if($line =~ m/(.*)MSG ::\s+L1_SCREEN (PASSED|FAILED)/) {
            $log_complete = 1;
        }
        if(($j2c_err_logged == 0) && ($line =~ m/MSG :: j2c : write req error/)) {
            $test_err_msg .= join("", @lines_saved);
            $j2c_err_logged = 1;
            $diag_fa_code{"Bad_J2C_L1"} = 1;
        }
        if(($j2c_err_logged == 0) && ($line =~ m/S2I Operation timed out/)) {
            $test_err_msg .= join("", @lines_saved);
            $j2c_err_logged = 1;
            $diag_fa_code{"Bad_J2C_L1"} = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."L1 log file: ".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
    if (-e -z $logfile) {
        $diag_fa_code{"L1_LOG_EMPTY"} = 1;
    } elsif ($log_complete == 0) {
        $diag_fa_code{"L1_LOG_INCOMPLETE"} = 1;
    }
    close(TR3);
}

sub parse_nic_test_logs {
    my ($testname, $txtfile, $logfile, $sn, $test_and_failure_code) = @_;
    my $test_err_msg = "";
    print "testname: $testname\n";
    my $teststart = qr/=== TEST STARTED === testID: \d+ testName: $testname/;
    my $testdone = qr/=== TEST DONE === testID: \d+ testName: $testname/;
    my $logend = "";
    if ($testname eq "ETH_PRBS") {
        $logend = qr/:: MX PRBS (PASSED|FAILED)/;
    } elsif ($testname eq "PCIE_PRBS") {
        $logend = qr/:: PCIE PRBS (PASSED|FAILED)/;
    } elsif ($testname eq "L1") {
        $logend = qr/:: ARM L1 TESTS (PASSED|FAILED)/;
    }

    if (!open(TR3, '<', $txtfile)) {
        $diag_fa_code{"NIC_TXTFILE_NOT_EXIST"} = 1;
    } else {
        my $start_capture = 0;
        my $txt_complete = 0;
        while(my $line = <TR3>)
        {
            if($line =~ m/$teststart/)
            {
                if ($debug_msgs) { print "line: $line"};
                $start_capture = 1;

            }
            if($line =~ m/$testdone/)
            {
                if ($debug_msgs) { print "line: $line"};
                $start_capture = 0;
                $txt_complete = 1;
            }
            if($line =~ m/\[ERROR\]/)
            {
                if ($start_capture) {
                    $test_err_msg .= $line;
		            if ($debug_msgs) { print "line: $line"};
                    if($line =~ m/core dumped/) {
                        $diag_fa_code{"${testname}_CORE_DUMPED"} = 1;
                    }
                }
            }
        }
        close(TR3);
        if (-e -z $txtfile) {
            $diag_fa_code{"NIC_TXT_EMPTY"} = 1;
        } elsif ($txt_complete == 0) {
            $diag_fa_code{"NIC_TXT_INCOMPLETE"} = 1;
        }
    }

    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"NIC_LOGFILE_NOT_EXIST"} = 1;
    } else {
	    my $log_complete = 0;
        my $prev_line = "";
        my $err_msg_num = 0;
        while(my $line = <TR3>)
        {
            if($line =~ m/ERROR :: elb_aapl_prbs_check :: sbus_addr/) {
                $test_err_msg .= $prev_line;
                $test_err_msg .= $line;
            } elsif(($line =~ m/ERROR/) && ($err_msg_num < 3))
            {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
                $err_msg_num++;
            }
            if(($line =~ m/MSG ::  PCIE: txdetectrx failed for lane/) && ($testname =~ "PCIE_PRBS"))
            {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
            }
            if(($line =~ m/\s+(\w+)\s+#FAILED#/) && ($testname =~ "L1"))
            {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
                my $arm_l1_failed_test = uc($1);
                print "arm l1 failed: $arm_l1_failed_test\n";
                $diag_fa_code{"ARM_L1_$arm_l1_failed_test"} = 1;
            }
            if($logend ne "" && $line =~ m/$logend/) {
                $log_complete = 1;
            }
            $prev_line = $line;
        }
        close(TR3);
        if (-e -z $logfile) {
            $diag_fa_code{"NIC_LOG_EMPTY"} = 1;
            return;
        } elsif ($log_complete == 0) {
            $diag_fa_code{"NIC_LOG_INCOMPLETE"} = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."txt file: ".$log_path."/".$txtfile."\n".$testname." log file: ".$log_path."/".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
}

sub parse_eth_prbs_log {
    my ($logfile, $sn, $test_and_failure_code) = @_;
    my $test_err_msg = "";
    my $err_msg_num = 0;

    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"ETH_PRBS_LOGFILE_NOT_EXIST"} = 1;
    } else {
	    my $log_complete = 0;
        while(my $line = <TR3>)
        {
            if($line =~ m/ERROR :: elb_aapl_prbs_check :: sbus_addr.*error count/) {
                $test_err_msg .= $line;
            } elsif(($line =~ m/ERROR/) && ($err_msg_num < 3)) {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
                $err_msg_num++;
            }
            if($line =~ m/:: MX PRBS (PASSED|FAILED)/) {
                $log_complete = 1;
            }
        }
        close(TR3);
        if (-e -z $logfile) {
            $diag_fa_code{"ETH_PRBS_LOG_EMPTY"} = 1;
        } elsif ($log_complete == 0) {
            $diag_fa_code{"ETH_PRBS_LOG_INCOMPLETE"} = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."eth_prbs log file: ".$log_path."/".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
}

sub parse_arm_l1_log {
    my ($logfile, $sn, $test_and_failure_code) = @_;
    my $test_err_msg = "";
    my $logend = qr/:: ARM L1 TESTS (PASSED|FAILED)/;

    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"ARM_L1_LOGFILE_NOT_EXIST"} = 1;
    } else {
	    my $log_complete = 0;
        while(my $line = <TR3>)
        {
            if($line =~ m/ERROR/) {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
            }
            if($line =~ m/\s+(\w+)\s+#FAILED#/) {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
                my $arm_l1_failed_test = uc($1);
                print "arm l1 failed: $arm_l1_failed_test\n";
                $diag_fa_code{"ARM_L1_$arm_l1_failed_test"} = 1;
            }
            if($logend ne "" && $line =~ m/$logend/) {
                $log_complete = 1;
            }
        }
        close(TR3);
        if (-e -z $logfile) {
            $diag_fa_code{"ARM_L1_LOG_EMPTY"} = 1;
        } elsif ($log_complete == 0) {
            $diag_fa_code{"ARM_L1_LOG_INCOMPLETE"} = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."arm_l1 log file: ".$log_path."/".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
}

sub find_failure_code {
    my ($fulllogpath, $sn, $toppath, $stage, $ts, $failedslot) = @_;
    my $mtp;
    my $slot;
    my $testname;
    my $failurecode;
    my $failuresn;
    my $bad_pcie=0;
    my $all_test_names = "";
    my $num_test_names = 0;
    my $all_failure_codes = "";
    my $asic_l1_failed = 0;
    my @tests_and_failure_codes;
    my $logfile=$fulllogpath."/"."mtp_test.log";
    if ($stage eq "FST") {
        $logfile=$fulllogpath."/"."test_fst.log";
    }

    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return 0;
    }
    while(my $line = <TR3>)
    {
        if($line =~ m/(.*)(ERR:\s\[)([\w-]+)(\]:\s\[NIC-)(\d+)(]:\s)(\w+)(\sDIAG\sTEST\s)([\w\-]+)(\s)(\w+)(\s)(FAIL|FAILED|FAILURE|TIMEOUT|SMB_READ_FAIL)/)
        {
            if ($debug_msgs) { print "line: $line"};
            $failuresn=$7;
            if ($sn eq $failuresn)
            {
                $mtp=$3;
                $slot=$5;
                $testname=$9;
                $failurecode=$11;

                printf "%-30s %-40s\n", "testname: ".$testname, "failurecode: ".$failurecode;
                $all_test_names .= $testname."\n";
                if ($testname =~ "LV_") {
                    $failurecode = "LV_".$failurecode;
                } elsif ($testname =~ "HV_") {
                    $failurecode = "HV_".$failurecode;
                }
                $all_failure_codes .= $failurecode."\n";
                push @tests_and_failure_codes, $testname." ".$failurecode;
                $num_test_names++;
            }
        }
    }

    chomp($all_test_names);
    chomp($all_failure_codes);
    $fa_row[$curr_row]{"Test"} = $all_test_names;
    $fa_row[$curr_row]{"MFG Error Code"} = $all_failure_codes;
    close(TR3);

    # filter on the test_name/mfg_err_code
    if ((index($all_test_names, $test_name_opt) == -1) ||
        (index($all_failure_codes, $mfg_err_code_opt) == -1)) {
        $diag_fa_code{"TEST_IGNORED"} = 1;
    }

    my $test_and_failure_code = "";
    $all_l1_fails = "L1_TST";
    foreach $test_and_failure_code (@tests_and_failure_codes) {
        print "test_and_failure_code: $test_and_failure_code\n";
        my $asic_log_dir = "";
        my $asic_txt_dir = "";
        my $test_name = substr($test_and_failure_code, 0, index($test_and_failure_code, ' '));
        my $failure_code = substr($test_and_failure_code, index($test_and_failure_code, ' ') + 1);

        if ($test_name =~ "LV_") {
            $asic_txt_dir = "/lv_nic_logs/";
            $asic_log_dir = "/lv_asic_logs/";
        } elsif ($test_name =~ "HV_") {
            $asic_txt_dir = "/hv_nic_logs/";
            $asic_log_dir = "/hv_asic_logs/";
        } else {
            $asic_txt_dir = "/nic_logs/";
            $asic_log_dir = "/asic_logs/";
        }

        if ($asic_log_dir ne "" && $failure_code =~ "SNAKE_ELBA") {
            my $snake_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_snake_elba.log";
            print "#### snake_log_file: $snake_log_file\n";
            parse_snake_log($snake_log_file, $sn, $test_and_failure_code);
        } elsif ($asic_log_dir ne "" && $failure_code =~ "L1" && $failure_code !~ "ARM_L1") {
            if (index($test_name, "NIC") == -1) {
                $asic_l1_failed = 1;
                my $l1_path = $log_path."/".$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir;
                my @l1_log_files = glob("${l1_path}*l1_screen_board_${sn}_*");
                if (@l1_log_files) {
                    my $l1_log_file= $l1_log_files[0];
                    print "#### l1_log_file: $l1_log_file\n";
                    parse_l1_log($l1_log_file, $sn, $test_and_failure_code, $all_l1_fails);
                } else {
                    $diag_fa_code{"L1_LOGFILE_NOT_EXIST"} = 1;
                }
            } else {
                my $nic_l1_txt_file1=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."AAPL-NIC-".$slot."/log_NIC_ASIC.txt";
                my $nic_l1_txt_file2=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."NIC-".$slot."/log_NIC_ASIC.txt";
                my $nic_l1_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_arm_l1_test.log";
                my $nic_l1_txt_file = $nic_l1_txt_file1;
                if (open(TXT, '<', $nic_l1_txt_file1)) {
                    my $test_found = 0;
                    while(my $line = <TXT>)
                    {
                        if($line =~ m/testName: L1/) {
                            $test_found = 1;
                            last;
                        }
                    }
                    close(TXT);
                    if ($test_found == 0) {
                        $nic_l1_txt_file = $nic_l1_txt_file2;
                    }
                } else {
                    $nic_l1_txt_file = $nic_l1_txt_file2;
                }
                print "#### NIC_l1_txt_file: $nic_l1_txt_file\n";
                print "#### NIC_l1_log_file: $nic_l1_log_file\n";
                parse_nic_test_logs("L1", $nic_l1_txt_file, $nic_l1_log_file, $sn, $test_and_failure_code);
            }
        } elsif ($asic_log_dir ne "" && $failure_code =~ "ARM_L1") {
            my $arm_l1_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_arm_l1_test.log";
            print "#### ARM_L1_log_file: $arm_l1_log_file\n";
            parse_arm_l1_log($arm_l1_log_file, $sn, $test_and_failure_code);
        } elsif ($asic_log_dir ne "" && $failure_code =~ "PCIE_PRBS") {
            my $pcie_prbs_txt_file1=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."AAPL-NIC-".$slot."/log_NIC_ASIC.txt";
            my $pcie_prbs_txt_file2=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."NIC-".$slot."/log_NIC_ASIC.txt";
            my $pcie_prbs_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_PRBS_PCIE.log";
            my $pcie_prbs_txt_file = $pcie_prbs_txt_file1;
            if (open(TXT, '<', $pcie_prbs_txt_file1)) {
                my $test_found = 0;
                while(my $line = <TXT>)
                {
                    if($line =~ m/testName: PCIE_PRBS/) {
                        $test_found = 1;
                        last;
                    }
                }
                close(TXT);
                if ($test_found == 0) {
                    $pcie_prbs_txt_file = $pcie_prbs_txt_file2;
                }
            } else {
                $pcie_prbs_txt_file = $pcie_prbs_txt_file2;
            }
            print "#### PCIE_PRBS_txt_file: $pcie_prbs_txt_file\n";
            print "#### PCIE_PRBS_log_file: $pcie_prbs_log_file\n";
            $diag_fa_code{"PCIE_PRBS_FAILURE"} = 1;
            parse_nic_test_logs("PCIE_PRBS", $pcie_prbs_txt_file, $pcie_prbs_log_file, $sn, $test_and_failure_code);
        } elsif ($asic_log_dir ne "" && $failure_code =~ "ETH_PRBS") {
            #my $eth_prbs_txt_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."AAPL-NIC-".$slot."/log_NIC_ASIC.txt";
            my $eth_prbs_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_PRBS_MX.log";
            #print "#### ETH_PRBS_txt_file: $eth_prbs_txt_file\n";
            print "#### ETH_PRBS_log_file: $eth_prbs_log_file\n";
            $diag_fa_code{"ETH_PRBS_FAILURE"} = 1;
            parse_eth_prbs_log($eth_prbs_log_file, $sn, $test_and_failure_code);
        } elsif ($failure_code =~ "EDMA") {
            $diag_fa_code{"${failure_code}_FAILURE"} = 1;
        } elsif ($failure_code =~ "PCIE_LINK") {
            parse_fst_pcie_link($fulllogpath, $slot, $test_and_failure_code);
        } elsif ($failure_code =~ "ROT") {
            parse_fst_rot($fulllogpath, $slot, $test_and_failure_code);
        }

        if (($failure_code =~ "NIC_PARA_MGMT_INIT") || ($failure_code =~ "NIC_MGMT_INIT") || ($failure_code =~ "NIC_PARA_MGMT_FPO_INIT")) {
            parse_mgmt_failure($fulllogpath, $slot);
            if (%diag_fa_code == 0) {
                $diag_fa_code{"MGMT_PORT_FAILURE_UNKNOWN"} = 1;
            }
        }
        if (($failure_code =~ "RMII_LINKUP") || ($failure_code =~ "UART_LPBACK")) {
            parse_ncsi_failure($fulllogpath, $slot);
        }
        if ($test_name eq "QSFP" && $failure_code eq "I2C") {
            $diag_fa_code{"QSFP_I2C"} = 1;
        }
        if ($failure_code eq "CONSOLE_BOOT") {
            if (%diag_fa_code == 0) {
                $diag_fa_code{"CONSOLE_BOOT_UNKNOWN"} = 1;
            }
        }
        if (($failure_code eq "DDR_BIST") || ($failure_code eq "LV_DDR_BIST") || ($failure_code eq "HV_DDR_BIST")) {
            $diag_fa_code{"ARM_DDR_BIST"} = 1;
        }
        if ($test_name eq "SWI" && $failure_code eq "EFUSE_PROG") {
            $diag_fa_code{"EFUSE_PROG"} = 1;
        }
        if ($test_name eq "SWI" && $failure_code eq "SW_BOOT") {
            $diag_fa_code{"SW_BOOT"} = 1;
        }
    }
    if ($stage ne "FST") {
        parse_mtp_and_slot_log($fulllogpath, $failedslot, $stage, $all_failure_codes);
    } else {
        parse_fst_log($fulllogpath, $failedslot, $all_failure_codes);
    }
    if ($all_test_msg eq "") {
        $all_test_msg = "log path: ".$fulllogpath."\n";
    }
    if ($all_l1_fails ne "L1_TST") {
        $diag_fa_code{$all_l1_fails} = 1;
    }
    return $asic_l1_failed;
}

sub parse_fst_pcie_link {
    my ($fulllogpath, $slot, $test_and_failure_code) = @_;
    my $logfile=$fulllogpath."/"."test_fst.log";
    my $test_err_msg = "";
    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if($line =~ m/\[NIC-(\d+)\]:\s+PCIE link (speed|width) fails/) {
            if ($1 eq $slot) {
	            if ($debug_msgs) { print "line: $line"};
	            $test_err_msg .= $line;
                $diag_fa_code{"PCIE_LINK_SPEED_WIDTH"} = 1;
            }
        }
    }
    if ($test_err_msg ne "") {
        $all_test_msg .= "log path: ".$fulllogpath."\n";
        $all_test_msg .= $test_err_msg;
    }
    close(TR3);
}

sub parse_fst_rot {
    my ($fulllogpath, $slot, $test_and_failure_code) = @_;
    my $fstlogfile=$fulllogpath."/"."test_fst.log";
    my $test_err_msg = "";
    my $state_linenum = 0;
    my $fail_linenum = 0;
    my @fa_code;
    my $fa_code_str = "";
    my $cable_connected = 0;

    if (!open(TR3, '<', $fstlogfile)) {
        print "Cannot open file $fstlogfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($line =~ m/NIC at serial port (\w+) failed/) {
            my $usbport = $1;
            my $rotfile = $fulllogpath."/"."rot_$usbport.log";
            $test_err_msg .= $line;
            $cable_connected = 1;
            if (!open(TR, '<', $rotfile)) {
                print "Cannot open file $rotfile\n";
                next;
            }
            while(my $rotline = <TR>) {
                if ($rotline =~ m/after (dtr|rts) state/) {
                    $state_linenum = $.;
                }
                if ($rotline =~ m/invalid qspi device id read/) {
                        #$diag_fa_code{"INVALID_QSPI_ID_$usbport"} = 1;
                        push(@fa_code, "INVALID_QSPI_ID_$usbport");
                        $test_err_msg .= $rotline;
                }
                if ($rotline =~ m/possible bad cable/) {
                        #$diag_fa_code{"BAD_CABLE_$usbport"} = 1;
                        push(@fa_code, "BAD_CABLE_$usbport");
                        $test_err_msg .= $rotline;
                }
                if ($rotline =~ m/possible NIC console is dead/) {
                        #$diag_fa_code{"CONSOLE_DEAD_$usbport"} = 1;
                        push(@fa_code, "CONSOLE_DEAD_$usbport");
                        $test_err_msg .= $rotline;
                }
                if (($rotline =~ m/force gold is not set as expected/) ||
                    ($rotline =~ m/force gold is not cleared as expected/) ||
                    ($rotline =~ m/failed to connect nic after forcing goldfw/) ||
                    ($rotline =~ m/failed to find gold-fw prompt, possible still in mainfw/)) {
                        @fa_code = grep(!/DTR_FAILURE_$usbport/, @fa_code);
                        #$diag_fa_code{"RTS_FAILURE_$usbport"} = 1;
                        push(@fa_code, "RTS_FAILURE_$usbport");
                        $test_err_msg .= $rotline;
                }
                if ($rotline =~ m/failed to connect to nic/) {
                    $fail_linenum = $.;
                    if ($fail_linenum - $state_linenum > 4) {
                        #$diag_fa_code{"CARD_REBOOTED_$usbport"} = 1;
                        push(@fa_code, "CARD_REBOOTED_$usbport");
                        $test_err_msg .= $rotline;
                    }
                } else {
                    if ($rotline =~ m/failed to connect/) {
                        my $rotline2 = <TR>;
                        if ($rotline2 =~ m/get data from uart register, possible dtr signal is wrong/) {
                            #$diag_fa_code{"DTR_FAILURE_$usbport"} = 1;
                            push(@fa_code, "DTR_FAILURE_$usbport");
                            $test_err_msg .= $rotline;
                            $test_err_msg .= $rotline2;
                        }
                    }
                }

            }
            close(TR);
        }
    }
    if ($cable_connected == 0) {
        $diag_fa_code{"CABLE_NOT_CONNECTED"} = 1;
    } else {
        foreach (@fa_code) {
            print "fa code is: $_\n";
            $fa_code_str .= $_."\n";
        }
        $diag_fa_code{$fa_code_str} = 1;
    }
    if ($test_err_msg ne "") {
        $all_test_msg .= "log path: ".$fulllogpath."\n";
        $all_test_msg .= $test_err_msg;
    }
    close(TR3);
}

sub parse_mgmt_failure {
    my ($fulllogpath, $slot) = @_;
    my $mtpdiagfile=$fulllogpath."/"."mtp_diag.log";
    my $mtp_diag_msg = "";
    my $halctl_slot_info = 0;
    my $eth1_3_down = 0;
    my $slotnum = 0 + $slot;

    if (!open(TR3, '<', $mtpdiagfile)) {
        print "Cannot open file $mtpdiagfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($line =~ m/cpldutil \-cpld\-wr \-addr=0x18 \-data=$slotnum/) {
            $halctl_slot_info = 1;
        }
        if ($halctl_slot_info && $line =~ m/^Eth1\/3/ && $line !~ m/Eth1\/3    UP          UP        -/ ) {
            $mtp_diag_msg .= $line;
            $eth1_3_down = 1;
        }
        if ($eth1_3_down != 0 && $line =~ m/exit/) {
            $eth1_3_down = 0;
        }
        if ($eth1_3_down != 0 && $line =~ m/-smird 0 0x3/) {
            $mtp_diag_msg .= $line;
            my $line2 = <TR3>;
            $mtp_diag_msg .= $line2;
            if ($line2 =~ m/0xffff/ && $card_type =~ m/ORTANO/) {
                $diag_fa_code{"MVL_ACC_FAILURE"} = 1;
            } else {
                $diag_fa_code{"ETH1/3_PORT_DOWN"} = 1;
            }
        }
        if (($line =~ m/PS48 Error:/) && (! exists $diag_fa_code{"PS48_ERROR"})) {
            $mtp_diag_msg .= $line;
            $diag_fa_code{"PS48_ERROR"} = 1;
        }
    }
    if ($mtp_diag_msg ne "") {
        $all_test_msg .= "\n--------mtp_diag log--------: ".$mtpdiagfile."\n";
        $all_test_msg .= $mtp_diag_msg;
    }
    close(TR3);
}

sub parse_ncsi_failure {
    my ($fulllogpath, $slot) = @_;
    my $mtpdiagfile=$fulllogpath."/"."mtp_diag.log";
    my $mtp_diag_msg = "";
    my $slotnum = 0 + $slot;

    if (!open(TR3, '<', $mtpdiagfile)) {
        print "Cannot open file $mtpdiagfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($line =~ m/slot $slotnum Reg 0x9C, expect: 0xe, actual: 0xc/) {
            $mtp_diag_msg .= $line;
            $diag_fa_code{"NCSI_LOOPBACK_MISSING"} = 1;
        }
    }
    if ($mtp_diag_msg ne "") {
        $all_test_msg .= "\n--------mtp_diag log--------: ".$mtpdiagfile."\n";
        $all_test_msg .= $mtp_diag_msg;
    }
    close(TR3);
}

sub parse_fst_log {
    my ($fulllogpath, $slot, $failure_code_list) = @_;
    my $fstfile=$fulllogpath."/"."test_fst.log";
    my $fst_test_msg = "";
    my $test_err_msg = "";

    if (!open(TR3, '<', $fstfile)) {
        print "Cannot open file $fstfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if (($line =~ m/\[NIC-$slot\]: 3th: Pre-Post \[\w+\] result to webserver failed/) ||
            ($line =~ m/\[NIC-$slot\]: Pre-Post \[\w+\] result to webserver failed/) ||
            ($line =~ m/\[NIC-$slot\]: \w+: Pre-Post \[\w+\] result to webserver failed.*(500|600142250)/)) {
            $fst_test_msg .= $line;
            $diag_fa_code{"2WAY_COMMUNICATION_FAILURE"} = 1;
        }
    }
    if ($fst_test_msg ne "") {
        $test_err_msg .= "\n--------test_fst log--------: ".$fstfile."\n";
        $test_err_msg .= $fst_test_msg;
    }
    close(TR3);

    if ($test_err_msg ne "") {
        $all_test_msg .= $test_err_msg;
    }
}

sub parse_mtp_and_slot_log {
    my ($fulllogpath, $slot, $stage, $failure_code_list) = @_;
    my $mtpfile=$fulllogpath."/"."mtp_test.log";
    my $slotlogfile=$fulllogpath."/"."mtp_NIC-".$slot."_diag.log";
    my $slot_err_msg = "";
    my $mtp_test_msg = "";
    my $test_err_msg = "";
    my $jtag_log = 0;
    my $err_msg_dump = 0;
    my $nic_status_dump = 0;
    my $slotnum = 0 + $slot;
    my $vmarg_low_start = 0;
    my $vmarg_low_start_linenum = 0;
    my $vmarg_high_start = 0;
    my $vmarg_high_start_linenum = 0;

    if (!open(TR3, '<', $slotlogfile)) {
        print "Cannot open file $slotlogfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if($line =~ m/\[ERROR\]/ && $line !~ m/Unsupported device: CPLD_ADAP/ && $line !~ m/smbus\.go/ && $line !~ m/Failed to read device CPLD at/ && $line !~ m/elb_mc_mr_/) {
	        if ($debug_msgs) { print "line: $line"};
	        $slot_err_msg .= $line;
	        #last;
        }
        if ($line =~ m/cat \/sys\/block\/mmcblk0\/device\/manfid/) {
            my $line2 = <TR3>;
	        if ($line2 =~ m/0x000013/) {
                $fa_row[$curr_row]{"EMMC Vendor"} = "Micron";
            } elsif ($line2 =~ m/0x000045/) {
                $fa_row[$curr_row]{"EMMC Vendor"} = "WDC";
            }
        }
        if ($line =~ m/No space left on device/) {
            $diag_fa_code{"CARD_SPACE_FULL"} = 1;
	        $slot_err_msg .= $line;
        }
        if ($line =~ m/Resetting CPU/) {
            $diag_fa_code{"CARD_RESET"} = 1;
	        $slot_err_msg .= $line;
        }
        if ($line =~ m/ifconfig: SIOCSIFADDR: No such device/) {
            $diag_fa_code{"OOB_MNIC_NOT_ENABLED"} = 1;
	        $slot_err_msg .= $line;
        }
        if ($line =~ m/elba\-gold login/) {
            $diag_fa_code{"BOOT_GOLDFW"} = 1;
	        $slot_err_msg .= $line;
        }
        if ($line =~ m/DSC# fwupdate -s diagfw/) {
            $diag_fa_code{"BOOT_UBOOT"} = 1;
            $slot_err_msg .= $line;
        }
        if (index($failure_code_list, "NIC_JTAG") != -1) {
            if ($line =~ m/NIC_JTAG Started/) {
                $jtag_log = 1;
            }
            if ($line =~ m/NIC_JTAG Stopped/) {
                $jtag_log = 0;
            }
            if ($jtag_log != 0) {
	            $slot_err_msg .= $line;
            }
        }
        if ($line =~ m/\/home\/diag\/diag\/scripts\/vmarg\.sh low/) {
            $vmarg_low_start = 1;
            $vmarg_low_start_linenum = $.;
        }
        if ($line =~ m/=== Vmarg is at low ===/) {
            my $line2 = <TR3>;
            if ($line2 =~ /sync/) {
                my $line3 = <TR3>;
                if ($line3 =~ /exit/) {
                    my $line4 = <TR3>;
                    if ($line4 =~ /Connection to .* closed./) {
                        if ($vmarg_low_start == 1) {
                            $vmarg_low_start = 0;
                        }
                    }
                }
            }
        }
        if ($line =~ m/\/home\/diag\/diag\/scripts\/vmarg\.sh high/) {
            $vmarg_high_start = 1;
            $vmarg_high_start_linenum = $.;
        }
        if ($line =~ m/=== Vmarg is at high ===/) {
            my $line2 = <TR3>;
            if ($line2 =~ /sync/) {
                my $line3 = <TR3>;
                if ($line3 =~ /exit/) {
                    my $line4 = <TR3>;
                    if ($line4 =~ /Connection to .* closed./) {
                        if ($vmarg_high_start == 1) {
                            $vmarg_high_start = 0;
                        }
                    }
                }
            }
        }
        if ($line =~ m/Timeout, server .* not responding/) {
            $slot_err_msg .= $line;
            if (($vmarg_low_start == 1) && ($. - $vmarg_low_start_linenum  < 30)) {
                $diag_fa_code{"VMARG_L_SSH_HUNG"} = 1;
            } elsif (($vmarg_high_start == 1) && ($. - $vmarg_high_start_linenum  < 30)) {
                $diag_fa_code{"VMARG_H_SSH_HUNG"} = 1;
            } else {
                $diag_fa_code{"NIC_UNRESP_SSH_HUNG"} = 1;
            }
        }
        if ($line =~ m/VRM_ARM        VBOOT/) {
            if ($. - $vmarg_low_start_linenum  < 800) {
                my $line2 = <TR3>;
                if ($line2 =~ /.*MSG ::\s+(\d\.\d+)\s+(\d\.\d+)\s+.*/) {
                    my $vboot = $1 * 1000;
                    my $vout = $2 * 1000;
                    if ($vout < $vboot * 0.95) {
                        $slot_err_msg .= $line;
                        $slot_err_msg .= $line2;
                        $diag_fa_code{"VMARG_L_VOLT_LOW"} = 1;
                    }
                }
            }
        }
        if ($line =~ m/DSC# uptime/) {
            if ($. - $vmarg_low_start_linenum  < 100) {
                $slot_err_msg .= $line;
                $diag_fa_code{"VMARG_L_BOOT_UBOOT"} = 1;
            }
            if ($. - $vmarg_high_start_linenum  < 100) {
                $slot_err_msg .= $line;
                $diag_fa_code{"VMARG_H_BOOT_UBOOT"} = 1;
            }
        }
        if ($stage eq "NT" || $stage eq "4C-L" || $stage eq "4C-H") {
            if (($line =~ m/env \| grep -v PS1/) && ($line !~ m /DSC#/)) {
                my $line2 = <TR3>;
                if ($line2 !~ m/ASIC_LIB=/) {
                    if (($. - $vmarg_low_start_linenum  < 200) && (exists $diag_fa_code{"VMARG_L_SSH_HUNG"})) {
                        $diag_fa_code{"VMARG_L_CARD_REBOOTED"} = 1;
                    } elsif (($. - $vmarg_high_start_linenum  < 200) && (exists $diag_fa_code{"VMARG_H_SSH_HUNG"})) {
                        $diag_fa_code{"VMARG_H_CARD_REBOOTED"} = 1;
                    } else {
                        $diag_fa_code{"CARD_REBOOTED"} = 1;
                    }
                }
            }
        }
        if ($line =~ m/\/data\/nic_util\/mvl_acc\.sh/) {
            my $line2 = <TR3>;
            if ($line2 !~ m/MVL ACC TEST PASSED/) {
                $slot_err_msg .= $line;
                $slot_err_msg .= $line2;
                $diag_fa_code{"MVL_ACC_FAILURE"} = 1;
            }
        }
        if ($line =~ m/\/data\/nic_util\/mvl_link\.sh/) {
            my $line2 = <TR3>;
            my $line3 = <TR3>;
            if ($line3 !~ m/MVL RJ45 port link is up/) {
                $slot_err_msg .= $line;
                $slot_err_msg .= $line2;
                $slot_err_msg .= $line3;
                $diag_fa_code{"MVL_LINK_DOWN"} = 1;
            }
        }
        if ($line =~ m/\/emmc_format\.sh/) {
            my $line2 = <TR3>;
            if ($line2 =~ m/open: No such file or directory/) {
                $slot_err_msg .= $line;
                $slot_err_msg .= $line2;
                $diag_fa_code{"EMMC_ERR"} = 1;
            }
        }
        if ($line =~ m/CRC32 cross check failed; Caculated.*Uboot.*/) {
            $slot_err_msg .= $line;
            $diag_fa_code{"KEY_PROG_CRC_ERR"} = 1;
        }
        if ($line =~ m/ERROR :: mc\d initialization failed w/) {
            $slot_err_msg .= $line;
            $diag_fa_code{"DDR_INIT_FAILURE"} = 1;
        }
    }
    if ($slot_err_msg ne "") {
        $test_err_msg .= "\n--------slot log--------: ".$slotlogfile."\n";
        $test_err_msg .= $slot_err_msg;
    }
    close(TR3);

    if (!open(TR3, '<', $mtpfile)) {
        print "Cannot open file $mtpfile\n";
        return;
    }

    while(my $line = <TR3>)
    {
        if (index($failure_code_list, "SW_PN_CHECK") != -1) {
            if ($line =~ m/\[NIC-$slot\].*Check SOFTWARE IMAGE PN.*CARD PN/) {
                $mtp_test_msg .= $line;
                my $line2 = <TR3>;
                $mtp_test_msg .= $line2;
                if ($line2 =~ m/Check PN REV: Software Image match to nic part number failed/) {
                    $diag_fa_code{"INCORRECT_PN_REV"} = 1;
                } elsif ($line2 =~ m/Check SWI Software Image: Software Image match to nic part number failed/) {
                    $diag_fa_code{"PN_SW_MATCH_ERR"} = 1;
                }
            }
            if ($line =~ m/\[NIC-$slot\].*Check SWI Software Image: Retreive PN Failed/) {
                $mtp_test_msg .= $line;
                $diag_fa_code{"RETREIVE_PN_FAIL"} = 1;
            }
        }
        if (index($failure_code_list, "SCAN_VERIFY") != -1) {
            if ($line =~ m/\[NIC-$slot\].*Incorrect (SN|MAC|PN). Scanned.*read.*/) {
                $mtp_test_msg .= $line;
                $diag_fa_code{"INCORRECT_$1"} = 1;
            } else {
                if ($line =~ m/\[NIC-$slot\].*Missing scan for this slot/) {
                    $mtp_test_msg .= $line;
                }
                $diag_fa_code{"SCAN_VERIFY"} = 1;
            }
        }
        if (index($failure_code_list, "VDD_DDR_VERIFY") != -1) {
            if ($line =~ m/\[NIC-$slot\].*VDD_DDR_VERIFY.*STARTED/) {
                $err_msg_dump = 1;
            }
            if ($line =~ m/\[NIC-$slot\].*VDD_DDR_VERIFY FAILED/) {
                $err_msg_dump = 0;
            }
            # if ($line =~ m/\[NIC-$slot\]: ==== Error Message Start: ====/) {
            #     $err_msg_dump = 1;
            # }
            # if ($line =~ m/\[NIC-$slot\]: ==== Error Message End: ====/) {
            #     $err_msg_dump = 0;
            # }
            if ($err_msg_dump != 0) {
                $mtp_test_msg .= $line;
            }
        }
        if (index($failure_code_list, "NIC_STATUS") != -1) {
            if ($line =~ m/\[NIC-$slot\].*PRE_CHECK NIC_STATUS FAIL/) {
                $nic_status_dump = 1;
            }
            if ($line =~ m/DIAG TEST.*STARTED/) {
                $nic_status_dump = 0;
            }
            if ($nic_status_dump != 0) {
                $mtp_test_msg .= $line;
            }
        }
        if (index($failure_code_list, "NIC_BOOT_INIT") != -1) {
            if ($line =~ m/\[NIC-$slot\].*DIAG_INIT NIC_BOOT_INIT FAILED/) {
                $nic_status_dump = 1;
            }
            if ($line =~ m/DIAG TEST.*STARTED/) {
                $nic_status_dump = 0;
            }
            if ($nic_status_dump != 0) {
                $mtp_test_msg .= $line;
            }
        }

        if ($line =~ m/\[NIC-$slot\].*MVL (ACC|STUB|LINK) FAIL/) {
            $nic_status_dump = 1;
        }
        if ($line =~ m/DIAG TEST.*STARTED/) {
            $nic_status_dump = 0;
        }
        if ($nic_status_dump != 0) {
            $mtp_test_msg .= $line;
        }
        if ($line =~ m/\[NIC-$slot\].*Timeout connecting to UART console/) {
            $mtp_test_msg .= $line;
            $diag_fa_code{"CONSOLE_UNRESP"} = 1;
        }
        if (($line =~ m/\[NIC-$slot\]: 3th: Pre-Post \[\w+\] result to webserver failed/) ||
            ($line =~ m/\[NIC-$slot\]: Pre-Post \[\w+\] result to webserver failed/) ||
            ($line =~ m/\[NIC-$slot\]: \w+: Pre-Post \[\w+\] result to webserver failed.*(500|600142250)/)) {
            $mtp_test_msg .= $line;
            $diag_fa_code{"2WAY_COMMUNICATION_FAILURE"} = 1;
        }
        #if ($line =~ m/\[NIC-$slot\]: ==== Error Message Start: ====/) {
        #    $err_msg_dump = 1;
        #}
        #if ($line =~ m/\[NIC-$slot\]: ==== Error Message End: ====/) {
        #    $err_msg_dump = 0;
        #}
        #if ($err_msg_dump != 0) {
        #    $mtp_test_msg .= $line;
        #}
    }
    if ($mtp_test_msg ne "") {
        $test_err_msg .= "\n--------mtp_test log--------: ".$mtpfile."\n";
        $test_err_msg .= $mtp_test_msg;
    }
    close(TR3);

    if ($test_err_msg ne "") {
        $all_test_msg .= $test_err_msg;
    }
}

sub parse_fpga_and_ecc {
    my ($mtpfile, $logfile, $sn, $ts, $l1_failed) = @_;
    my $test_err_msg = "";
    print "#### parse_fpga_and_ecc logfile: $logfile, l1_failed: $l1_failed\n";

    my $sts_dump_exist = 0;
    my $old_ecc_dump_exist = 0;
    my $new_ecc_dump_exist = 0;
    #my $corr_syn = 0;
    #my $multi_corr_syn = 0;
    #my $uncorr_syn = 0;
    #my $multi_uncorr_syn = 0;
    my $cpld_sts = "";
    my $num_cpld_sts_errors = 0;
    my $ecc_sts = "";
    my $num_ecc_sts_errors = 0;
    my $smbus_err = 0;
    my $asic_pin_sts_0;
    my $asic_pin_sts_1;
    my $asic_pin_sts_2;
    my $power_failure_12v = 0;
    my $power_cycle_reason;
    my $j2c_error_linenum = 0;
    my $ecc_reg_linenum = 0;
    my $ecc_start_linenum = 0;
    my $ecc_result_linenum = 0;
    my $ecc_not_valid = 0;
    my $ecc_result_exist = 0;
    my $ecc_result_exist_current = 0;
    my $ecc_result_err = 0;
    my $ecc_result_err_current = 0;
    my $c92_upgrade = 0;
    my $mtp_failed_slots = 0x0;
    my $mtp_loaded_slots = 0x0;
    my $ecc_disp_start = 0;
    my $ecc_j2c_s2i_timeout = 0;
    my $ecc_j2c_error = 0;
    my $ecc_j2c_error_current = 0;
    my $mc_info;
    my $mc_int_status = "";

    if (!open(TR3, '<', $mtpfile)) {
        print "Cannot open file $mtpfile\n";
        return;
    }

    while(my $line = <TR3>)
    {
        if ($line =~ m/NIC\-([0-9]+).*NIC_DIAG_REGRESSION_TEST_(PASS|FAIL)/) {
            my $slot_num = $1;
            $slot_num += 0;
            if ($2 eq "FAIL") {
                $mtp_failed_slots |= 0x1 << ($slot_num - 1);
                #printf("mtp_failed_slots: 0x%x\n", $mtp_failed_slots);
            }
            $mtp_loaded_slots |= 0x1 << ($slot_num - 1);
        }
    }
    close(TR3);

    if (($mtp_failed_slots & $mtp_loaded_slots) == $mtp_loaded_slots) {
        $diag_fa_code{"ALL_SLOTS_FAIL"} = 1;
    } elsif ((($mtp_loaded_slots & 0x3e0) != 0) && ($mtp_failed_slots & ($mtp_loaded_slots & 0x3e0)) == ($mtp_loaded_slots & 0x3e0)) {
        $diag_fa_code{"SLOTS_10_6_FAIL"} = 1;
    } elsif ((($mtp_loaded_slots & 0x1f) != 0) && ($mtp_failed_slots & ($mtp_loaded_slots & 0x1f)) == ($mtp_loaded_slots & 0x1f)) {
        $diag_fa_code{"SLOTS_5_1_FAIL"} = 1;
    }

    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($line =~ m/START post dsp NIC_POWER fail debug/) {
            my $line2;
            do {
                $line2 = <TR3>;
            } while ($line2 !~ m/END post dsp NIC_POWER fail debug/);
        }
        if ($sts_dump_exist == 0) {
            if($line =~ m/(.*)(Addr: 0x21; Value:)\s(\w+)/) {
                my $line2 = <TR3>;
                if ($line2 =~ m/smbus\.go/) {
                    $diag_fa_code{"CANNOT_READ_CPLD_STATUS_DUE_TO_SMBUS_ERR"} = 1;
                    $smbus_err = 1;
                } else {
                    if (($3 ne "0x2d") && ($3 ne "0x35")) {
                        $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x21, expected: 0x2d, actual: $3\n";
                        $num_cpld_sts_errors++;
                        $diag_fa_code{"CON_REDIR_FAILURE(0x21)"} = 1;
                    }
                    if($line2 =~ m/(.*)(Addr: 0x26; Value:)\s(\w+)/) {
                        if ($smbus_err == 0 && ((hex($3) | 0x20) != 0x27)) {
                            $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x26, expected: 0x27 or 0x07, actual: $3\n";
                            $num_cpld_sts_errors++;
                            $diag_fa_code{"ASIC_PIN_STATUS_0_FAILURE(0x26)"} = 1;
                        }
                        $asic_pin_sts_0 = $3;
                    }
                }
            }

            if($line =~ m/(.*)(Addr: 0x27; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0xee") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x27, expected: 0xee, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"ASIC_PIN_STATUS_1_FAILURE(0x27)"} = 1;
                }
                $asic_pin_sts_1 = $3;
            }
            if($line =~ m/(.*)(Addr: 0x28; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0xdf") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x28, expected: 0xdf, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"ASIC_PIN_STATUS_2_FAILURE(0x28)"} = 1;
                }
                $asic_pin_sts_2 = $3;
            }
            if($line =~ m/(.*)(Addr: 0x2a; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x2a, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"PUF_ERRORS(0x2a)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x2b; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x2b, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"CORE_PLL_FAILURE(0x2b)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x2c; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x2c, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"CPU_PLL_FAILURE(0x2c)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x2d; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x2d, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"FLASH_PLL_FAILURE(0x2d)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x2e; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x2e, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"PCIE_PLL_FAILURE(0x2e)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x30; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x30, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"NIC_POWER_FAILURE"} = 1;
                    if (hex($3) & 0x1 == 0x1) {
                        $power_failure_12v = 1;
                        print "asic_pin_sts_0: $asic_pin_sts_0, asic_pin_sts_1: $asic_pin_sts_1, asic_pin_sts_2: $asic_pin_sts_2\n"
                    }
                }
            }
            if($line =~ m/(.*)(Addr: 0x31; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x31, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"NIC_POWER_FAILURE"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x32; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0x00") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x32, expected: 0x00, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"NIC_POWER_FAILURE"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x50; Value:)\s(\w+)/) {
                if ($smbus_err == 0) {
                    $power_cycle_reason = $3;
                    if ($power_cycle_reason ne "0x80") {
                        if (!($l1_failed && ($power_cycle_reason eq "0x81"))) { #expected
                            $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x50, expected: 0x80, actual: $power_cycle_reason\n";
                            $num_cpld_sts_errors++;
                            if (hex($power_cycle_reason) & 0x8) {
                                $diag_fa_code{"TEMP_TRIP_FAILURE(0x50)"} = 1;
                            } elsif (hex($power_cycle_reason) & 0x1) {
                                $diag_fa_code{"ELBA_SELF_POWER_CYCLE(0x50)"} = 1;
                            } elsif ($power_cycle_reason eq "0x90" && $power_failure_12v == 1 && $asic_pin_sts_0 eq "0x00" && $asic_pin_sts_1 eq "0x00" && $asic_pin_sts_2 eq "0x00") {
                                $diag_fa_code{"NIC_POWER_FAILURE_12V_LOST"} = 1;
                            } else {
                                $diag_fa_code{"OTHER_POWER_CYCLE_REASON_FAILURE(0x50)"} = 1;
                            }
                        }
                    } else {
                        if ($power_failure_12v == 1 && $asic_pin_sts_0 eq "0x00" && $asic_pin_sts_1 eq "0x00" && $asic_pin_sts_2 eq "0x00") {
                            $diag_fa_code{"NIC_POWER_FAILURE_12V_NOT_UP"} = 1;
                        }
                    }
                }
                $sts_dump_exist = 1;
            }
            if($line =~ m/ERROR/ && $line !~ m/smbus\.go/) {
                $test_err_msg .= $line;
            }
        }
        if ($ecc_result_err == 0) {
            if($line =~ m/=== Dumping ECC info ===/ || $line =~ m/ECC intr/) {
                $ecc_start_linenum = $.;
            }
            if($line =~ m/=== Collect ECC info ===/) {
                $ecc_disp_start = 1;
                $ecc_j2c_error_current = 0;
            }
            #if ($old_ecc_dump_exist == 0) {
                if($line =~ m/j2c : read req error.*addr: 0x305305e4/) {
                    $j2c_error_linenum = $.;
                    print "j2c_error_linenum: $j2c_error_linenum\n";
                }
                if($line =~ m/(.*)(Reg 0x305305e4; value:)\s(\w+)/) {
                    $ecc_reg_linenum = $.;
                    print "ecc_reg_linenum: $ecc_reg_linenum\n";
                    if ($3 eq "0xffffffff") {
                        if ($ecc_reg_linenum - $j2c_error_linenum == 3) {
                            $ecc_j2c_error_current = 1;
                        }
                    } elsif ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x305305e4, value: $3\n";
                        $num_ecc_sts_errors++;
                    } elsif ($ecc_reg_linenum - $j2c_error_linenum == 2) {
                        $ecc_j2c_error_current = 1;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x30530454; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530454, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x30530458; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530458, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x30530464; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530464, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x30530468; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530468, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x3053046c; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x3053046c, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line =~ m/(.*)(Reg 0x30530470; value:)\s(\w+)/)) {
                    if ($3 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530470, value: $3\n";
                        $num_ecc_sts_errors++;
                    }
                    $old_ecc_dump_exist = 1;
                }
            #}

            #if ($new_ecc_dump_exist == 0) {
                if($line =~ m/j2c : read req error.*addr: 0x305305e4/) {
                    $j2c_error_linenum = $.;
                    print "j2c_error_linenum: $j2c_error_linenum\n";
                }
                if($line !~ m/P000/ && $line =~ m/Reg 0x305305e4:\s+(\w+)/) {
                    $ecc_reg_linenum = $.;
                    print "ecc_reg_linenum: $ecc_reg_linenum\n";
                    if ($1 eq "0xffffffff") {
                        if ($ecc_reg_linenum - $j2c_error_linenum == 3) {
                            $ecc_j2c_error_current = 1;
                        }
                    } elsif ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x305305e4, value: $1\n";
                        $num_ecc_sts_errors++;
                    } elsif ($ecc_reg_linenum - $j2c_error_linenum == 2) {
                        $ecc_j2c_error_current = 1;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x30530454:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530454, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x30530458:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530458, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x30530464:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530464, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x30530468:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530468, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x3053046c:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x3053046c, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                }
                if(($ecc_j2c_error_current == 0) && ($line !~ m/P000/ && $line =~ m/Reg 0x30530470:\s+(\w+)/)) {
                    if ($1 ne "0x00000000") {
                        $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530470, value: $1\n";
                        $num_ecc_sts_errors++;
                    }
                    $new_ecc_dump_exist = 1;
                }
            #}

            if ($ecc_j2c_error_current == 0) {
                if ($line =~ m/MSG :: (MC\d: CORE\d: read syndrome).*/) {
                    $mc_info .= $1."\r\n";
                }
                #if ($ecc_result_err == 0) {
                    if($line =~ m/(Correctable ECC Syndrome:.*Incorrect Bit:.*)/) {
                        if ($mc_info ne "") {
                            $ecc_sts .= $mc_info;
                            $mc_info = "";
                        }
                        $ecc_sts = $ecc_sts.$1."\r\n";
                        $num_ecc_sts_errors++;
                        #$corr_syn = 1;
                    }
                #}
                #if ($ecc_result_err == 0) {
                    if($line =~ m/(Multi-bit Correctable ECC Syndrome:.*)/) {
                        if ($mc_info ne "") {
                            $ecc_sts .= $mc_info;
                            $mc_info = "";
                        }
                        $ecc_sts = $ecc_sts.$1."\r\n";
                        $num_ecc_sts_errors++;
                        #$multi_corr_syn = 1;
                    }
                #}
                #if ($ecc_result_err == 0) {
                    if($line =~ m/(UnCorrectable ECC Syndrome:.*Incorrect Bit:.*)/) {
                        if ($mc_info ne "") {
                            $ecc_sts .= $mc_info;
                            $mc_info = "";
                        }
                        $ecc_sts = $ecc_sts.$1."\r\n";
                        $num_ecc_sts_errors++;
                        #$uncorr_syn = 1;
                    }
                #}
                #if ($ecc_result_err == 0) {
                    if($line =~ m/(Multi-bit Uncorrectable ECC Syndrome:.*)/) {
                        if ($mc_info ne "") {
                            $ecc_sts .= $mc_info;
                            $mc_info = "";
                        }
                        $ecc_sts = $ecc_sts.$1."\r\n";
                        $num_ecc_sts_errors++;
                        #$multi_uncorr_syn = 1;
                    }
                #}
                #if(($ecc_result_err == 0) && ($line =~ m/FAIL: ECC_EN:/)) {
                if($line =~ m/FAIL: ECC_EN:/) {
                    $ecc_result_linenum = $.;
                    if ($ecc_result_linenum - $ecc_start_linenum < 300) {
                        $ecc_result_exist_current = 1;
                        $ecc_result_err_current = 1;
                        print $ecc_sts;
                        $ecc_sts = $ecc_sts.$line;
                    }
                }
                if($line =~ m/MSG :: ECC_EN:0x\d+ ECC_INTERRUPT:0x0 ECC_INTERRUPT_COUNTER:0x0/) {
                    $ecc_result_linenum = $.;
                    if ($ecc_result_linenum - $ecc_start_linenum < 300) {
                        $ecc_result_exist_current = 1;
                        $ecc_result_err_current = 0;
                    }
                }
            }

            if($line =~ m/ECC COLLECTION DONE/ || $line =~ m/ARM status/) {
                $ecc_disp_start = 0;
                if (($j2c_error_linenum != 0) && ($ecc_reg_linenum == 0)) {
                    $ecc_j2c_error_current = 1;
                }
                $ecc_j2c_error |= $ecc_j2c_error_current;
                $ecc_result_exist |= $ecc_result_exist_current;
                $ecc_result_err |= $ecc_result_err_current;
            }
        }

        if($line =~ m/MC.*(elb_mc_phy_int_status|elb_mc_controller_int_status)/) {
            $mc_int_status = $line;
        }
        if($line =~ m/(PARITY|PARITY_ERR)=1/) {
            $ecc_sts = $ecc_sts.$mc_int_status.$line;
        }
        if($line =~ m/S2I Operation timed out/) {
            if ($ecc_disp_start) {
                #$diag_fa_code{"Bad_J2C_ECC"} = 1;
                $ecc_j2c_s2i_timeout = 1;
            } else {
                $diag_fa_code{"Bad_J2C"} = 1;
            }
        }
        if($line =~ m/ERROR:i2c_read_count: 1001/) {
            #print "$line";
            $diag_fa_code{"Bad_I2C"} = 1;
        }
        if($line =~ m/fwupdate -p .*-C-92_/) {
            $c92_upgrade = 1;
        }
    }
    close(TR3);
    # When ECC error is not detected, check if there's J2C error when dumping ECC
    if (($num_ecc_sts_errors == 0) && ($ecc_result_err == 0)) {
        if (($ecc_j2c_s2i_timeout == 1) || ($ecc_j2c_error == 1)) {
            $ecc_not_valid = 1;
        }
    }
    if ($ecc_not_valid == 1) {
        $diag_fa_code{"Bad_J2C_ECC"} = 1;
        print "ECC not valid due to bad J2C\n";
        $fa_row[$curr_row]{"ECC Reg"} = "ECC not valid due to bad J2C";
    } elsif (($old_ecc_dump_exist == 0) && ($new_ecc_dump_exist == 0) && ($ecc_result_exist == 0)) {
        print "ECC not dumped\n";
        $fa_row[$curr_row]{"ECC Reg"} = "ECC not dumped";
        my $retest_ts = "2021-11-23_00-00-00";
        my $unixts = convert_ts($ts);
        my $unixts_retest = convert_ts($retest_ts);
        if ($unixts < $unixts_retest) {
            $diag_fa_code{"RETEST_NEEDED"} = 1;
        }
        if (exists $diag_fa_code{"SNAKE_LOGFILE_NOT_EXIST"} ||
            exists $diag_fa_code{"NO_ERR_IN_SNAKE_LOG"} ||
            exists $diag_fa_code{"SNAKE_LOG_EMPTY"} ||
            exists $diag_fa_code{"SNAKE_LOG_INCOMPLETE"}) {
            $diag_fa_code{"RETEST_NEEDED"} = 1;
        }
    } elsif (($num_ecc_sts_errors == 0) && ($ecc_result_err == 0)) {
        print "ECC status OK\n";
        $fa_row[$curr_row]{"ECC Reg"} = "ECC status OK";
    } else {
        chomp($ecc_sts);
        $fa_row[$curr_row]{"ECC Reg"} = $ecc_sts;
        if ($c92_upgrade == 1) {
            $diag_fa_code{"DDR_ECC_FAILURE_AFTER_C92_UPGRADED"} = 1;
        } else {
            $diag_fa_code{"DDR_ECC_FAILURE"} = 1;
        }
    }

    if ($sts_dump_exist == 0) {
        print "CPLD registers not dumped\n";
        $fa_row[$curr_row]{"CPLD Reg"} = "CPLD registers not dumped";
    } elsif ($smbus_err == 0) {
        if ($num_cpld_sts_errors == 0) {
            print "CPLD registers status OK\n";
            $fa_row[$curr_row]{"CPLD Reg"} = "CPLD registers status OK";
        } else {
            chomp($cpld_sts);
            $fa_row[$curr_row]{"CPLD Reg"} = $cpld_sts;
        }
    } else {
        $fa_row[$curr_row]{"CPLD Reg"} = "Failed to dump CPLD registers status";
    }
}

sub parse_mtp_diag_file {
    my ($mtpdiagfile) = @_;
    my $mfr_id_linenum = 0;
    my $failed_psu1_linenum = 0;
    my $failed_psu2_linenum = 0;

    if (!open(TR3, '<', $mtpdiagfile)) {
        print "Cannot open file $mtpdiagfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($line =~ m/MFR_ID: FSP GROUP/) {
            $mfr_id_linenum = $.;
        }
        if ($line =~ m/Failed to retrieve status: PSU_1/) {
            $failed_psu1_linenum = $.;
            if ($failed_psu1_linenum - $mfr_id_linenum < 20) {
                $diag_fa_code{"PSU1_NOT_INSTALLED"} = 1;
            }
        }
        if ($line =~ m/Failed to retrieve status: PSU_2/) {
            $failed_psu2_linenum = $.;
            if ($failed_psu2_linenum - $mfr_id_linenum < 20) {
                $diag_fa_code{"PSU2_NOT_INSTALLED"} = 1;
            }
        }
        if ($line =~ m/PSU_1               -.-       -.-       -.-       -.-       -.-       -.-/) {
            $failed_psu1_linenum = $.;
            if ($failed_psu1_linenum - $mfr_id_linenum < 10) {
                $diag_fa_code{"PSU1_CORD_NOT_CONNECTED"} = 1;
            }
        }
        if ($line =~ m/PSU_2               -.-       -.-       -.-       -.-       -.-       -.-/) {
            $failed_psu2_linenum = $.;
            if ($failed_psu2_linenum - $mfr_id_linenum < 10) {
                $diag_fa_code{"PSU2_CORD_NOT_CONNECTED"} = 1;
            }
        }
    }
    close(TR3);
}
