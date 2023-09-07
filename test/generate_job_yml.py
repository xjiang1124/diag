import sys, os

def write_headers(fh):
    fh.write("---\n")
    fh.write("version: 2.0\n")
    fh.write("\n")
    fh.write("queue_name: asic\n")
    fh.write("image:\n")
    fh.write("  bind_dir: \"/psdiag\"\n")
    fh.write("  work_dir: \"/psdiag\"\n")
    fh.write("\n")
    #fh.write("host_mounts:\n")
    #fh.write("  \"/hw\": \"/vol/hw\"\n")
    fh.write("\n")

    fh.write("logfiles:\n")
    fh.write(" - /psdiag/diag_detailed_log.tgz\n")
    fh.write("\n")

    fh.write("e2e-targets:\n")

def write_targets(fh, asic, hardware, nic_type, stage):
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
    fh.write("    build-dependencies:\n")
    fh.write("     - build-amd64-{:s}\n".format(asic))
    fh.write("     - build-arm64-{:s}\n".format(asic))
    fh.write("     - package-{:s}-mfg-script\n".format(asic))
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


def f1(stage):
    with open("jobs.cfg", "r") as fj:

        job_yml_file = "{:s}/.job.yml".format(stage)
        fh = open(job_yml_file, "w")
        write_headers(fh)

        for line in fj:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.startswith("#"):
                continue
            asic, hardware, nic_type, *fields = line.split("\t")
            write_targets(fh, asic, hardware, nic_type, stage)


f1(sys.argv[1])
