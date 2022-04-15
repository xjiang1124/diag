#!/usr/bin/python3

import mysql.connector
import json
import datetime

class mysql_db(object):
    def __init__(self,host='127.0.0.1',database='mfg'):
        self.host = host
        """ Read mysql config file."""
        filename = 'mysql.json'
        try:
            with open(filename) as data:
                mysqlip = json.load(data)
                self.host = mysqlip['ip']
        except IOError as err:
            print('File error: ' + str(err))
        print('Self Host: ' + self.host)
        self.database = database
        self.cnx = None

    def read_mysql_json():
        """ Read CA Servers config file."""
        filename = 'mysql.json'
        try:
            with open(filename) as data:
                mysqlip = json.load(data)
        except IOError as err:
            print('File error: ' + str(err))
            return -1

        return mysqlip['ip']

    def connect(self,username='',pw=''):        
        try:
            #self.cnx = mysql.connector.connect(user=username,password=pw,host=self.host,database=self.database)
            # Adding unix_socket was necessary to get this to work on opsfs.
            self.cnx = mysql.connector.connect(user=username,password=pw,host=self.host,database=self.database)
                #,unix_socket="/var/run/mysqld/mysqld.sock")
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                print("Error:  mysql username or password.")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                print("Error:  Database, {0}, does not exist.".format(self.database))
            else:
                print("Error: {0}".format(err))
            return -1
        else:
          #  self.disconnect();
            pass


        return 0


    def disconnect(self):
        print("Closing database.")
        self.cnx.close()

    def send_cmd(self,cmd,values):

        # Examples parameters:
        # cmd = ("INSERT INTO table "
        #       "(sn,pn) " 
        #       "VALUES (%s, %s)")
        # values = ( 'sn000888','JX999A' )

        cursor = self.cnx.cursor()
        try:
            cursor.execute(cmd,values)        
            self.cnx.commit()
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0

    def check_table(self,table):

        #cursor.execute("desc table_name")
        #print [column[0] for column in cursor.fetchall()]


        cmd = "desc {}".format(table)
        #print(cmd)
        cursor = self.cnx.cursor()
        output = list()
        try:
            cursor.execute(cmd)        
            #self.cnx.commit()
            #print([column[0] for column in cursor.fetchall()])
            for column in cursor.fetchall():
                #print(column[0])
                output.append(column[0])
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1


        return output

    def show_table(self):

        #cursor.execute("desc table_name")
        #print [column[0] for column in cursor.fetchall()]


        cmd = "SHOW TABLES"
        #print(cmd)
        cursor = self.cnx.cursor()
        output = list()
        try:
            cursor.execute(cmd)        
            #self.cnx.commit()
            #print([column[0] for column in cursor.fetchall()])
            for column in cursor.fetchall():
                #print(column[0])
                output.append(column[0])
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1


        return output

    def execute_cmd(self,cmd):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(cmd)        
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return None

    def read_cmd(self,cmd):

        cursor = self.cnx.cursor()
        output = list()
        try:
            cursor.execute(cmd)        
            for column in cursor.fetchall():
                output.append(column[0])
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return output

    def insert(self,cmd,values):

        # Examples parameters:
        # cmd = ("INSERT INTO hpn_certs "
        #       "(sn,pn) " 
        #       "VALUES (%s, %s)")
        # values = ( 'sn000888','JX999A' )

        cursor = self.cnx.cursor()
        try:
            cursor.execute(cmd,values)        
            self.cnx.commit()
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0

    def update_data(self,cmd):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(cmd)        
            self.cnx.commit()
            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0

    def insert_cert(self,cert,date_code,pid):
        # add_cert = ("INSERT INTO hpn_certs "
        #             "(sn,pn) " 
        #             "VALUES (%s, %s)")
        #print("  insert cmd: {0}".format(add_ce))

        data_cert = ( 'sn000999','JX999A' )

        cursor = self.cnx.cursor()
        cursor.execute(add_cert,data_cert)
        self.cnx.commit()
        cursor.close()    

        return 0


    def select_list(self,query,values,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query,values)        
            rows = cursor.fetchall()
            for row in rows:
                for item in row:
                    container.append(item) 

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0





    def select_ret_dict(self,query,values,fields,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query,values)        
            rows = cursor.fetchall()
            #print(fields)
            #print(rows)
            for row in rows:
                #print("row - {0}".format(row)) 
                first = 1;
                for field,item in zip(fields,row):
                    #print(" query field: {0}, item: {1}".format(field,item))
                    if first:
                        first_item = item
                        container[first_item] = dict()
                        first = 0
                        #print("found first_item: {0}".format(first_item))
                        continue
                    if type(item) is datetime.date:
                        item = item.strftime("%Y/%m/%d")

                    container[first_item][field] = item 

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1


        return 0

    def select_family_qty_dict(self,query,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query)        
            rows = cursor.fetchall()
            for row in rows:
                #print("row - {0}".format(row)) 
                container[row[0]] = row[1] 

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0

    def select_only_one_result(self,query,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query)        
            rows = cursor.fetchall()
            for row in rows:
                #print("row - {0}".format(row)) 
                container = row

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return 

        return 0

    def select_ret_list_of_dict(self,query,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query)        
            rows = cursor.fetchall()
            for row in rows:
                #print("row - {0}".format(row)) 
                container[row[0]] = list()
                for eachdata in row:
                    container[row[0]].append(str(eachdata))

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1

        return 0

    def select_ret_list(self,query,values,fields,container):

        cursor = self.cnx.cursor()
        try:
            cursor.execute(query,values)        
            rows = cursor.fetchall()
            #print(fields)
            #print(rows)
            for row in rows:
                #print("row - {0}".format(row)) 
                eachdict = dict()
                for field,item in zip(fields,row):
                    if type(item) is datetime.date:
                        item = item.strftime("%Y/%m/%d")

                    eachdict[field] = item 
                container.append(eachdict)

            cursor.close()    
        except mysql.connector.Error as err:
            print("Error: {0}".format(err))
            return -1


        return 0



