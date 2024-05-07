In CTO model, one nic_type can have different flavors
- in DL-4C, it has different flavors of DPNs
- in SWI-FST, it has different flavors of SKUs
- each flavor comes with its own CPLD and FW images, following SW Image Tracking spreadsheet

Remove SW PN for all cards, CTO and older. SW PN is hardcoded in script instead of being scanned.
- mainfw (and netapp_nic_profile.py) does not need to be linked as a file

