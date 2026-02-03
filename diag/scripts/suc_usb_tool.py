#!/usr/bin/env python3

# Copyright (c) 2025 Advanced Micro Devices, Inc. (AMD)

#
# suc_usb_tool.py: interact with a board connected via USB
#
#  - discover USB CDC_ACM shell tty based on the board's PIC device ID
#     - from Zephyr shell, use "hwinfo devid" to discover your ID
#
#  - upload CPLD image over USB for flashing
#     - only uploads, doesn't actually flash (use "cpld" cmds in Zephyr shell)
#
# ("suc_usb_tool.py --help" for usage info)
#

import sys
import argparse
import errno
import struct
import array
import re
import time
import subprocess
import os
from pathlib import Path
from zlib import crc32
try:
    import usb.core
    import usb.util
    missing_pyusb = False
except ModuleNotFoundError:
    missing_pyusb = True


# Region codes for the usb_test_class driver on the device
REGION_CPLD_IMAGE = 0x01

# TBD: This is still from the Zephyr loopback sample - we should change it.
VENDOR_DEVICE_PAIRS = (
                       (0x2fe3, 0x000a),  # Original Zephyr loopback sample IDs
                       (0x0438, 0x0001),  # AMD vendor ID, temporary device ID
                       (0x0438, 0x000a),  # AMD vendor ID, temporary device ID
                      )

# -----------------------------------------------------------------------------
#  Basic USB device access
# -----------------------------------------------------------------------------

class UsbDevices:
    _devices_dir = Path('/sys/bus/usb/devices')

    class UsbDevice:
        def __init__(self, usb_dev_dir, skip_read_serial=False):
            self.name = usb_dev_dir.name
            self.dir = usb_dev_dir
            self.busnum = self.read_value_or_none('busnum', 0)
            self.devnum = self.read_value_or_none('devnum', 0)
            self.idVendor = self.read_value_or_none('idVendor', 16)
            self.idProduct = self.read_value_or_none('idProduct', 16)
            self.bInterfaceClass = self.read_value_or_none('bInterfaceClass', 16)
            if skip_read_serial:
                self.serial = None
            else:
                self.serial = self.read_string_or_none('serial')

        def __repr__(self):
            if self.idVendor is not None:
                return 'UsbDevice({:04x}:{:04x}@{})'.format(self.idVendor,
                                                            self.idProduct,
                                                            self.name)
            elif self.bInterfaceClass is not None:
                return 'UsbDevice(class=0x{:02x}@{})'.format(self.bInterfaceClass,
                                                       self.name)
            else:
                return 'UsbDevice({})'.format(self.name)

        def file_exists(self, filename):
            return (self.dir / filename).exists()

        def read_string(self, filename):
            return (self.dir / filename).read_text().strip()

        def read_string_or_none(self, filename):
            if self.file_exists(filename):
                return (self.dir / filename).read_text().strip()
            else:
                return None

        def read_value(self, filename, base=0):
            return int(self.read_string(filename), base)

        def read_value_or_none(self, filename, base=0):
            if self.file_exists(filename):
                return int(self.read_string(filename), base)
            else:
                return None

        def read_dir(self, dirname):
            return [p.name for p in (self.dir / dirname).iterdir()]

        def match_serial(self, serial):
            if serial == None:
                return True
            if ':' in serial:
                match_bus, _, match_dev = serial.partition(':')
                try:
                    return int(match_bus) == self.busnum and int(match_dev) == self.devnum
                except:
                    return False
            serial = serial.upper()
            if serial.startswith('0X'):
                serial = serial[2:]
            return self.serial == serial

    def __init__(self, skip_read_serial=False):
        self._devices = {}
        for usb_dev_dir in self._devices_dir.iterdir():
            usb_dev = self.UsbDevice(usb_dev_dir, skip_read_serial)
            self._devices[usb_dev.name] = usb_dev

    def find_all_by_id(self, match_idVendor, match_idProduct):
        result = []
        for name in self._devices:
            usb_dev = self._devices[name]
            if usb_dev.idVendor == match_idVendor and usb_dev.idProduct == match_idProduct:
                result.append(usb_dev)
        return result

    def find_interfaces(self, match_name, match_class=None):
        result = []
        for name in self._devices:
            if name.startswith(match_name + ':'):
                usb_dev = self._devices[name]
                if match_class is None or usb_dev.bInterfaceClass == match_class:
                    result.append(usb_dev)
        return result


