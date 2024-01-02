import sys, os

EXCLUDE_FROM_PRECHECKIN=["ScanDL", "4C", "ORT", "RDT", "SRN"]

cwd = os.path.basename(os.getcwd())
if cwd == "test-asic":
    job_set = "asic"
elif "DEV" in os.environ.keys():
    job_set = "diag"
else:
    job_set = "modeling"
    EXCLUDE_FROM_PRECHECKIN = ["ScanDL", "SRN"]

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

def write_targets(fh, asic, hardware, nic_type, stage):
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
        fh.write("           value: {:s}\n".format(asic))
    fh.write("         - name: {:s}\n".format(hardware))
    fh.write("           value: yes\n")
    fh.write("    provision:\n")
    fh.write("      username: diag\n")
    fh.write("      password: lab123\n")
    fh.write("      vars:\n")
    fh.write("        BmOs: linux\n")
    fh.write("\n")

def write_stage_headers(stage):
    job_yml_file = "{:s}/.job.yml".format(stage)
    try:
        with open(job_yml_file, "r") as fh:
            first_line = fh.readline()
            if first_line.strip() == "---":
                # headers already present
                # else, rewrite this file
                return
    except FileNotFoundError:
        # will write new file
        pass
    os.system(f"mkdir -p {stage}/")
    with open(job_yml_file, "w") as fh:
        write_headers(fh)

def test_bundle_by_stage():
    os.system("rm -r DL P2C 4C RDT ORT SRN SWI FST ScanDL")
    with open("jobs.cfg", "r") as jobs_matrix:
        for line in jobs_matrix:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            *stages, asic, hardware, nic_type = line.split("\t")

            for stage in stages:
                if not stage: # empty
                    continue
                write_stage_headers(stage)
                job_yml_file = "{:s}/.job.yml".format(stage)
                fh = open(job_yml_file, "a")
                fh.write("  {:s}:\n".format(nic_type))
                write_targets(fh, asic, hardware, nic_type, stage)
                fh.close()

def test_bundle_by_nic_type():
    with open("jobs.cfg", "r") as job_matrix:
        for line in job_matrix:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            *stages, asic, hardware, nic_type = line.split("\t")

            os.system(f"mkdir -p {nic_type}/")
            job_yml_file = f"{nic_type}/.job.yml"
            fh = open(job_yml_file, "w")
            write_headers(fh)
            for stage in stages:
                if not stage: # empty
                    continue
                if stage in EXCLUDE_FROM_PRECHECKIN:
                    continue
                fh.write("  {:s}:\n".format(stage))
                write_targets(fh, asic, hardware, nic_type, stage)
            fh.close()

def write_FST_test_bundle():
    # always keep FST test even if ortano-ti-orc is skipped
    # since infra tests depend on it
    os.system("rm -r FST")
    stage, asic, hardware, nic_type = "FST", "elba", "ortano-ti", "ortano-ti-orc"

    write_stage_headers(stage)
    job_yml_file = "{:s}/.job.yml".format(stage)
    fh = open(job_yml_file, "a")
    fh.write("  {:s}:\n".format(nic_type))
    write_targets(fh, asic, hardware, nic_type, stage)
    fh.close()

def update_root_job_yml():
    ### remove old lines
    if job_set == "diag" or job_set == "modeling":
        sections = [ "NIC_TYPE TEST BUNDLE", "NIC_TYPE DEPENDENCY" ]
    elif job_set == "asic":
        sections = [ "NIC_TYPE ASIC TEST BUNDLE" ]

    for section in sections:
        os.system("sed -i '/^### %s ###/,/^### END %s ###/{/^### %s ###/!{/^### END %s ###/!d}}' ../.job.yml" % (section, section, section, section))
        os.system("sync")

    import fileinput
    with open("jobs.cfg", "r") as job_matrix:
        for line in job_matrix:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            *stages, asic, hardware, nic_type = line.split("\t")

            ### add a new line below the line in .job.yml "### xx{{NIC_TYPE}}"
            for rline in fileinput.FileInput("../.job.yml", inplace=True):
                if job_set == "diag" or job_set == "modeling":
                    if "### NIC_TYPE TEST BUNDLE ###" in rline:
                        new_line  = f"  test/{nic_type}:\n"
                        new_line += f"    labels: [\"CI-DIAG-Model\", \"CI-DIAG-Build\", \"CI-DIAG-{nic_type}\"]\n"
                        rline += new_line
                    if "### NIC_TYPE DEPENDENCY ###" in rline:
                        new_line  = f"    - reference: test/{nic_type}\n"
                        new_line += f"      exclude_dirs: [\"scripts\"]\n"
                        rline += new_line
                elif job_set == "asic":
                    if "### NIC_TYPE ASIC TEST BUNDLE ###" in rline:
                        new_line  = f"  test-asic/{nic_type}:\n"
                        new_line += f"    labels: [\"CI-ASIC-TOT\", \"CI-ASIC-{nic_type}\"]\n"
                        rline += new_line
                print(rline, end="")
                
if job_set == "diag":
    test_bundle_by_nic_type()
    test_bundle_by_stage()
    update_root_job_yml()

elif job_set == "modeling":
    test_bundle_by_nic_type()
    update_root_job_yml()    

elif job_set == "asic":
    test_bundle_by_nic_type()
    update_root_job_yml()

write_FST_test_bundle()
