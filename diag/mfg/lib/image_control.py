from libmfg_cfg import *
from libdefs import FF_Stage

cpld = "CPLD"
sec_cpld = "Secure CPLD"
fail_cpld = "Failsafe CPLD"
fea_cpld = "CPLD Feature Row"
ufm1 = "UFM1"
fpga = "FPGA"
test_fpga = "Test FPGA"
timer1 = "FPGA timer1"
timer2 = "FPGA timer2"
diagfw = "DiagFW"
goldfw = "GoldFW"
mainfw = "MainFW"
uboot = "uboot"
uboota = "uboota"
ubootb = "ubootb"
cert = "certificate"
arm_a_boot0 = "arm_a_boot0"
arm_a_uboota = "arm_a_uboota"
arm_a_ubootb = "arm_a_ubootb"
arm_a_ubootg = "arm_a_ubootg"
arm_n_boot0 = "arm_n_boot0"
arm_n_uboota = "arm_n_uboota"
arm_n_ubootb = "arm_n_ubootb"
arm_n_ubootg = "arm_n_ubootg"
arm_n_kernel_goldfw = "arm_n_kernel_goldfw"
qspi_prog_sh_img = "qspi_prog_sh_img"
qspi_snake_img = "qspi_snake_img"
arm_a_zephyr = "arm_a_zephyr"
arm_a_zephyr_gold = "arm_a_zephyr_gold"
arm_a_zephyr_a = "arm_a_zephyr_a"
arm_a_zephyr_b = "arm_a_zephyr_b"
fwsel = "fwsel"
device_config_dtb = "device_config_dtb"
firmware_config_dtb = "firmware_config_dtb"
mbist_boot0_img = "mbist_boot0_img"

def get_dict_entry(mtp_mgmt_ctrl, img_dict, nic_type):
    try:
        return img_dict[nic_type]
    except Exception:
        return ""

def get_cpld(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_dat, nic_type)
    }

def get_sec_cpld(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, sec_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_dat, nic_type)
    }

def get_fail_cpld(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, fail_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_dat, nic_type)
    }

def get_fea_cpld(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, fea_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fea_cpld_img, nic_type)
    }

def get_ufm1(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.ufm1_img, nic_type)
    }

def get_timer1(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, timer1)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.timer1_img, nic_type)
    }

def get_timer2(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, timer2)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.timer2_img, nic_type)
    }

def get_test_fpga(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, test_fpga)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_dat, nic_type)
    }

def get_diagfw(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, diagfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.diagfw_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.diagfw_dat, nic_type)
    }

def get_goldfw(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, goldfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.goldfw_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.goldfw_dat, nic_type)
    }

def get_mainfw(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, mainfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.mainfw_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.mainfw_dat, nic_type)
    }

def get_uboot(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, uboot)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboot_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboot_dat, nic_type)
    }

def get_uboota(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, uboota)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboota_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboota_dat, nic_type)
    }

def get_ubootb(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, ubootb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.ubootb_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.ubootb_dat, nic_type)
    }

def get_cert(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, cert)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cert_img, nic_type)
    }

def get_arm_a_boot0_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_boot0)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_boot0_img, nic_type)
    }

def get_arm_a_uboota_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_uboota)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_uboota_img, nic_type)
    }

def get_arm_a_ubootb_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_ubootb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_ubootb_img, nic_type)
    }

def get_arm_a_ubootg_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_ubootg)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_ubootg_img, nic_type)
    }

def get_arm_a_zephyr_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_zephyr)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_zephyr_img, nic_type)
    }

def get_arm_a_zephyr_gold_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_zephyr_gold)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_zephyr_gold_img, nic_type)
    }

def get_arm_a_zephyr_a_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_zephyr_a)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_zephyr_a_img, nic_type)
    }

def get_arm_a_zephyr_b_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_a_zephyr_b)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_a_zephyr_b_img, nic_type)
    }

def get_fwsel_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, fwsel)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fwsel_img, nic_type)
    }

def get_device_config_dtb_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, device_config_dtb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.device_config_dtb, nic_type)
    }

def get_firmware_config_dtb_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, firmware_config_dtb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.firmware_config_dtb, nic_type)
    }

def get_arm_n_boot0_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_n_boot0)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_n_boot0_img, nic_type)
    }

def get_arm_n_uboota_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_n_uboota)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_n_uboota_img, nic_type)
    }

def get_arm_n_ubootb_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_n_ubootb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_n_ubootb_img, nic_type)
    }

def get_arm_n_ubootg_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_n_ubootg)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_n_ubootg_img, nic_type)
    }

def get_arm_n_kernel_goldfw_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, arm_n_kernel_goldfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.arm_n_kernel_goldfw_img, nic_type)
    }

