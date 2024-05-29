import re
import sys
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

import libmfg_utils

def similar_match(lines=[], pattern="", threshold=95):
    """
    this function will remove non-printable chars for evey line or given lines list.
    then trim the line with given pattern,
    then call the fuzzywuzzy process to pick the most smilar string,
    if the score great than the given threshold, return True, otherwiese return False
    """

    pattern = pattern.strip()
    choices = []
    pattern_start_word = pattern.split()[0]
    pattern_end_word = pattern.split()[-1]
    is_pattern_single_word = True if len(pattern.split()) == 1 else False

    # figure our the the expression start with pattern start word or end with pattern end word
    for line in lines:
        # remove non-printable ASCII characters
        line = re.sub(r"[\x00-\x1F]", "", line)
        # Trim with pattern
        if pattern_start_word in line:
            line = line[line.index(pattern_start_word):]
        if pattern_end_word in line:
            line = line[0: line.index(pattern_end_word)] + pattern_end_word

        choices.append(line)

    # call the fuzzywuzzy process to pick the most smilar string
    # if the passter is single character, extractOne wil always got score 0 with ffollowing message, so using fuzz.ratio here instead of extractOne
    # WARNING:root:Applied processor reduces input query to empty string, all comparisons will have score 0. [Query: '# ']
    # choice, score = process.extractOne(pattern, choices)
    libmfg_utils.cli_inf("Try to match pattern {:s} in choices {:s}".format(str(pattern), str(choices)))
    h_score = 0
    h_choice = ""
    for choice in choices:
        if is_pattern_single_word:
            h_score_sub = 0
            h_sub_choice = ""
            for sub_choice in choice.split():
                sub_score = fuzz.ratio(sub_choice, pattern)
                # libmfg_utils.cli_inf("sub_choice word {:s} got score {:s}".format(str(sub_choice), str(sub_score)))
                if sub_score > h_score_sub:
                    h_score_sub =sub_score
                    h_sub_choice = sub_choice
            score = h_score_sub
            libmfg_utils.cli_inf("Choice {:s} got score {:s} by the highest score word {:s} with score {:s}".format(str(choice), str(score), str(h_sub_choice), str(h_score_sub)))
        else:
            score = fuzz.ratio(choice, pattern)
            libmfg_utils.cli_inf("Choice {:s} got score {:s}".format(str(choice), str(score)))

        if score > h_score:
            h_score =score
            h_choice = choice

    if h_score < threshold:
        return (h_choice, h_score, False)

    return (h_choice, h_score, True)

def similar_matches(message="", patterns_thresholds=[], default_threshold=95):
    """
    do the sumilar match over multiple pattern_thresholds pairs, if thresholds not specified in the pairs, using the default.
    the patterns_thresholds can be
    if any pattern meet the threshold, return the highest core patterns index
    """

    passed_pattern_list = list()
    lines = message.split("\n")

    for index, pattern_threshold in enumerate(patterns_thresholds):
        if isinstance(pattern_threshold, (list, tuple)):
            if len(pattern_threshold) == 1:
                pattern = pattern_threshold[0]
                threshold = default_threshold
            elif len(pattern_threshold) ==2:
                pattern = pattern_threshold[0]
                threshold = pattern_threshold[1]
            else:
                return None
        else:
            pattern = pattern_threshold
            threshold = default_threshold

        match_str, score, result = similar_match(lines, pattern, threshold)

        if result:
            libmfg_utils.cli_inf("Found the most Similar String: \n==>'{:s}' For Pattern \n==>'{:s}'\n==> Meet the score {:s} with acture score {:s}".format(match_str, pattern, str(threshold), str(score)))
            passed_pattern_list.append((index, score))

    if not passed_pattern_list:
        return None

    hightest_score = passed_pattern_list[0]
    for i, c in  passed_pattern_list:
        if c > hightest_score[1]:
            hightest_score = (i, c)

    return hightest_score

def unit_test():
    msg = """
        [2023-12-21_14:43] root# date -s 2023.12.21-14:43:29^M
        Thu Dec 21 14:43:29 UTC 2023^M
        [2023-12^@-21_14:43] root ^M
        Terminating...^M
        Thanks for usin picocom^M
        [2023-12-21_14:58:30] diag@NIC-08:$ killall -9 picocom^
        picocom: no process found^M
        """

    # lines = msg.split("\n")
    # target_pattern = "Thanks for using picocom"
    # target_threshold = 95
    # match_str, score, result = similar_match(lines, target_pattern, target_threshold)

    # if not result:
    #     if len(target_pattern) == 1:
    #         print(match_str)
    #     else:
    #         print("Found the most Similar String: \n==>'{:s}' For Pattern \n==>'{:s}'\n==> NOT meet the score threshold {:d} with acture score {:d}".format(match_str, target_pattern, target_threshold, score))
    #     return False
    # print("Found the most Similar String: \n==>'{:s}' For Pattern \n==>'{:s}'\n==> Meet the score threshold {:d} with acture score {:d}".format(match_str, target_pattern, target_threshold, score))
    # return True

    target_pattern_thresholds = ["Thanks for using picocom"]
    msg = "root "
    target_pattern_thresholds = ["#roof"]
    rc = similar_matches(msg, target_pattern_thresholds)
    if rc is None:
        return False
    print(rc)
    return True

if __name__ == '__main__':
    sys.exit(not unit_test())