# -----------------------------------------------------------------------------
#  Bulk command interface implemented by the usb_test_class class driver
# -----------------------------------------------------------------------------

class BulkCmdInterface:
    USB_TEST_CMD_WRITE = 0x00
    USB_TEST_CMD_READ = 0x01
    USB_TEST_CMD_FILL = 0x02
    USB_TEST_CMD_GET_LEN = 0x03
    USB_TEST_CMD_GET_CRC = 0x04
    USB_TEST_RESP_FLAG = 0x80

    def __init__(self, busnum, devnum, timeout_ms=2000):
        if missing_pyusb:
            print("Can't access the device: pyusb not installed (install in a venv?)", file=sys.stderr)
            sys.exit(1)
        self._dev = usb.core.find(bus=busnum, address=devnum)
        assert(self._dev is not None)
        try:
            self._dev.set_configuration()
        except usb.core.USBError as e:
            if e.errno == errno.EBUSY:
                pass  # probably UART already open?
            else:
                raise
        self._cfg = self._dev.get_active_configuration()
        self._intf = usb.util.find_descriptor(self._cfg, bInterfaceClass=0xff)
        self._out_ep = self._find_bulk_endpoint(usb.util.ENDPOINT_OUT)
        self._in_ep = self._find_bulk_endpoint(usb.util.ENDPOINT_IN)
        self._timeout = timeout_ms

    def _find_bulk_endpoint(self, ep_type):
        return usb.util.find_descriptor(
            self._intf,
            custom_match = lambda e: (
                usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK and
                usb.util.endpoint_direction(e.bEndpointAddress) == ep_type
                )
            )

    def _run_cmd(self, msg):
        sent = self._out_ep.write(msg, timeout=self._timeout)
        if sent < len(msg):
            raise IOError("Command {} (out) failed: len={} but rc={}".format(ord(msg[0]), len(msg), sent))
        resp = self._in_ep.read(self._in_ep.wMaxPacketSize, timeout=self._timeout)
        if resp[0] != msg[0] | self.USB_TEST_RESP_FLAG:
            raise IOError("Command {} bad response type 0x{:02x}".format(msg[0], resp[0]))
        if resp[1] != 0:
            raise IOError("Command {} resported error %u".format(msg[0], resp[1]))
        return resp[2:]

    def max_write_chunk(self):
        return self._out_ep.wMaxPacketSize - 8

    def max_read_chunk(self):
        return self._in_ep.wMaxPacketSize - 2

    def write(self, region, offset, data):
        msg = struct.pack('>BBIH', self.USB_TEST_CMD_WRITE, region, offset, len(data))
        msg += data
        resp = self._run_cmd(msg)
        assert len(resp) == 0

    def read(self, region, offset, length):
        msg = struct.pack('>BBIH', self.USB_TEST_CMD_READ, region, length)
        resp = self._run_cmd(msg)
        assert len(resp) == length
        return resp

    def fill(self, region, byte):
        msg = struct.pack('>BBB', self.USB_TEST_CMD_FILL, region, byte)
        resp = self._run_cmd(msg)
        assert len(resp) == 0

    def get_len(self, region):
        msg = struct.pack('>BB', self.USB_TEST_CMD_GET_LEN, region)
        resp = self._run_cmd(msg)
        assert len(resp) == 4
        return struct.unpack('>I', resp)[0]

    def get_crc(self, region):
        msg = struct.pack('>BB', self.USB_TEST_CMD_GET_CRC, region)
        resp = self._run_cmd(msg)
        assert len(resp) == 4
        return struct.unpack('>I', resp)[0]


# -----------------------------------------------------------------------------
#  JEDEC file parsing
# -----------------------------------------------------------------------------

