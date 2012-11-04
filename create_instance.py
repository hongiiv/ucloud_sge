import CloudStack
import pexpect
import time
import os
import json
import boto
from uuid import uuid4
import thread
from boto.sqs.message import Message
import sqlite3

REQUEST_QUEUE = 'developer'
MAX_TRY = 10 #if failed deploy virtual machine we will try 10 times
VISIBILITY_TIMEOUT = 600 # 10 min
KT_HOST = 'https://api.ucloudbiz.olleh.com/server/v1/client/api'
KT_APIKEY = 'iW59r_QY7T07T-fXY7FH8IRsYbgJ6b-fV4pvCFsYkbx6ArMGFhaL4-sEz7zbpCNUA1I6ovcLIH2dTbXVp34mAA'
KT_SECRET = 'ttteX3ygXMJBHPinj3zVOuHg1WCq3tqX014elUPkMryMhiGP3OjcBijKPkMA7N9DGCZY5RvO9aLMuOh6SfY9dQ'
SQLITE_ADMIN = 'genome_admin'
diskofferingid_50 = '1ca340fd-2cd2-419d-a07e-a506bfdbad2b'
diskofferingid_100 = '8ba5e35b-58f7-4cf1-b21c-57029ec2a831'
diskofferingid_150 = '80924d89-4fa6-4c69-8806-d914c2adae33'
diskofferingid_200 = '0578fc8e-887b-41d6-a08e-a69332318ec5'
diskofferingid_250 = 'b772d500-111d-4268-99e8-6cc3e0282df6'
diskofferingid_300 = '670d225c-2dd8-48e1-ac51-d9ab45aa64a0'

def update_db_103(n_date, displayname, code, private_address, password, virtual_machine_id):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()

      SQL = "update genome_admin set status_code='%s', date_process_end='%s', private_address='%s', password='%s', virtual_machine_id='%s' where displayname='%s'"%(code,n_date, private_address, password, virtual_machine_id, displayname)
      
      print SQL

      try:
         cursor.execute(SQL)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully updated db - %s"%(code)
         break
      except sqlite.OperationalError:
         print "database locked"

def update_db(n_date, displayname, code):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()

      if code == "101":
         SQL = "update genome_admin set status_code='%s', date_process_start='%s', date_queued='%s' where displayname='%s'"%(code, n_date, n_date, displayname)
      elif code == "102":
         SQL = "update genome_admin set status_code='%s', date_runqueue='%s' where displayname='%s'"%(code, n_date, displayname)
      elif code == "501":
         SQL = "update genome_admin set status_code='%s', date_exception='%s' where displayname='%s'"%(code, n_date, displayname)
      elif code == "502":
         SQL = "update genome_admin set status_code='%s', date_exception='%s' where displayname='%s'"%(code, n_date, displayname)

      print SQL

      try:
         cursor.execute(SQL)
         #cursor.execute("update genome_admin set (status_code=?, date_process_start=?) where displayname=?", datas) 
         cursor.close()
         db.commit()
         db.close()
         print "Successfully updated db - %s"%(code)
         break
      except sqlite.OperationalError:
         print "database locked"

def preprocessing_vm(virtual_machine_id, display_name, diskofferingid, zoneid):
   cloudstack = CloudStack.Clinet(KT_HOST, KT_APIKEY, KT_SECRET)
   attach_vol = cloudstack.create_volume("Extra_300", diskofferingid, zoneid)



