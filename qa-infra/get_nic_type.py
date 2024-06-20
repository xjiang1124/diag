import sys
jobd_nic_type = sys.argv[1].lower()

script_nic_type = {
        "naples100": "NAPLES100",
        "naples25swm-hpe": "NAPLES25SWM",
        "naples25swm-dell": "NAPLES25SWMDELL",
        "naples25ocp-hpe": "NAPLES25OCP",
        "naples25ocp-dell": "NAPLES25OCP",

        "ortano-ti-orc": "ORTANO2",
        "ortano-adi-orc": "ORTANO2ADI",
        "ortano-interp-orc": "ORTANO2INTERP",
        "ortano-solo-orc": "ORTANO2SOLO",
        "ortano-solo-orc_th": "ORTANO2SOLOORCTHS",
        "ortano-adicr-orc": "ORTANO2ADICR",
        "ortano-solo-orc-matera": "ORTANO2SOLO",

        "ortano-ti-msft": "ORTANO2",
        "ortano-adi-msft": "ORTANO2ADIMSFT",
        "ortano-solo-msft": "ORTANO2SOLOMSFT",
        "ortano-adicr-msft": "ORTANO2ADICRMSFT",

        "ortano-adi-ibm": "ORTANO2ADIIBM",

        "ortano-solo-s4": "ORTANO2SOLOS4",
        "ortano-adicr-s4": "ORTANO2ADICRS4",

        "lacona-hpe": "LACONA32",
        "lacona-dell": "LACONA32DELL",
        "pomonte-dell": "POMONTEDELL",

        "ginestra": "GINESTRA_D5",
        "ginestra-s4_58-0001-01": "GINESTRA_S4",
        "ginestra-s4_58-0002-01": "GINESTRA_S4",
        "dsc2a-2q200-32s32f64p-s4a": "GINESTRA_S4",
        "dsc2a-2q200-32s32f64p-s4b": "GINESTRA_S4",
        "dsc2a-2q200-32s32f64p-s4c": "GINESTRA_S4",
        }

if jobd_nic_type in script_nic_type:
    print(script_nic_type[jobd_nic_type])
else:
    print("Unknown")