class JedecParser:

    # Size of CFG area in bytes (from documentation) is 200656 (0x30fd0)
    _CFG_BYTES = 200656

    def __init__(self, filename):
        self._bit_address = 0
        self._image = None
        self._sum = 0
        with open(filename, 'r') as f:
            for l in f.readlines():
                self._parse(l)

    def _parse(self, line):
        l = line.strip()
        if l.startswith('F'):
            # F<n> is the default value of unspecified bits
            if l[1] == '0':
                self._image = array.array('B', [0x00 for x in range(self._CFG_BYTES)])
            elif l[1] == '1':
                self._image = array.array('B', [0xff for x in range(self._CFG_BYTES)])
            else:
                raise ValueError('Unexpected: ' + l)
        elif l.startswith('G1'):
            # G<n> is the encryption flag - not sure how to handle if it's set
            raise ValueError('Encryption not handled: ' + l)
        elif l.startswith('L'):
            # L<addr> sets the bit address
            self._bit_address = int(l[1:])
        elif l.startswith('0') or l.startswith('1'):
            # Strings of 0/1 bits are the data we're interested in
            # (all the files I've seen write one 128-bit row at a time)
            assert (self._bit_address % 8) == 0
            assert (len(l) % 8) == 0
            offset = self._bit_address // 8
            while l != '':
                # Bits are in the right order in the file for simple conversion to a byte for SPI...
                b = int(l[:8], 2)
                # ...but need to be reversed for adding to the running checksum
                self._sum +=  int(l[:8][::-1], 2)
                # Anything outside the CFG region (the .jed files also have uninteresting content for UFM)
                # can be ignored for the purpose of making the binary image (but still included in checksum).
                if offset < self._CFG_BYTES:
                    self._image[offset] = b
                l = l[8:]
                offset += 1
            self._bit_address = offset * 8
        elif l.startswith('C'):
            # Checksum - we should have got this right
            assert int(l[1:5], 16) == self._sum & 0xffff

    def image(self):
        return self._image

    def write(self, f):
        self._image.tofile(f)

    def crc32(self):
        return crc32(self._image)


# -----------------------------------------------------------------------------
#  Main application code
# -----------------------------------------------------------------------------