def launch_vm(m):
   cloudstack = CloudStack.Client(KT_HOST, KT_APIKEY, KT_SECRET)
   message_data = json.loads(m.get_body())

   now = time.localtime()
   #now_date = "%02d-%02d-%02d" % (now.tm_mday, now.tm_hour, now.tm_min)
   now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)

   #db_update/message_update
   update_db(now_date, message_data['displayname'],"101")

   reservation = cloudstack.deployVirtualMachine({
      'serviceofferingid': message_data['serviceofferingid'],
      'templateid': message_data['templateid'],
      'diskofferingid':message_data['diskofferingid'],
      'zoneid':message_data['zoneid'],
      'usageplantype':message_data['usageplantype'],
      'displayname': message_data['displayname'],
   })
 
   if reservation.has_key('errorcode'):
      print '>>>error during resource reservation, deployvirtualmachine %s >> 501'%(message_data['displayname'])
      #db_update/message_update
      now = time.localtime()
      now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
      update_db(now_date,message_data['displayname'],"501")
      #this message will be apeared 1 hour later
      print '[deployvirtualmachine] Resquest fail / message will be back : %s %s'%(reservation['errorcode'],reservation['errortext'])
      result ='{"rescode":"2"}'
   else:
      jobid = reservation['jobid']
      vmid = reservation['id']
      #db_update/message_update
      now = time.localtime()
      now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
      update_db(now_date,message_data['displayname'],"102")

      while True:
         asyncstatus = cloudstack.queryAsyncJobResult({
            'jobid':jobid
         })

         if asyncstatus.has_key('errorcode'):
            print '[asyncstatus_error01] Resquest fail but i love u: %s %s'%(asyncstatus['errorcode'],asyncstatus['errortext'])
            time.sleep(5)
         elif asyncstatus['jobstatus'] == 1:
            password = asyncstatus['jobresult']['virtualmachine']['password']
            ipaddress = asyncstatus['jobresult']['virtualmachine']['nic'][0]['ipaddress']
            virtual_machine_id = asyncstatus['jobresult']['virtualmachine']['id']
            print "[deployvirtualmachine] VM was successfuly created %s %s"%(ipaddress, password)
            result ='{"rescode":"1","ipaddress": "%s","password":"%s"}'%(ipaddress,password)

            #db_update/message_update
            now = time.localtime()
            #now_date = "%02d-%02d-%02d" % (now.tm_mday, now.tm_hour, now.tm_min)
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db_103(now_date,message_data['displayname'],"103", ipaddress, password, virtual_machine_id)

            #preprocessing virtual machine
            ###preprocessing_vm(virtual_machine_id, message_data['displayname'],diskofferingid_300, message_data['zoneid'])

            break
         elif asyncstatus['jobstatus'] == 2:
            result ='{"rescode":"2"}'
            #db_update/message_update
            print '[asyncstatus_error02] job file'
            now = time.localtime()
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db(now_date,message_data['displayname'],"502")
            break
         else:
            ###print '.'
            time.sleep(5)

   print 'done'
   return result

def read_queue():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue('developer')
   message = request_queue.read(VISIBILITY_TIMEOUT) #3600 sec, 1 hour
   if message is not None:
      #data = json.loads(message.get_body())
      #data = message.get_body()
      print "Get message, read it"
      print message.get_body()
      run(message)
   ###else:
      ###print "I havn't message, Give me a message :)"
   
def run(message):
   try_count = 0
   while True:
      if try_count != MAX_TRY:
         launch_result = launch_vm(message)
         #print launch_result
         result = json.loads(launch_result)
         if result['rescode'] == '1':
            sqs_conn = boto.connect_sqs()
            request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
            request_queue.delete_message(message)
            print "Delete message from dev queue :("
            return 1
            break
         elif result['rescode'] == '2':
            print 'job fail'
            try_count = try_count +1
      else:
         print try_count
         print "-------------------------------------------"
         print "last job fail"
         print "message will be back 10 min later"
         print "-------------------------------------------"
         #sqs_conn = boto.connect_sqs()
         #request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
         #request_queue.delete_message(m)
         #new_m = Message()
         #new_m.set_body('new')
         #status = request_queue.write(new_m)
         #print "Re-insert queue message (fail) :(" 
         return 2
         break

#if __name__ == "__main__":
while True:
   thread.start_new_thread(read_queue,())
   ###print "I will read a queue"
   time.sleep(5)
