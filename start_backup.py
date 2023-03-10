#!/usr/bin/python3
class bc:
    hed = '\033[95m'
    dtm = '\033[0;36;40m'
    ENDC = '\033[0m'
    SUB = '\033[3;30;45m'
    WARN = '\033[0;31;40m'
    grn = '\033[0;32;40m'
    wht = '\033[0;37;40m'
    ylw = '\033[93m'
    fail = '\033[91m'
    blu = '\033[36m'


print(bc.hed + " ")
print("    __  __                             _         ")
print("   |  \/  |                    /\     (_)        ")
print("   | \  / |   __ _  __  __    /  \     _   _ __  ")
print("   | |\/| |  / _` | \ \/ /   / /\ \   | | | '__| ")
print("   | |  | | | (_| |  >  <   / ____ \  | | | |    ")
print("   |_|  |_|  \__,_| /_/\_\ /_/    \_\ |_| |_|    ")
print(" ")
print("             " +bc.SUB + "S M A R T   THERMOSTAT " + bc.ENDC)
print("********************************************************")
print("*        Script Backup Database to a gz file and       *")
print("*                send as an Email message.             *")
print("*                Build Date: 26/10/2019                *")
print("*      Version 0.05 - Last Modified 12/06/2022         *")
print("*                                 Have Fun - PiHome.eu *")
print("********************************************************")
print(" ")
print(" " + bc.ENDC)

import MySQLdb as mdb, datetime, sys, smtplib, string, os
import configparser
import subprocess

# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Initialise the database access varables
config = configparser.ConfigParser()
config.read('/var/www/st_inc/db_config.ini')
dbhost = config.get('db', 'hostname')
dbuser = config.get('db', 'dbusername')
dbpass = config.get('db', 'dbpassword')
dbname = config.get('db', 'dbname')

# Create the container (outer) email message.
try:
    con = mdb.connect(dbhost, dbuser, dbpass, dbname)
    cursorselect = con.cursor()
    query = ("SELECT * FROM email;")
    cursorselect.execute(query)
    name_to_index = dict(
        (d[0], i)
        for i, d
        in enumerate(cursorselect.description)
    )
    results = cursorselect.fetchone()
    cursorselect.close()
    if cursorselect.rowcount > 0:
        USER = results[name_to_index['username']]
        result = subprocess.run(
            ['php', '/var/www/cron/email_passwd_decrypt.php'],         # program and arguments
            stdout=subprocess.PIPE,                     # capture stdout
            check=True                                  # raise exception if program fails
        )
        PASS = result.stdout.decode("utf-8").split()[0] # result.stdout contains a byte-string
        HOST = results[name_to_index['smtp']]
        PORT = results[name_to_index['port']]
        TO = results[name_to_index['to']]
        FROM = results[name_to_index['from']]
        SUBJECT = "MaxAir Database Backup"
        MESSAGE = ""
        send_status = results[name_to_index['status']]
    else:
        print("Error - No Email Account Found in Database.")
        sys.exit(1)

    cursorselect = con.cursor()
    query = ("SELECT backup_email FROM system;")
    cursorselect.execute(query)
    name_to_index = dict(
        (d[0], i)
        for i, d
        in enumerate(cursorselect.description)
    )
    results = cursorselect.fetchone()
    if cursorselect.rowcount > 0:
        TO = results[name_to_index['backup_email']]
    else:
        print("Error - No Backup Email Account Found in Database.")
        sys.exit(1)

    query = ("SELECT destination FROM auto_backup LIMIT 1;")
    cursorselect.execute(query)
    destination_to_index = dict(
        (d[0], i)
        for i, d
        in enumerate(cursorselect.description)
    )
    result = cursorselect.fetchone()
    if cursorselect.rowcount > 0 and len(result[destination_to_index['destination']]) > 0:
        destination = result[destination_to_index['destination']]
    else:
        destination = "/var/www/MySQL_Database/database_backups/"
    cursorselect.close()

except mdb.Error as e:
    print("Error %d: %s" % (e.args[0], e.args[1]))
    sys.exit(1)
finally:
    if con:
        con.close()

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Database Backup Script Started")
print("------------------------------------------------------------------")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Creating Database Backup SQL File")
print("------------------------------------------------------------------")
dumpfname = dbname + "_" + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ".sql";
cmd = "mysqldump --ignore-table=" + dbname + ".backup --add-drop-table --host=" + dbhost +" --user=" + dbuser + " --password=" + dbpass + " " + dbname + " > " + dumpfname
os.system(cmd)
print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Database Backup SQL File Created")
print("------------------------------------------------------------------")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Creating ZIP Archive of SQL File")
print("------------------------------------------------------------------")

zipfname = dumpfname + ".gz"
cmd = "gzip " + dumpfname
os.system(cmd)

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - ZIP Archive Created")
print("------------------------------------------------------------------")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Emailing the ZIP Archive File")
print("------------------------------------------------------------------")

# Send Email Message
msg = MIMEMultipart()
msg['Subject'] = 'MaxAir Database Backup'
me = FROM
to = [TO]
Body = 'Database Backup.'
msg['From'] = me
msg['To'] =  ', '.join(to)
msg.preamble = 'Database Backup'
Body = MIMEText(Body) # convert the body to a MIME compatible string
msg.attach(Body) # attach it to your main message
# add zip file as an attachment
with open(zipfname,'rb') as file:
    msg.attach(MIMEApplication(file.read(), Name=zipfname))

# Send the email via our own SMTP server.
try:
    if PORT == 465 :
        server = smtplib.SMTP_SSL(HOST, PORT)
    else :
        server = smtplib.SMTP(HOST, PORT)
    #server.set_debuglevel(1)
    server.login(USER, PASS)
    server.sendmail(FROM, TO, msg.as_string())
    server.quit()
except:
    print(bc.fail + (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - ERROR Sending Email Message")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Email Sent")
print("------------------------------------------------------------------")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Moving Archile file to - " + destination)
print("------------------------------------------------------------------")
cmd = "mv ./" + zipfname + " " + destination
os.system(cmd)
print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Archive Moved")
print("------------------------------------------------------------------")

print(bc.blu + (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + bc.wht + " - Database Backup Script Ended \n")
print("------------------------------------------------------------------")