def get_qspi_prog_sh_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, qspi_prog_sh_img)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.qspi_prog_sh_img, nic_type)
    }

def get_qspi_snake_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, qspi_snake_img)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.qspi_snake_img, nic_type)
    }

def get_mbist_boot0_img(mtp_mgmt_ctrl, slot, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, mbist_boot0_img)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.mbist_boot0_img, nic_type)
    }

def get_all_images_for_stage(mtp_mgmt_ctrl, slot, stage):
    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)
    # map image display names to the right get method
    image_method_map = {
        cpld: get_cpld,
        sec_cpld: get_sec_cpld,
        fail_cpld: get_fail_cpld,
        fea_cpld: get_fea_cpld,
        ufm1: get_ufm1,
        test_fpga: get_test_fpga,
        timer1: get_timer1,
        timer2: get_timer2,
        diagfw: get_diagfw,
        goldfw: get_goldfw,
        mainfw: get_mainfw,
        uboot: get_uboot,
        uboota: get_uboota,
        ubootb: get_ubootb,
        cert: get_cert,
        arm_a_boot0: get_arm_a_boot0_img,
        arm_a_uboota: get_arm_a_uboota_img,
        arm_a_ubootb: get_arm_a_ubootb_img,
        arm_a_ubootg: get_arm_a_ubootg_img,
        arm_a_zephyr: get_arm_a_zephyr_img,
        arm_a_zephyr_gold: get_arm_a_zephyr_gold_img,
        arm_a_zephyr_a: get_arm_a_zephyr_a_img,
        arm_a_zephyr_b: get_arm_a_zephyr_b_img,
        fwsel: get_fwsel_img,
        device_config_dtb: get_device_config_dtb_img,
        firmware_config_dtb: get_firmware_config_dtb_img,
        arm_n_boot0: get_arm_n_boot0_img,
        arm_n_uboota: get_arm_n_uboota_img,
        arm_n_ubootb: get_arm_n_ubootb_img,
        arm_n_ubootg: get_arm_n_ubootg_img,
        arm_n_kernel_goldfw: get_arm_n_kernel_goldfw_img,
        qspi_prog_sh_img: get_qspi_prog_sh_img,
        qspi_snake_img: get_qspi_snake_img,
        mbist_boot0_img: get_mbist_boot0_img
        }

    images_needed = list()

    if stage == FF_Stage.FF_DL:
        images_needed.append(cpld)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            images_needed.append(diagfw)

        if nic_type in SALINA_NIC_TYPE_LIST:
            images_needed.append(arm_a_boot0)
            images_needed.append(arm_a_uboota)
            images_needed.append(arm_a_ubootb)
            images_needed.append(arm_a_ubootg)
            images_needed.append(arm_a_zephyr_a)
            images_needed.append(arm_a_zephyr_b)
            images_needed.append(arm_a_zephyr_gold)
            images_needed.append(qspi_prog_sh_img)
            images_needed.append(fail_cpld)
            images_needed.append(fea_cpld)
            images_needed.append(ufm1)
            images_needed.append(qspi_snake_img)
            if nic_type in SALINA_DPU_NIC_TYPE_LIST:
                images_needed.append(arm_n_boot0)
                images_needed.append(arm_n_uboota)
                images_needed.append(arm_n_ubootb)
                images_needed.append(arm_n_ubootg)
                images_needed.append(arm_n_kernel_goldfw)
                images_needed.append(device_config_dtb)

        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(timer1)
            images_needed.append(timer2)

        elif nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(fea_cpld)

        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT, NIC_Type.ORTANO2ADICRS4):
            images_needed.append(goldfw)

        if nic_type in NEED_UBOOT_IMG_CARD_TYPE_LIST:
            images_needed.append(uboot)

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            images_needed.append(uboota)
            images_needed.append(ubootb)

    elif stage in (FF_Stage.FF_P2C, FF_Stage.FF_RDT, FF_Stage.FF_ORT, FF_Stage.FF_4C_H, FF_Stage.FF_4C_L):
        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(test_fpga)
            images_needed.append(cpld)

        if nic_type in SALINA_NIC_TYPE_LIST:
            images_needed.append(mbist_boot0_img)
            if nic_type in SALINA_DPU_NIC_TYPE_LIST:
                images_needed.append(arm_a_boot0)
                images_needed.append(arm_a_uboota)
                images_needed.append(arm_a_ubootb)
                images_needed.append(arm_a_ubootg)
                images_needed.append(arm_a_zephyr_a)
                images_needed.append(arm_a_zephyr_b)
                images_needed.append(arm_a_zephyr_gold)
                images_needed.append(device_config_dtb)
                images_needed.append(qspi_prog_sh_img)
                images_needed.append(fail_cpld)
                images_needed.append(ufm1)
                images_needed.append(qspi_snake_img)
                images_needed.append(arm_n_boot0)
                images_needed.append(arm_n_uboota)
                images_needed.append(arm_n_ubootb)
                images_needed.append(arm_n_ubootg)
                images_needed.append(arm_n_kernel_goldfw)

    elif stage == FF_Stage.FF_SWI:
        images_needed.append(cpld)
        images_needed.append(sec_cpld)
        if nic_type not in SALINA_NIC_TYPE_LIST:
            images_needed.append(goldfw)

        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(timer1)
            images_needed.append(timer2)
            images_needed.append(uboot)
            images_needed.append(mainfw)

        elif nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            images_needed.append(fail_cpld)

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            images_needed.append(cert)

        if nic_type in MAINFW_TYPE_LIST:
            images_needed.append(mainfw)

        if nic_type in SALINA_NIC_TYPE_LIST:
            images_needed.append(arm_a_boot0)
            images_needed.append(arm_a_uboota)
            images_needed.append(arm_a_ubootb)
            images_needed.append(arm_a_ubootg)
            images_needed.append(arm_a_zephyr_a)
            images_needed.append(arm_a_zephyr_b)
            images_needed.append(arm_a_zephyr_gold)
            images_needed.append(device_config_dtb)
            images_needed.append(fail_cpld)
            images_needed.append(ufm1)
            images_needed.append(qspi_prog_sh_img)
            if nic_type in SALINA_DPU_NIC_TYPE_LIST:
                images_needed.append(arm_n_boot0)
                images_needed.append(arm_n_uboota)
                images_needed.append(arm_n_ubootb)
                images_needed.append(arm_n_ubootg)
                images_needed.append(arm_n_kernel_goldfw)
                images_needed.append(mainfw)
            if nic_type in SALINA_AI_NIC_TYPE_LIST:
                images_needed.append(firmware_config_dtb)
                images_needed.append(arm_a_zephyr)
                if nic_type in NIC_Type.POLLARA:
                    images_needed.append(fwsel)

    # return dict with {"Image display name": filepath}
    ret_dict = dict()
    for image_name in images_needed:
        if image_name not in list(image_method_map.keys()):
            mtp_mgmt_ctrl.cli_log_err("script error: could not find key as {:s}".format(image_name))
            return None

        get_method = image_method_map[image_name]
        img_details = get_method(mtp_mgmt_ctrl, slot, stage)
        if img_details is None:
            nic_type_key = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, image_name)
            mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing {:s} for {:s}".format(image_name, nic_type_key))
            return None
        if "filename" not in list(img_details.keys()):
            return None
        if not img_details["filename"]:
            nic_type_key = pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, image_name)
            mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing {:s} for {:s}".format(image_name, nic_type_key))
            return None
        ret_dict[image_name] = img_details["filename"]

    return ret_dict

