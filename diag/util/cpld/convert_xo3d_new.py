#!/usr/bin/env python
import sys
from array import *

class xo3d_convert:
    def __init__(self):
        self.name = "convert jed to bin"

    def convert_cfg(self, image_number, filename, outfile):
        bin_array = array('B')
        total_page = 0

        with open (filename) as f:
            lines = f.readlines()
            begin = lines.index('L0000000\r\n')
            second = lines.index('NOTE EBR_INIT DATA*\r\n')
            third = lines.index('NOTE END CONFIG DATA*\r\n')
            if image_number == 0:
                end = lines.index('NOTE USER MEMORY DATA UFM0*\r\n')
            elif image_number == 1:
                end = lines.index('NOTE USER MEMORY DATA UFM1*\r\n')
            else:
                print "Invalide image number\n"
                return
            for j in range(begin + 1, second -1):
                s = lines[j]
                total_page = total_page + 1
                for i in range(16):
                    bin_array.append(int((s[i*8 : (i+1)*8]), 2))
            for j in range(second + 2, third - 1):
                s = lines[j]
                total_page = total_page + 1
                for i in range(16):
                    bin_array.append(int((s[i*8 : (i+1)*8]), 2))
            for j in range(third + 2, end - 1):
                s = lines[j]
                total_page = total_page + 1
                if total_page > 12541:
                    break;
                for i in range(16):
                    bin_array.append(int((s[i*8 : (i+1)*8]), 2))
        f = file(outfile, 'wb')
        bin_array.tofile(f)
        f.close()

    def convert_ufm(self, image_number, filename, outfile):
        ufm_array = array('B')
        total_page = 0

        with open (filename) as f:
            lines = f.readlines()
            if image_number == 0:
                start = lines.index('NOTE USER MEMORY DATA UFM0*\r\n')
            elif image_number == 1:
                start = lines.index('NOTE USER MEMORY DATA UFM1*\r\n')
            else:
                print "Invalide image number\n"
                return
            ufm_end = lines.index('NOTE User Electronic Signature Data*\r\n')
            for j in range(start + 2, ufm_end - 2):
                s = lines[j]
                for i in range(16):
                    ufm_array.append(int((s[i*8 : (i+1)*8]), 2))
        f = file(outfile, 'wb')
        ufm_array.tofile(f)
        f.close()

    def convert_fea(self, filename, outfile):
        bin_array = array('B')
        output_file = filename[:filename.find('.')] + "_fea.bin"
        with open (filename) as f:
            lines = f.readlines()
            begin = lines.index('DATA:\r\n')
            s = lines[begin+1]
            for i in range(12):
                bin_array.append(int((s[i*8 : (i+1)*8]), 2))
            s = lines[begin+2]
            for i in range(4):
                bin_array.append(int((s[i*8 : (i+1)*8]), 2))
            f.close()
            f = file(outfile, 'wb')
            bin_array.tofile(f)
            f.close()

if __name__=="__main__":
    convert = xo3d_convert()
    image_number = sys.argv[1]
    filename = sys.argv[2]
    outfile = sys.argv[3]

    if image_number == "cfg0":
        convert.convert_cfg(0, filename, outfile)
    elif image_number == "cfg1":
        convert.convert_cfg(1, filename, outfile)
    elif image_number == "ufm0":
        convert.convert_ufm(0, filename, outfile)
    elif image_number == "ufm1":
        convert.convert_ufm(1, filename, outfile)
    elif image_number == "fea":
        convert.convert_fea(filename, outfile)
    else:
        print "Invalid config name provided\n"
        print "./convert_xo3d cfg0 infile outfile\n"
        print "./convert_xo3d cfg1 infile outfile\n"
        print "./convert_xo3d ufm0 infile outfile\n"
        print "./convert_xo3d ufm1 infile outfile\n"
        print "./convert_xo3d fea infile outfile\n"
        print "./convert_xo3d cfg0 somefile.jed target_file.bin\n"

    sys.exit()
