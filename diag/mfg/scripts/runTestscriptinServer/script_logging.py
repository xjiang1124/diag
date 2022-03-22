 #!/usr/bin/python3

import os
import time
import datetime

class Script_logging(object):
    def __init__(self,log_dir='.',log_prefix='log',log_suffix='txt'):

        self.log_dir = log_dir
        self.log_prefix = log_prefix
        self.log_suffix = log_suffix
        self.write_to_console = 1  
        self.insert_timestamp = 1
        self.filehandle=None
        self.wirtehandle=False
        self.basename=None
        self.fullname=None

    def Set_wirtehandle_lock(self):
        self.wirtehandle = True

    def Set_wirtehandle_unlock(self):
        self.wirtehandle = False

    def check_wirtehandle(self):
        return self.wirtehandle

    def Set_log_dir(self,directory):
        self.log_dir = directory

    def Set_log_prefix(self,prefix):
        self.log_prefix = prefix

    def Set_log_suffix(self,suffix):
        self.log_suffix = suffix

    def Set_insert_timestamp(self,state):
        self.insert_timestamp = state

    def Set_write_to_console(self,state):
        self.write_to_console = state

    def Open(self):
        if self.filehandle:
            print("Error: Log file already opened.".format(self.filename))
            return -1;

        self.set_filename()

        if not os.path.exists(self.log_dir):
            print("Creating directory: {0}".format(self.log_dir))
            stat=os.makedirs(self.log_dir)
            if stat:
                print("Error: Failed to open directory {0}".format(self.log_dir))
                return -1;

        try:
         #  with open(self.fullname, "w") as handle:
            handle = open(self.fullname, "w")
            self.set_filehandle(handle)
            self.WriteLine("Log opened")
        except IOError as err:
            print("Error: Opening file {0}".format(self.fullname))
            print("Error. Err code: {0}".format(str(err)))
            return -1
       

        #self.Writeline("log still opened!")
 
        return 0


    def Open_again(self):

        try:
         #  with open(self.fullname, "w") as handle:
            handle = open(self.fullname, "a")
            self.set_filehandle(handle)
            self.WriteLine("Log opened")
        except IOError as err:
            print("Error: Opening file {0}".format(self.fullname))
            print("Error. Err code: {0}".format(str(err)))
            return -1
       
        return 0


    def Close(self):
        if self.filehandle:
            self.WriteLine("Closing log: {0}".format(self.fullname))
            self.filehandle.close()         
        else:
            print("Error: Filehandle does not exist.")
            return -1
        return 0

    def WriteLine(self,message):
        if self.write_to_console:
           print("{0}".format(message))

        while True:
            if not self.check_wirtehandle():
                self.Set_wirtehandle_lock()
                timestamp = ''
                if self.insert_timestamp: 
                    now = datetime.datetime.now()
                    timestamp = now.strftime("%y%m%d_%H%M%S: ");

                msg = timestamp + str(message)

                #print("logname {0}".format(self.fullname))
                print(msg,file=self.filehandle)
                self.Set_wirtehandle_unlock()
                break
            else:
                time.sleep(1)

        return 0

    def Write(self,message):
        if self.write_to_console:
            print(message)
        while True:
            if not self.check_wirtehandle():
                self.Set_wirtehandle_lock()
                print(message,file=self.filehandle)
                self.Set_wirtehandle_unlock()
                break
            else:
                time.sleep(1)
        return 0
           
    def Delete_log(self):
        print("Deleting log {0}.".format(self.fullname))
    
        if os.remove(self.fullname):
            print("Error: Delete log {0} failed.".format(self.fullname))
            return -1


    def set_filename(self):
        now = datetime.datetime.now()
        timestamp = now.strftime("%y%m%d-%H%M%S");

        self.basename = self.log_prefix + '-' + timestamp + self.log_suffix
        self.fullname = self.log_dir + '/' + self.basename

        print(self.fullname)


    def set_filehandle(self,handle):
        self.filehandle = handle


    def finddisplaytime(self,start):
        difftime = datetime.datetime.now()-start
        hours, minutes, seconds = self.convert_timedelta(difftime)
        #print('{} minutes, {} hours'.format(minutes, hours))
        displaytime = "{hour:0>2d}:{minute:0>2d}:{second:0>2d}".format(
                    hour=hours,
                    minute=minutes,
                    second=seconds
                    )
        return displaytime  

    def convert_timedelta(self,duration):
        days, seconds = duration.days, duration.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return hours, minutes, seconds
