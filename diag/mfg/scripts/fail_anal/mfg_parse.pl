#!/usr/bin/perl
use strict;
use warnings;
use lib "/home/mfg/mfg_diag_fa/scripts/Archive-Zip-1.68/lib";
use lib "/home/mfg/mfg_diag_fa/scripts/Excel-Writer-XLSX-1.09/lib";
use Time::Local;
use Cwd;
use File::Find;
use Excel::Writer::XLSX;

my $fa_opt = shift;
my $result_file = shift;
my $failure_txt_path = shift;
my $test_name_opt = shift;
my $mfg_err_code_opt = shift;

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
my $file_logs_all = $failure_txt_path."/testresult.txt";
my $failure_logs = $failure_txt_path."/logs_fail.txt";
my $pass_logs = $failure_txt_path."/logs_pass.txt";
my $log_path = cwd();

my $curr_sn = "";
my $curr_unixts = 0;
my $lastline = "";
my $debug_msgs = 0;
my $worksheet_name = "";

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
        if($line =~ m/\.\/([\w-]+)\/(\w+)\/([0-9A-Z-]+)_MTP-([0-9]+)_(.*)\/mtp_test.log(.*)(\]:\s)(NIC-\d+)(\s\w+\s)(\w+)(\s)NIC_DIAG_REGRESSION_TEST_FAIL/)
        {
            my $toppath=$1;
            my $sn=$2;
            my $stage=$3;
            my $mtp=$4;
            my $ts=$5;
            my $slot=$8;
            my $sn2=$10;

            if ($debug_msgs) {
                print "toppath:  $toppath\n";
                print "folder sn:  $sn\n";
                print "card  sn2:  $sn2\n";
                print "stage:      $stage\n";
                print "ts:         $ts\n";
            }

            if ($sn eq $sn2)
            {
                if ($curr_sn eq "")
                {
                    $curr_sn = $sn2;
                    if ($debug_msgs) { print "first new SN: $curr_sn\n"};
                }

                my $unixts = convert_ts($ts);

                if ($fa_opt ne "ALL") {
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
    if ($fa_opt ne "ALL") {
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
    $worksheet_name = "Last failures";
    $curr_unixts = 0;
    count_num_of_failures($fa_opt);
} elsif($fa_opt eq "FIRST") {
    $worksheet_name = "First failures";
    $curr_unixts = time();
    count_num_of_failures($fa_opt);
} elsif($fa_opt eq "ALL") {
    $worksheet_name = "All failures";
    count_num_of_failures($fa_opt);
} else {
    print "unexpected fa_opt $fa_opt\n";
    exit(1);
}

my $workbook = Excel::Writer::XLSX->new($result_file);

my $worksheet = $workbook->add_worksheet($worksheet_name);
my $format = $workbook->add_format(text_wrap => 1);
my @colDefs = (
    {
        header => 'SN',
        header_format => $format,
    },
    {
        header => 'Stage',
        header_format => $format,
    },
    {
        header => 'Date',
        header_format => $format,
    },
    {
        header => 'MTP',
        header_format => $format,
    },
    {
        header => 'Slot',
        header_format => $format,
    },
    {
        header => 'Test',
        header_format => $format,
    },
    {
        header => 'MFG Error Code',
        header_format => $format,
    },
    {
        header => 'Diag FA Code',
        header_format => $format,
    },
    {
        header => 'CPLD Reg',
        header_format => $format,
    },
    {
        header => 'ECC Reg',
        header_format => $format,
    },
    {
        header => 'Err Msg',
        header_format => $format,
    },
    {
        header => 'Detailed Diag FA Code',
        header_format => $format,
    },
);
 
$worksheet->add_table(0, 0, $num_failures, 11, { columns     => \@colDefs,  } );

open(TR2, '<', $failure_logs) or die $!;
my $curr_row = 1;
my $sn_col = 0;
my $stage_col = 1;
my $date_col = 2;
my $mtp_col = 3;
my $slot_col = 4;
my $test_name_col = 5;
my $failure_code_col = 6;
my $top_diag_fa_col = 7;
my $cpld_sts_col = 8;
my $ecc_sts_col = 9;
my $err_msg_col = 10;
my $full_diag_fa_col = 11;

my $default_fmt = $workbook->add_format();
$default_fmt->set_align("top");
$default_fmt->set_align("left");
$default_fmt->set_text_wrap();
$worksheet->set_column($sn_col, $sn_col, 14, $default_fmt);
$worksheet->set_column($stage_col, $stage_col, undef, $default_fmt);
$worksheet->set_column($date_col, $date_col, 20, $default_fmt);
$worksheet->set_column($mtp_col, $mtp_col, undef, $default_fmt);
$worksheet->set_column($slot_col, $slot_col, 6, $default_fmt);
$worksheet->set_column($test_name_col, $test_name_col, 15, $default_fmt);
$worksheet->set_column($failure_code_col, $failure_code_col, 22, $default_fmt);
$worksheet->set_column($top_diag_fa_col, $top_diag_fa_col, 32, $default_fmt);
$worksheet->set_column($cpld_sts_col, $cpld_sts_col, 55, $default_fmt);
$worksheet->set_column($ecc_sts_col, $ecc_sts_col, 48, $default_fmt);
$worksheet->set_column($err_msg_col, $err_msg_col, 60, $default_fmt);
$worksheet->set_column($full_diag_fa_col, $full_diag_fa_col, 32, $default_fmt);

my %diag_fa_code;
my $top_diag_fa_code = "";
my $all_test_msg = "";
my $all_l1_fails = "";
while(my $line = <TR2>)
{
    if($line =~ m/\.\/([\w-]+)\/(\w+)\/([0-9A-Z-]+)_(MTP-[0-9]+)_(.*)\/mtp_test.log(.*)(\]:\s)NIC-(\d+)(\s\w+\s)(\w+)(\s)NIC_DIAG_REGRESSION_TEST_FAIL/)
    {
        my $toppath=$1;
        my $sn=$2;
        my $stage=$3;
        my $mtp=$4;
        my $ts=$5;
        my $slot=$8;
        my $sn2=$10;

        if ($debug_msgs) { print "\nThe SN we are looking at: $sn2, line: $line\n" };
        my $fulllogpath=$log_path."/".$toppath."/".$sn2."/".$3."_".$mtp."_".$5;
        my $summaryfile=$toppath."/".$sn2."/".$3."_".$mtp."_".$5."/"."mtp_test.log";
        my $slotlogfile=$toppath."/".$sn2."/".$3."_".$mtp."_".$5."/"."mtp_NIC-".$slot."_diag.log";


        if ($debug_msgs) { print "summaryfile: $summaryfile\n" };
        if ($debug_msgs) { print "slotlogfile: $slotlogfile\n" };
        print "########################## $curr_row ###############################\n";
        printf "%-30s %-20s %-20s\n", "Failed sn: ".$sn2, "mtp: ".$mtp, "slot: ".$slot;
        $worksheet->write($curr_row, $sn_col, $sn2);
        $worksheet->write($curr_row, $stage_col, $toppath);
        $worksheet->write($curr_row, $date_col, $ts);
        $worksheet->write($curr_row, $mtp_col, $mtp);
        $worksheet->write($curr_row, $slot_col, $slot);
        %diag_fa_code = ();
        $all_test_msg = "";
        my $l1_failed = find_failure_code($fulllogpath, $sn2, $toppath, $stage, $ts);
        parse_fpga_and_ecc($slotlogfile, $sn2, $ts, $l1_failed);

        my $diag_fa_code_str = "";
        foreach my $diag_fa_code (keys %diag_fa_code) {
            $diag_fa_code_str .= $diag_fa_code."\n";
        }
        if ($diag_fa_code_str ne "") {
            chomp($diag_fa_code_str);
            $worksheet->write($curr_row, $full_diag_fa_col, $diag_fa_code_str);
        }

        pick_top_diag_fa();
        $worksheet->write($curr_row, $top_diag_fa_col, $top_diag_fa_code);
        $worksheet->write($curr_row, $err_msg_col, $all_test_msg);
        $curr_row++;
    }
}
close(TR2);

sub pick_top_diag_fa {
    if (%diag_fa_code == 0) {
        $top_diag_fa_code = "UNKNOWN";
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

    if (exists $diag_fa_code{"L1_DDR_BIST"}) {
        $top_diag_fa_code = "L1_DDR_BIST";
        delete $diag_fa_code{"L1_DDR_BIST"};
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
        }
    }

    if (exists $diag_fa_code{"LV_EDMA_FAILURE"}) {
        $top_diag_fa_code = "LV_EDMA_FAILURE";
        delete $diag_fa_code{"LV_EDMA_FAILURE"};
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

    if (exists $diag_fa_code{"SNAKE_ECC_FAILURE"}) {
        $top_diag_fa_code = "SNAKE_ECC_FAILURE";
        delete $diag_fa_code{"SNAKE_ECC_FAILURE"};
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

    if (exists $diag_fa_code{"L1_CORE_DUMPED"}) {
        $top_diag_fa_code = "L1_CORE_DUMPED";
        delete $diag_fa_code{"L1_CORE_DUMPED"};
        return;
    }

    if (exists $diag_fa_code{"SNAKE_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "SNAKE_LOG_INCOMPLETE";
        delete $diag_fa_code{"SNAKE_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"L1_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "L1_LOG_INCOMPLETE";
        delete $diag_fa_code{"L1_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"NIC_LOG_INCOMPLETE"}) {
        $top_diag_fa_code = "NIC_LOG_INCOMPLETE";
        delete $diag_fa_code{"NIC_LOG_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"NIC_TXT_INCOMPLETE"}) {
        $top_diag_fa_code = "NIC_TXT_INCOMPLETE";
        delete $diag_fa_code{"NIC_TXT_INCOMPLETE"};
        return;
    }
    if (exists $diag_fa_code{"Bad_J2C"}) {
        $top_diag_fa_code = "Bad_J2C";
        delete $diag_fa_code{"Bad_J2C"};
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
            $diag_fa_code{"SNAKE_PCIe_LINKUP"} = 1;
            $err_found = 1;
        }
        if ($err_found == 0 && $line =~ m/ERROR :: elb(.*)(_ecc|_mc)(.*)interrupt/) {
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
            $diag_fa_code{"SNAKE_ECC_FAILURE"} = 1;
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
    $all_test_msg .= "############### $test_and_failure_code ###############\n"."log file: ".$log_path."/".$logfile."\n\n";
    if ($test_err_msg ne "") {
        $all_test_msg .= $test_err_msg;
    } else {
        $diag_fa_code{"NO_ERR_IN_SNAKE_LOG"} = 1;
    }
    if ($log_complete == 0) {
        $diag_fa_code{"SNAKE_LOG_INCOMPLETE"} = 1;
    }
    close(TR3);
}

sub parse_l1_log {
    my ($logfile, $sn, $test_and_failure_code) = @_;
    my $log_complete = 0;
    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"L1_LOGFILE_NOT_EXIST"} = 1;
        return;
    }
    my $test_err_msg = "";
    while(my $line = <TR3>)
    {
        if($line =~ m/#FAIL#\s+(\w+)\s+\d+:\d+/) {
            if ($1 eq "elb_l1_ddr_bist") {
                $diag_fa_code{"L1_DDR_BIST"} = 1;
            } else {
                $all_l1_fails .= "_".uc($1);
            }
            if ($debug_msgs) { print "line: $line"};
            $test_err_msg .= $line;
        }
        if($line =~ m/(.*)MSG ::\s+L1_SCREEN (PASSED|FAILED)/)
        {
            $log_complete = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."L1 log file: ".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
    if ($log_complete == 0) {
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
	    if ($txt_complete == 0) {
            $diag_fa_code{"NIC_TXT_INCOMPLETE"} = 1;
        }
    }
    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"NIC_LOGFILE_NOT_EXIST"} = 1;
    } else {
	    my $log_complete = 0;
        my $prev_line = "";
        while(my $line = <TR3>)
        {
            if($line =~ m/ERROR :: elb_aapl_prbs_check :: sbus_addr/) {
                $test_err_msg .= $prev_line;
                $test_err_msg .= $line;
            } elsif($line =~ m/ERROR/)
            {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
            }
            if(($line =~ m/\s+(\w+)\s+#FAILED#/) && ($testname eq "L1"))
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
	    if ($log_complete == 0) {
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

    if (!open(TR3, '<', $logfile)) {
        $diag_fa_code{"ETH_PRBS_LOGFILE_NOT_EXIST"} = 1;
    } else {
	    my $log_complete = 0;
        while(my $line = <TR3>)
        {
            if($line =~ m/ERROR/) {
                if ($debug_msgs) { print "line: $line"};
                $test_err_msg .= $line;
            }
            if($line =~ m/:: MX PRBS (PASSED|FAILED)/) {
                $log_complete = 1;
            }
        }
        close(TR3);
	    if ($log_complete == 0) {
            $diag_fa_code{"ETH_PRBS_LOG_INCOMPLETE"} = 1;
        }
    }
    #if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."eth_prbs log file: ".$log_path."/".$logfile."\n\n";
        $all_test_msg .= $test_err_msg;
    #}
}

sub find_failure_code {
    my ($fulllogpath, $sn, $toppath, $stage, $ts) = @_;
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

    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return 0;
    }
    while(my $line = <TR3>)
    {
        if($line =~ m/(.*)(ERR:\s\[)([\w-]+)(\]:\s\[NIC-)(\d+)(]:\s)(\w+)(\sDIAG\sTEST\s)(\w+)(\s)(\w+)(\s)(FAIL|FAILED|FAILURE|TIMEOUT)/)
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
    $worksheet->write($curr_row, $test_name_col, $all_test_names);
    $worksheet->write($curr_row, $failure_code_col, $all_failure_codes);
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
        } elsif ($asic_log_dir ne "" && $failure_code =~ "L1") {
            if (index($test_name, "NIC") == -1) {
                $asic_l1_failed = 1;
                my $l1_path = $log_path."/".$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir;
                my @l1_log_files = glob("${l1_path}elb_l1_screen_board_${sn}_*");
                if (@l1_log_files) {
                    my $l1_log_file= $l1_log_files[0];
                    print "#### l1_log_file: $l1_log_file\n";
                    parse_l1_log($l1_log_file, $sn, $test_and_failure_code, $all_l1_fails);
                } else {
                    $diag_fa_code{"L1_LOGFILE_NOT_EXIST"} = 1;
                }
            } else {
                my $nic_l1_txt_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."AAPL-NIC-".$slot."/log_NIC_ASIC.txt";
                my $nic_l1_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_arm_l1_test.log";
                print "#### NIC_l1_txt_file: $nic_l1_txt_file\n";
                print "#### NIC_l1_log_file: $nic_l1_log_file\n";
                parse_nic_test_logs("L1", $nic_l1_txt_file, $nic_l1_log_file, $sn, $test_and_failure_code);
            }
        } elsif ($asic_log_dir ne "" && $failure_code =~ "PCIE_PRBS") {
            my $pcie_prbs_txt_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_txt_dir."AAPL-NIC-".$slot."/log_NIC_ASIC.txt";
            my $pcie_prbs_log_file=$toppath."/".$sn."/".$stage."_".$mtp."_".$ts.$asic_log_dir.$sn."_elba_PRBS_PCIE.log";
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
        } else {
            if ($failure_code =~ "NIC_STATUS" || $failure_code =~ "CONSOLE_BOOT" || $failure_code =~ "NIC_MGMT_INIT" || $failure_code =~ "NIC_CPLD" || $failure_code =~ "NIC_DIAG_BOOT") {
                parse_mtp_and_slot_log($fulllogpath, $slot, $test_and_failure_code);
            }
        }
        if ($all_test_msg eq "") {
            $all_test_msg = "log path: ".$fulllogpath."\n";
        }
    }
    if ($all_l1_fails ne "L1_TST") {
        $diag_fa_code{$all_l1_fails} = 1;
    }
    return $asic_l1_failed;
}

sub parse_mtp_and_slot_log {
    my ($fulllogpath, $slot, $test_and_failure_code) = @_;
    my $slotlogfile=$fulllogpath."/"."mtp_NIC-".$slot."_diag.log";
    my $test_err_msg = "";

    if (!open(TR3, '<', $slotlogfile)) {
        print "Cannot open file $slotlogfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if($line =~ m/ERROR/ && $line !~ m/Unsupported device: CPLD_ADAP/) {
	        #if ($debug_msgs) { print "line: $line"};
	        # $test_err_msg .= $line;
	        # last;
        }
    }
    if ($test_err_msg ne "") {
        $all_test_msg .= "############### $test_and_failure_code ###############\n"."slot log: ".$log_path."/".$slotlogfile."\n\n";
        $all_test_msg .= $test_err_msg;
    }
    close(TR3);
}

sub parse_fpga_and_ecc {
    my ($logfile, $sn, $ts, $l1_failed) = @_;
    my $test_err_msg = "";
    print "#### parse_fpga_and_ecc logfile: $logfile, l1_failed: $l1_failed\n";

    my $sts_dump_exist = 0;
    my $old_ecc_dump_exist = 0;
    my $new_ecc_dump_exist = 0;
    my $corr_syn = 0;
    my $multi_corr_syn = 0;
    my $uncorr_syn = 0;
    my $multi_uncorr_syn = 0;
    my $cpld_sts = "";
    my $num_cpld_sts_errors = 0;
    my $ecc_sts = "";
    my $num_ecc_sts_errors = 0;
    my $smbus_err = 0;

    # open the log file once to handle the SMBus problem
    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return;
    }
    while(my $line1 = <TR3>)
    {
        if($line1 =~ m/(.*)(Addr: 0x21; Value:)\s(\w+)/) {
            my $line2 = <TR3>;
            if ($line2 =~ m/smbus\.go/) {
                $diag_fa_code{"SMBUS_ERR"} = 1;
                $smbus_err = 1;
                last;
            }
        }
    }
    close(TR3);

    # open the log file again to handle the SMBus problem
    if (!open(TR3, '<', $logfile)) {
        print "Cannot open file $logfile\n";
        return;
    }
    while(my $line = <TR3>)
    {
        if ($sts_dump_exist == 0) {
            if($line =~ m/(.*)(Addr: 0x21; Value:)\s(\w+)/) {

                if ($smbus_err == 0 && $3 ne "0x2d") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x21, expected: 0x2d, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"CON_REDIR_FAILURE(0x21)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x26; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && ((hex($3) | 0x20) != 0x27)) {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x26, expected: 0x27 or 0x07, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"ASIC_PIN_STATUS_0_FAILURE(0x26)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x27; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0xee") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x27, expected: 0xee, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"ASIC_PIN_STATUS_1_FAILURE(0x27)"} = 1;
                }
            }
            if($line =~ m/(.*)(Addr: 0x28; Value:)\s(\w+)/) {
                if ($smbus_err == 0 && $3 ne "0xdf") {
                    $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x28, expected: 0xdf, actual: $3\n";
                    $num_cpld_sts_errors++;
                    $diag_fa_code{"ASIC_PIN_STATUS_2_FAILURE(0x28)"} = 1;
                }
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
                if ($smbus_err == 0 && $3 ne "0x80") {
                    if (!($l1_failed && ($3 eq "0x81"))) { #expected
                        $cpld_sts = $cpld_sts."Unexpected CPLD STS: Addr 0x50, expected: 0x80, actual: $3\n";
                        $num_cpld_sts_errors++;
                        if (hex($3) & 0x8) {
                            $diag_fa_code{"TEMP_TRIP_FAILURE(0x50)"} = 1;
                        } elsif (hex($3) & 0x1) {
                            $diag_fa_code{"ELBA_SELF_POWER_CYCLE(0x50)"} = 1;
                        } else {
                            $diag_fa_code{"OTHER_POWER_CYCLE_REASON_FAILURE(0x50)"} = 1;
                        }
                    }
                }
                $sts_dump_exist = 1;
            }
            if($line =~ m/ERROR/) {
                $test_err_msg .= $line;
            }
        }
        if ($old_ecc_dump_exist == 0) {
            if($line =~ m/(.*)(Reg 0x305305e4; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x305305e4, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x30530454; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530454, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x30530458; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530458, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x30530464; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530464, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x30530468; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530468, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x3053046c; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x3053046c, value: $3\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line =~ m/(.*)(Reg 0x30530470; value:)\s(\w+)/) {
                if ($3 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530470, value: $3\n";
                    $num_ecc_sts_errors++;
                }
                $old_ecc_dump_exist = 1;
            }
        }
        if ($new_ecc_dump_exist == 0) {
            if($line !~ m/P000/ && $line =~ m/Reg 0x305305e4:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x305305e4, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x30530454:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530454, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x30530458:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530458, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x30530464:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530464, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x30530468:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530468, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x3053046c:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x3053046c, value: $1\n";
                    $num_ecc_sts_errors++;
                }
            }
            if($line !~ m/P000/ && $line =~ m/Reg 0x30530470:\s+(\w+)/) {
                if ($1 ne "0x00000000") {
                    $ecc_sts = $ecc_sts."Unexpected ECC: Reg 0x30530470, value: $1\n";
                    $num_ecc_sts_errors++;
                }
                $new_ecc_dump_exist = 1;
            }
        }

        if ($corr_syn == 0) {
            if($line =~ m/(Correctable ECC Syndrome:.*Incorrect Bit:.*)/) {
                $ecc_sts = $ecc_sts."$1\n";
                $num_ecc_sts_errors++;
                $corr_syn = 1;
            }
        }
        if ($multi_corr_syn == 0) {
            if($line =~ m/(Multi-bit Correctable ECC Syndrome:.*)/) {
                $ecc_sts = $ecc_sts."$1\n";
                $num_ecc_sts_errors++;
                $multi_corr_syn = 1;
            }
        }
        if ($uncorr_syn == 0) {
            if($line =~ m/(UnCorrectable ECC Syndrome:.*Incorrect Bit:.*)/) {
                $ecc_sts = $ecc_sts."$1\n";
                $num_ecc_sts_errors++;
                $uncorr_syn = 1;
            }
        }
        if ($multi_uncorr_syn == 0) {
            if($line =~ m/(Multi-bit Uncorrectable ECC Syndrome:.*)/) {
                $ecc_sts = $ecc_sts."$1\n";
                $num_ecc_sts_errors++;
                $multi_uncorr_syn = 1;
            }
        }

        if($line =~ m/S2I Operation timed out/) {
            print "$line";
            $diag_fa_code{"Bad_J2C"} = 1;
        }
        if($line =~ m/ERROR:i2c_read_count: 1001/) {
            print "$line";
            $diag_fa_code{"Bad_I2C"} = 1;
        }
    }
    close(TR3);

    if (($old_ecc_dump_exist == 0) && ($new_ecc_dump_exist == 0)) {
        print "ECC not dumped\n";
        $worksheet->write($curr_row, $ecc_sts_col, "ECC not dumped");
        my $retest_ts = "2021-11-23_00-00-00";
        my $unixts = convert_ts($ts);
        my $unixts_retest = convert_ts($retest_ts);
        if ($unixts < $unixts_retest) {
            $diag_fa_code{"RETEST_NEEDED"} = 1;
        }
        if (exists $diag_fa_code{"SNAKE_LOGFILE_NOT_EXIST"} ||
            exists $diag_fa_code{"NO_ERR_IN_SNAKE_LOG"} ||
            exists $diag_fa_code{"SNAKE_LOG_INCOMPLETE"}) {
            $diag_fa_code{"RETEST_NEEDED"} = 1;
        }
    } elsif ($num_ecc_sts_errors == 0) {
        print "ECC status OK\n";
        $worksheet->write($curr_row, $ecc_sts_col, "ECC status OK");
    } else {
        chomp($ecc_sts);
        $worksheet->write($curr_row, $ecc_sts_col, $ecc_sts);
        $diag_fa_code{"DDR_ECC_FAILURE"} = 1;
    }

    if ($sts_dump_exist == 0) {
        print "CPLD registers not dumped\n";
        $worksheet->write($curr_row, $cpld_sts_col, "CPLD registers not dumped");
    } elsif ($smbus_err == 0) {
        if ($num_cpld_sts_errors == 0) {
            print "CPLD registers status OK\n";
            $worksheet->write($curr_row, $cpld_sts_col, "CPLD registers status OK");
        } else {
            chomp($cpld_sts);
            $worksheet->write($curr_row, $cpld_sts_col, $cpld_sts);
        }
    } else {
        $worksheet->write($curr_row, $cpld_sts_col, "Failed to dump CPLD registers status");
    }
}