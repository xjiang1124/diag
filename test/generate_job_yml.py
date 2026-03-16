import sys, os
"""
 USAGE

 - ON A RELEASE BRANCH,

    cd test
    python3 generate_job_yml.py

    this will make sure 4C, ORT, RDT are part of PR tests.
    and that all stage bundles remain in root jobyml despite being skipped.


 - FOR MASTER BRANCH,

    cd test
    python3 generate_job_yml.py

    this will skip 4C, ORT, RDT, SRN, etc (default)


 - FOR ASIC TOT,

    cd test-asic
    python3 ../test/generate_job_yml.py
 
"""

DEFAULT = ["FST"]
DIAG_CHANGES = ["P2C"]
SCRIPT_CHANGES = ["P2C", "SWI", "FST"]
RELEASE_MODELING = ["ScanDL", "DL", "P2C", "4C", "ORT", "RDT", "SWI", "FST", "SRN"]

cwd = os.path.basename(os.getcwd())
if cwd == "test-asic":
    job_set = "asic"
else:
    job_set = "diag"

NICS_BY_STAGE = dict()

def write_headers(fh):
    fh.write("---\n")
    fh.write("version: 2.0\n")
    fh.write("\n")
    fh.write("queue_name: asic\n")
    fh.write("image:\n")
    fh.write("  bind_dir: \"/psdiag\"\n")
    fh.write("  work_dir: \"/psdiag\"\n")
    fh.write("\n")
    fh.write("host_mounts:\n")
    fh.write("  \"/hw\": \"/vol/hw\"\n")
    fh.write("\n")

    fh.write("logfiles:\n")
    fh.write(" - /psdiag/diag_detailed_log.tgz\n")
    fh.write("\n")

    fh.write("e2e-targets:\n")

def write_targets(fh, mtp_type, asic, hardware, nic_type, stage):
    fh.write("  {:s}:\n".format(nic_type))
    fh.write("    commands: [\"sh\", \"-c\", \"/psdiag/test/run_mfg_job.sh \
--nic-type {:s} \
--testbed /warmd.json \
--test-type precheckin \
--asic {:s} \
--testsuite /psdiag/test/spec/testsuites/{:s}.testsuite\"]\n".format(nic_type, asic, stage))
    fh.write("    owners: [\"email:nabeel@pensando.io\"]\n")
    fh.write("    area:\n")
    fh.write("    sub-area:\n")
    fh.write("    feature:\n")
    if stage == "4C":
        fh.write("    max-duration: 24h\n")
    fh.write("    build-dependencies:\n")
    if stage == "FST":
        pass
    elif job_set == "diag":
        fh.write("     - build-amd64-{:s}\n".format(asic))
        fh.write("     - build-arm64-{:s}\n".format(asic))
    elif job_set == "asic":
        fh.write("     - build-amd64-{:s}-tot\n".format(asic))
        fh.write("     - build-arm64-{:s}-tot\n".format(asic))
    fh.write("     - package-{:s}-mfg-script\n".format(asic))
    fh.write("     - package-fw-assets\n")
    fh.write("    deployment:\n")
    fh.write("      skip-pxe-install: true\n")
    fh.write("    resources:\n")
    fh.write("     - generic:\n")
    fh.write("       - type: MTP\n")
    fh.write("         vendor: Pensando\n")
    fh.write("         count: 1\n")
    fh.write("         props:\n")
    if stage == "FST":
        fh.write("         - name: mtp-type\n")
        fh.write("           value: supermicro\n")
    else:
        fh.write("         - name: mtp-nic-processor\n")
        fh.write("           value: {:s}\n".format(mtp_type))
    fh.write("         - name: {:s}\n".format(hardware))
    fh.write("           value: yes\n")
    fh.write("    provision:\n")
    fh.write("      username: diag\n")
    fh.write("      password: lab123\n")
    fh.write("      vars:\n")
    fh.write("        BmOs: linux\n")
    fh.write("\n")

def write_stage_jobyml():
    # re-orient jobs.cfg to key by stage instead of nic_type
    def add_stage(key, nic_type, nic_detail):
        if key not in NICS_BY_STAGE:
            NICS_BY_STAGE[key] = dict()
        NICS_BY_STAGE[key][nic_type] = nic_detail

    with open("jobs.cfg", "r") as jobs_matrix:
        for line in jobs_matrix:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            *stages, mtp_type, asic, hardware, nic_type = line.split("\t")

            for stage in stages:
                if not stage: continue # skip empty
                add_stage(stage, nic_type, (mtp_type, asic, hardware))

    # write the new .job.ymls for each stage
    for stage in NICS_BY_STAGE:
        os.system(f"rm -r {stage}")
        os.system(f"mkdir -p {stage}")
        with open(f"{stage}/.job.yml", "w") as fh:
            write_headers(fh)
            for nic_type, nic_detail in NICS_BY_STAGE[stage].items():
                write_targets(fh, nic_detail[0], nic_detail[1], nic_detail[2], nic_type, stage)

def update_root_job_yml():
    ### remove old lines
    if job_set == "diag":
        sections = [ "JOB LABELS", "TEST DIAG CHANGES", "TEST SCRIPT CHANGES" ]
    elif job_set == "asic":
        sections = [ "ASIC JOB LABELS" ]

    for section in sections:
        os.system("sed -i '/^### %s ###/,/^### END %s ###/{/^### %s ###/!{/^### END %s ###/!d}}' ../.job.yml" % (section, section, section, section))
        os.system("sync")

    import fileinput
    ### add a new line below the line in .job.yml "### xx{{NIC_TYPE}}"
    for rline in fileinput.FileInput("../.job.yml", inplace=True):
        if job_set == "diag":
            if "### JOB LABELS ###" in rline:
                for stage in NICS_BY_STAGE:
                    new_line  = f"  test/{stage}:\n"
                    new_line += f"    labels: [\"CI-DIAG-Model\", \"CI-DIAG-Release\", \"CI-DIAG-{stage}\"]\n"
                    rline += new_line
            if "### TEST DIAG CHANGES ###" in rline:
                d_stages = [s for s in NICS_BY_STAGE.keys() if s in DIAG_CHANGES]
                for stage in d_stages:
                    new_line  = f"    - reference: test/{stage}\n"
                    new_line += f"      exclude_dirs: [\"mfg\"]\n"
                    rline += new_line
            if "### TEST SCRIPT CHANGES ###" in rline:
                s_stages = [s for s in NICS_BY_STAGE.keys() if s in SCRIPT_CHANGES]
                for stage in s_stages:
                    new_line  = f"    - reference: test/{stage}\n"
                    new_line += f"      exclude_dirs: [\"scripts\"]\n"
                    rline += new_line
        elif job_set == "asic":
            if "### ASIC JOB LABELS ###" in rline:
                for stage in NICS_BY_STAGE:
                    new_line  = f"  test-asic/{stage}:\n"
                    new_line += f"    labels: [\"CI-ASIC-TOT\", \"CI-ASIC-TOT-{stage}\"]\n"
                    rline += new_line
        print(rline, end="")


write_stage_jobyml()
update_root_job_yml()
