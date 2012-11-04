import time
import boto
from boto.sqs.message import Message
from uuid import uuid4
import sqlite3

REQUEST_QUEUE = 'developer'
SQLITE_ADMIN = 'genome_admin'

def delete_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN,timeout=1)
      cursor = db.cursor()
      try:
         cursor.execute("delete from genome_admin")
         db.commit()
         db.close()
         print "Database was deleted"
         break
      except sqlite.OperationlError:
         print "database locked"

def create_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      try:
         cursor.execute("create table genome_admin (displayname, userid, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, date_queued, date_runqueue, date_process_start, date_process_end, date_exception, status_code)")
         db.commit()
         db.close()
         print "Database created"
         break
      except sqlite.OperationlError:
         print "database locked"

def insert_db(displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      datas = (displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date,"","","","","100")
      try:
         cursor.execute("insert into genome_admin values (?,?,?,?,?,?,?,?,?,?,?,?,?)", datas)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully inserted"
         break
      except sqlite.OperationlError:
         print "database locked"

def select_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      try:
         cursor.execute("select * from genome_admin")
         print "Displayname\tUser\tServiceID\tTemplate\tDisk\tzone\tusage\tqueued\trunqueue\tprocess_start\tprocess_end\texcep\tcode"
         for row in cursor:
            print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t"%(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12])
         cursor.close()
         db.commit()
         db.close()
         print "================================="
         break
      except sqlite.OperationalError:
         print "database locked"

def insert_message(serviceofferingid,templateid,diskofferingid,zoneid,usageplantype,user_name,vm_counts,displayname,now_date):
   now = time.localtime()
   queued_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
   request_queue_message = '{"serviceofferingid":"%s","templateid": "%s","diskofferingid":"%s","zoneid":"%s","usageplantype":"%s","user_name":"%s","queued_date":"%s","displayname":"%s"}'%(serviceofferingid,templateid,diskofferingid, zoneid, usageplantype, user_name, queued_date, displayname)
   print request_queue_message
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
   new_message = Message()
   new_message.set_body(request_queue_message)
   status = request_queue.write(new_message)
   if status is not None:
      insert_db(displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date)
      return 1
   else:
      return 2

#if __name__ == "__main__":
serviceofferingid = '94341d94-ccd4-4dc4-9ccb-05c0c632d0b4' #CPU, Memory
templateid = 'e24c0475-07ae-441c-acdd-e01ab5f0a732'
diskofferingid = 'cc85e4dd-bfd9-4cec-aa22-cf226c1da92f'
zoneid = 'eceb5d65-6571-4696-875f-5a17949f3317'
usageplantype = 'hourly'
user_name = 'hongiiv'
vm_counts = 2
now = time.localtime()
now_date = "%02d-%02d-%02d" % (now.tm_mday, now.tm_hour, now.tm_min)
displayname = str(uuid4())

result = insert_message(serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, user_name, vm_counts,displayname,now_date)
if result == 1:
   print "Message inserted"
else:
   print "Message fail"