def pick_dictionary_key(mtp_mgmt_ctrl, slot, stage, image_name):
    # some images are not stored by [NIC_TYPE], rather by their PN

    nic_type = mtp_mgmt_ctrl.mtp_get_nic_type(slot)

    if stage == FF_Stage.FF_DL:
        if image_name == diagfw:
            if nic_type == NIC_Type.ORTANO2:# and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                return "68-0015"

        if nic_type in CTO_MODEL_TYPE_LIST:
            dpn = mtp_mgmt_ctrl.get_scanned_dpn(slot)
            if not dpn or dpn == "None":
                # not a stage with scanning, read from FRU
                dpn = mtp_mgmt_ctrl.mtp_get_nic_dpn(slot)
            return str(dpn)

    if stage == FF_Stage.FF_SWI:
        if image_name in (goldfw, mainfw):
            if nic_type == NIC_Type.ORTANO2:# and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                return "68-0015"
            if nic_type == NIC_Type.ORTANO2ADI:
                return "68-0026"
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                return "68-0028"
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                return "68-0034"
            if nic_type == NIC_Type.ORTANO2ADICR:
                return "68-0049"
            if nic_type == NIC_Type.ORTANO2ADICRMSFT:
                return "68-0091"

        if image_name in (cpld, sec_cpld, fail_cpld):
            if nic_type == NIC_Type.ORTANO2ADI:
                return "68-0026"
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                return "68-0028"
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                return "68-0034"

        if image_name == cert:
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                return "68-0028"

        if nic_type in CTO_MODEL_TYPE_LIST:
            return str(mtp_mgmt_ctrl.get_scanned_sku(slot))

    # else return original nic_type
    return nic_type
