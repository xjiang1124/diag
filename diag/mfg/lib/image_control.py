from libmfg_cfg import *
from libdefs import FF_Stage

cpld = "CPLD"
sec_cpld = "Secure CPLD"
fail_cpld = "Failsafe CPLD"
fea_cpld = "CPLD Feature Row"
fpga = "FPGA"
test_fpga = "Test FPGA"
timer1 = "FPGA timer1"
timer2 = "FPGA timer2"
diagfw = "DiagFW"
goldfw = "GoldFW"
uboot = "uboot"
uboota = "uboota"
ubootb = "ubootb"
cert = "certificate"

def get_dict_entry(mtp_mgmt_ctrl, img_dict, nic_type):
    try:
        return img_dict[nic_type]
    except Exception:
        return ""

def get_cpld(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cpld_dat, nic_type)
    }

def get_sec_cpld(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, sec_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.sec_cpld_dat, nic_type)
    }

def get_fail_cpld(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, fail_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fail_cpld_dat, nic_type)
    }

def get_fea_cpld(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, fea_cpld)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.fea_cpld_img, nic_type)
    }

def get_timer1(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, timer1)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.timer1_img, nic_type)
    }

def get_timer2(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, timer2)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.timer2_img, nic_type)
    }

def get_test_fpga(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, test_fpga)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_img, nic_type),
    "version":   get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_ver, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.test_fpga_dat, nic_type)
    }

def get_diagfw(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, diagfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.diagfw_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.diagfw_dat, nic_type)
    }

def get_goldfw(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, goldfw)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.goldfw_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.goldfw_dat, nic_type)
    }

def get_uboot(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, uboot)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboot_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboot_dat, nic_type)
    }

def get_uboota(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, uboota)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboota_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.uboota_dat, nic_type)
    }

def get_ubootb(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, ubootb)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.ubootb_img, nic_type),
    "timestamp": get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.ubootb_dat, nic_type)
    }

def get_cert(mtp_mgmt_ctrl, nic_type, stage):
    nic_type = pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, cert)
    return {
    "filename":  get_dict_entry(mtp_mgmt_ctrl, NIC_IMAGES.cert_img, nic_type)
    }

def get_all_images_for_stage(mtp_mgmt_ctrl, nic_type, stage):
    # map image display names to the right get method
    image_method_map = {
        cpld: get_cpld,
        sec_cpld: get_sec_cpld,
        fail_cpld: get_fail_cpld,
        fea_cpld: get_fea_cpld,
        test_fpga: get_test_fpga,
        timer1: get_timer1,
        timer2: get_timer2,
        diagfw: get_diagfw,
        goldfw: get_goldfw,
        uboot: get_uboot,
        uboota: get_uboota,
        ubootb: get_ubootb,
        cert: get_cert
        }

    images_needed = list()

    if stage == FF_Stage.FF_DL:
        images_needed.append(cpld)
        images_needed.append(diagfw)

        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(timer1)
            images_needed.append(timer2)

        elif nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(fea_cpld)

        if nic_type in (NIC_Type.ORTANO2ADI, NIC_Type.ORTANO2ADIIBM, NIC_Type.ORTANO2ADIMSFT, NIC_Type.ORTANO2ADICR, NIC_Type.ORTANO2ADICRMSFT):
            images_needed.append(goldfw)

        if nic_type in NEED_UBOOT_IMG_CARD_TYPE_LIST:
            images_needed.append(uboot)

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            images_needed.append(uboota)
            images_needed.append(ubootb)

    elif stage == FF_Stage.FF_P2C:
        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(test_fpga)

    elif stage == FF_Stage.FF_SWI:
        images_needed.append(cpld)
        images_needed.append(sec_cpld)
        images_needed.append(goldfw)

        if nic_type in FPGA_TYPE_LIST:
            images_needed.append(fail_cpld)
            images_needed.append(timer1)
            images_needed.append(timer2)
            images_needed.append(uboot)

        elif nic_type in ELBA_NIC_TYPE_LIST or nic_type in GIGLIO_NIC_TYPE_LIST:
            images_needed.append(fail_cpld)

        if nic_type == NIC_Type.ORTANO2ADIIBM:
            images_needed.append(cert)

    # return dict with {"Image display name": filepath}
    ret_dict = dict()
    for image_name in images_needed:
        if image_name not in image_method_map.keys():
            mtp_mgmt_ctrl.cli_log_err("script error: could not find key as {:s}".format(image_name))
            return None

        get_method = image_method_map[image_name]
        img_details = get_method(mtp_mgmt_ctrl, nic_type, stage)
        if img_details is None:
            mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing {:s} for {:s}".format(image_name, nic_type))
            return None
        if "filename" not in img_details.keys():
            return None
        if not img_details["filename"]:
            mtp_mgmt_ctrl.cli_log_err("mfg_cfg is missing {:s} for {:s}".format(image_name, nic_type))
            return None
        ret_dict[image_name] = img_details["filename"]

    return ret_dict

def pick_dictionary_key(mtp_mgmt_ctrl, nic_type, stage, image_name):
    # some images are not stored by [NIC_TYPE], rather by their PN

    if stage == FF_Stage.FF_DL:
        if image_name == diagfw:
            if nic_type == NIC_Type.ORTANO2:# and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                return "68-0015"

    if stage == FF_Stage.FF_SWI:
        if image_name == goldfw:
            if nic_type == NIC_Type.ORTANO2:# and mtp_mgmt_ctrl.mtp_is_nic_ortano_oracle(slot):
                return "68-0015"
            if nic_type == NIC_Type.ORTANO2ADI:
                return "68-0026"
            if nic_type == NIC_Type.ORTANO2ADIIBM:
                return "68-0028"
            if nic_type == NIC_Type.ORTANO2ADIMSFT:
                return "68-0034"

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

    # else return original nic_type
    return nic_type
