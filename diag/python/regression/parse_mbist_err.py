#!/usr/bin/python3

import sys
import argparse
import re

DIAG_MBIST = "Diagnostics MBIST"
MBIST = "Smart MBIST"
ALGO22 = "Algo22 MBIST"

def extract_between_signatures(content, start_sig, end_sig, overlap=False, dbg=False):
    """
    Extract all text between beginning and ending signatures from a log file.

    Args:
        content: log file content
        start_sig: Beginning signature string
        end_sig: Ending signature string

    Returns:
        List of extracted text blocks
    """
    results = []
    start_idx = 0

    while True:
        # Find next occurrence of start signature
        start_pos = content.find(start_sig, start_idx)
        if start_pos == -1:
            break

        # Find corresponding end signature
        end_pos = content.find(end_sig, start_pos + len(start_sig))
        if end_pos == -1:
            break

        # Extract text between signatures
        extracted = content[start_pos + len(start_sig):end_pos]
        results.append(start_sig + " " + extracted.strip() + " " + end_sig)

        if not overlap:
            # Move past this block
            start_idx = end_pos + len(end_sig)
        else:
            # Search for substrings inside this block
            start_idx = start_pos + len(start_sig)

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Salina MBIST Failure Parsing", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("logfile", help="Log file name", type=str, default="")
    args = parser.parse_args()

    test_name_list = [
        (DIAG_MBIST,   'Running diagnostics...',   'running  '),
        (MBIST,        'running  mbist_with_diag', 'running  '),
        (ALGO22,       'running  mbist_algo22',    'running  '),
    ]

    with open(args.logfile, 'r') as f:
        content = f.read()
        failure_messages = set()

        for test_title, test_start, test_end in test_name_list:
            extracted_blocks = extract_between_signatures(
                content,
                start_sig=test_start,
                end_sig=test_end
            )

            # one logfile will have multiple MBIST tests. extract one MBIST test and parse one at a time.
            for block in extracted_blocks:
                if test_title == ALGO22:
                    # algo22 has different output signature
                    for mem in re.findall("Failed TDO check.* ([0-9:]+ +Top.*) =>", block):
                        failure_messages.add(mem)
                else:
                    # Error message only reports the failure bit first
                    # then need to search the output for the memory name corresponding to that failure bit
                    failure_cells = extract_between_signatures(block, "Failed TDO check", "MSG :: ///Expect:", overlap=True)
                    for i,f in enumerate(failure_cells,1):
                        m = re.search(":([0-9]+) tag", f)
                        if m:
                            failure_bit = m.group(1)
                            for msb, lsb in re.findall("[ \*/]*([0-9]+):([0-9]+) .*Top", f):
                                # the bit we need can be inside a range e.g. [MSB:LSB]
                                if lsb <= failure_bit <= msb:
                                    failure_messages.add(re.search(f"(//.*:{lsb} .*Top.*) =>", f).group(1))
                                    break

            if failure_messages:
                for f in failure_messages:
                    print(f)
                if test_title == MBIST:
                    print(f"Failed {MBIST} at above memories but passed {DIAG_MBIST}")
                else:
                    print(f"Failed {test_title} at above memories")
                break # dont check MBIST after DIAG_MBIST, it's gonna be repetitive..