def handle_upload(busnum, devnum, filename):
    print('Parsing {}'.format(filename))
    jp = JedecParser(filename)
    image = jp.image()
    image_len = len(image)
    crc = crc32(image)
    cmd_if = BulkCmdInterface(busnum, devnum)
    needed_len = cmd_if.get_len(REGION_CPLD_IMAGE)
    if image_len != needed_len:
        print('JEDEC file parsed as {} bytes, but we need {}'.format(image_len, needed_len))
        return
    max_chunk = cmd_if.max_write_chunk()
    for offset in range(0, image_len, max_chunk):
        chunk = min(max_chunk, image_len - offset)
        sys.stdout.write('\rUploading: {:3d}% '.format((offset * 100) // image_len))
        sys.stdout.flush()
        cmd_if.write(REGION_CPLD_IMAGE, offset, image[offset:offset+chunk])
        time.sleep(0.01)  # Temporary hack to work around lack of buffering on device side
    print('\rUploading: 100%')
    check_crc = cmd_if.get_crc(REGION_CPLD_IMAGE)
    if check_crc == crc:
        print('Image CRC = 0x{:08x}'.format(crc))
        print('*** Use Zephyr shell to actually program it into flash! ***')
    else:
        print('UPLOAD FAILED: image CRC = 0x{:08x} does not match device buffer = 0x{:08x}'.format(crc, check_crc))

def handle_crc(busnum, devnum):
    cmd_if = BulkCmdInterface(busnum, devnum)
    crc = cmd_if.get_crc(REGION_CPLD_IMAGE)
    print("CRC of current device upload buffer content = 0x{:08x}".format(crc))

def get_bus_dev_from_sucuart(slot):
    """Given slot=x, resolve /dev/SUCUARTx and return (busnum, devnum)"""

    busnum=0
    devnum=0

    if int(slot)<1 or int(slot) > 10:
        print(f"Error: Slot needs to be in the range of 1-10.  You entered --> {slot}")
        sys.exit(1)
    
    card_path_dict = dict()
    card_path_dict[1] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-1"
    card_path_dict[2] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-2"
    card_path_dict[3] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-3"
    card_path_dict[4] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-4"
    card_path_dict[5] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-5"
    card_path_dict[6] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.3/usb3/3-6"
    card_path_dict[7] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-1/"
    card_path_dict[8] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-2/"
    card_path_dict[9] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-3/"
    card_path_dict[10] = "/sys/devices/pci0000:00/0000:00:01.6/0000:04:00.0/0000:05:08.0/0000:06:00.1/usb1/1-4/"
    print(" Path={}".format(card_path_dict[slot]))
    try:
        with open(os.path.join(card_path_dict[slot], "busnum")) as f:
            busnum = int(f.read().strip())
        with open(os.path.join(card_path_dict[slot], "devnum")) as f:
            devnum = int(f.read().strip())
    except FileNotFoundError:
        print(f"Error: busnum/devnum not found for {card_path_dict[slot]}")
        print("Check the slot is present and powered on")
        sys.exit(1)
    return busnum, devnum

def parse_args():
    parser = argparse.ArgumentParser()
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-l', '--list', default=False, action='store_true',
                        help="List serial numbers of attached devices")
    group1.add_argument('-d', '--device', metavar='DEVICE', type=str, action='store',
                        help="Device to talk to")
    group1.add_argument('-s', '--slot', metavar='SLOT', type=int, action='store',
                        help="Specify SUCUART slot number (e.g. --slot 2)")
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-t', '--tty', default=False, action='store_true',
                        help="Find the CDC-ACM tty for this device")
    group2.add_argument('-u', '--upload', metavar='IMAGE', type=str, action='store',
                        help="Upload CPLD image to device")
    group2.add_argument('-c', '--crc', default=False, action='store_true',
                        help="Get CRC of device CPLD image upload buffer")
    group2.add_argument('-z', '--zero', default=False, action='store_true',
                        help="Zero the device CPLD image upload buffer")
    args = parser.parse_args()
    if args.list and (args.tty or args.upload or args.crc or args.zero):
        parser.error("-l/--list doesn't make sense with other options")
    return args

def main(args):
    # If slot is provided, handle that path first
    if getattr(args, "slot", None) is not None:
        busnum, devnum = get_bus_dev_from_sucuart(args.slot)
        if args.upload:
            handle_upload(busnum, devnum, args.upload)
        elif args.crc:
            handle_crc(busnum, devnum)
        elif args.zero:
            handle_zero(busnum, devnum)
        else:
            print(f"Slot {args.slot}: Bus={busnum}, Dev={devnum}")
        return
    skip_read_serial = args.device is not None and ':' in args.device
    usb_devs = UsbDevices(skip_read_serial)
    our_usb_devs = []
    for vendor_id, device_id in VENDOR_DEVICE_PAIRS:
        our_usb_devs.extend(usb_devs.find_all_by_id(vendor_id, device_id))
    matched = False
    for dev in our_usb_devs:
        if not dev.match_serial(args.device):
            continue
        matched = True
        cdc_ifs = usb_devs.find_interfaces(dev.name, match_class=2)
        assert len(cdc_ifs) <= 1
        vendor_ifs = usb_devs.find_interfaces(dev.name, match_class=0xff)
        assert len(vendor_ifs) <= 1
        if args.list or args.tty:
            if len(cdc_ifs) > 0:
                ttys = cdc_ifs[0].read_dir('tty')
                assert len(ttys) == 1
                tty = '/dev/' + ttys[0]
            else:
                tty = None
            if args.list:
                print(dev.serial, tty)
            else:
                assert(tty is not None)
                print(tty)
        elif args.upload:
            handle_upload(dev.busnum, dev.devnum, args.upload)
        elif args.crc:
            handle_crc(dev.busnum, dev.devnum)
        elif args.zero:
            handle_zero(dev.busnum, dev.devnum)

    if len(our_usb_devs) == 0:
        print('No suitable USB devices found!')
        sys.exit(1)

    if not matched:
        print('Requested device not found (try -l to list devices?)')
        sys.exit(1)

if __name__ == '__main__':
    main(parse_args())
