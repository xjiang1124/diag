#!/usr/bin/perl
use strict;
use warnings;
use Excel::Writer::XLSX;
use YAML::XS 'LoadFile';

my $fa_opt = shift;
my $result_file = shift;
my $missing_log_file = shift;
my $passing_log_file = shift;

my $yaml_file = "./temp.yaml";

my $worksheet_name = "";
my @missing;
my @passing;

if($fa_opt eq "LAST") {
    $worksheet_name = "Last failures";
} elsif($fa_opt eq "LAST_RUN") {
    $worksheet_name = "Last run";
} elsif($fa_opt eq "FIRST") {
    $worksheet_name = "First failures";
} elsif($fa_opt eq "FIRST_RUN") {
    $worksheet_name = "First run";
} elsif($fa_opt eq "ALL") {
    $worksheet_name = "All failures";
} elsif($fa_opt eq "ALL_RUN") {
    $worksheet_name = "All run";
} else {
    print "unexpected fa_opt $fa_opt\n";
    exit(1);
}

if (open(LOG, '<', $missing_log_file)) {
    chomp(@missing = <LOG>);
    close (LOG);
}
if (open(LOG, '<', $passing_log_file)) {
    chomp(@passing = <LOG>);
    close (LOG);
}

#open my $fh, '<', $yaml_file or die $!;
my @fa_array = LoadFile($yaml_file);

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
my $num_failures = scalar(@fa_array) + scalar(@missing) + scalar(@passing);
$worksheet->add_table(0, 0, $num_failures, 11, { columns     => \@colDefs,  } );

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

my $curr_row = 1;
foreach (@fa_array) {
    $worksheet->write($curr_row, $sn_col, $_->{"SN"});
    $worksheet->write($curr_row, $stage_col, $_->{"Stage"});
    $worksheet->write($curr_row, $date_col, $_->{"Date"});
    $worksheet->write($curr_row, $mtp_col, $_->{"MTP"});
    $worksheet->write($curr_row, $slot_col, $_->{"Slot"});
    $worksheet->write($curr_row, $top_diag_fa_col, $_->{"Diag FA Code"});
    $worksheet->write($curr_row, $err_msg_col, $_->{"Err Msg"});
    $worksheet->write($curr_row, $test_name_col, $_->{"Test"});
    $worksheet->write($curr_row, $failure_code_col, $_->{"MFG Error Code"});
    $worksheet->write($curr_row, $ecc_sts_col, $_->{"ECC Reg"});
    $worksheet->write($curr_row, $cpld_sts_col, $_->{"CPLD Reg"});
    $worksheet->write($curr_row, $full_diag_fa_col, $_->{"Detailed Diag FA Code"});
    $curr_row++;
}
foreach (@passing) {
    $worksheet->write($curr_row, $sn_col, $_);
    $worksheet->write($curr_row, $top_diag_fa_col, "NO_FAILURE_LOG");
    $curr_row++;
}
foreach (@missing) {
    $worksheet->write($curr_row, $sn_col, $_);
    $worksheet->write($curr_row, $top_diag_fa_col, "NO_LOG_FOUND");
    $curr_row++;
}