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

REQUEST_QUEUE = 'volume_queue'
MAX_TRY = 10 #if failed deploy virtual machine we will try 10 times
VISIBILITY_TIMEOUT = 1500 # 25 min
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

def deploy_start_check(productid):
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select totnodecount, nodecount from table_product"
      cursor.execute(SQL)
      for row in cursor:
         totnodecount = row[0]
         nodecount = row[1]
      print "debug nodes>>> %s .... %s"%(totnodecount, nodecount)
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      print ":( deploy_start_check database locked"
   
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select totvolumecount, volumecount from table_product"
      cursor.execute(SQL)
      for row in cursor:
         totvolumecount = row[0]
         volumecount = row[1]
      print "debug volumes>>> %s ... %s"%(totvolumecount, volumecount)
      cursor.close()
      db.commit()
      db.close()
      if int(totnodecount) == int(nodecount) and int(totvolumecount) == int(volumecount):
         complete_message = '{"status":"1", "productid":"%s"}'%(productid)
         return complete_message
      else:
         complete_message = '{"status":"2", "productid":"%s"}'%(productid)
         return complete_message
   except sqlite3.OperationalError:
      print "database locked"

def update_db_product(productid):
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select volumecount from table_product"
      cursor.execute(SQL)
      for row in cursor:
         volumecount = int(row[0])
      volumecount = volumecount + 1
      cursor.close()
      db.commit()

      cursor = db.cursor()
      SQL = "update table_product set volumecount='%s' where productid='%s'"%(str(volumecount), productid)
      print SQL
      cursor.execute(SQL)
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      print "database locked"

   dstart = deploy_start_check(productid)
   dstart = json.loads(dstart)
   status = dstart['status']
   product_id = dstart['productid']
   if dstart == "1":
      print "starting deploy product: %s"%(product_id)
   elif dstart == "2":
      print "deploy not yet: %s"%(product_id)


def update_db_103(n_date, displayname_volume, code, volumeid):
   while(1):
      try:
         db = sqlite3.connect(SQLITE_ADMIN)
         cursor = db.cursor()
         SQL = "update table_volume set status_code='%s', date_process_end='%s', volume_id='%s' where displayname_volume='%s'"%(code, n_date, volumeid, displayname_volume)
         print SQL
         cursor.execute(SQL)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully updated db - %s"%(code)
         break
      except sqlite3.OperationalError:
         print "database locked"

def update_db(n_date, displayname_volume, code):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()

      if code == "101":
         SQL = "update table_volume set status_code='%s', date_process_start='%s', date_queued='%s' where displayname_volume='%s'"%(code, n_date, n_date, displayname_volume)
      elif code == "102":
         SQL = "update table_volume set status_code='%s', date_runqueue='%s' where displayname_volume='%s'"%(code, n_date, displayname_volume)
      elif code == "501":
         SQL = "update table_volume set status_code='%s', date_exception='%s' where displayname_volume='%s'"%(code, n_date, displayname_volume)
      elif code == "502":
         SQL = "update table_volume set status_code='%s', date_exception='%s' where displayname_volume='%s'"%(code, n_date, displayname_volume)

      print SQL

      try:
         cursor.execute(SQL)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully updated db - %s"%(code)
         break
      except sqlite3.OperationalError:
         print "database locked"

def create_volume(message):
   cloudstack = CloudStack.Client(KT_HOST, KT_APIKEY, KT_SECRET)
   message_data = json.loads(message.get_body())

   now = time.localtime()
   now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)

   #db_update/message_update
   update_db(now_date, message_data['displayname_volume'],"101")

   reservation = cloudstack.createVolume({
      'name': message_data['displayname_volume'],
      #'diskofferingid': '670d225c-2dd8-48e1-ac51-d9ab45aa64a0',
      'diskofferingid': '1ca340fd-2cd2-419d-a07e-a506bfdbad2b',
      'zoneid' : message_data['zoneid'],
   })

   if reservation.has_key('errorcode'):
      print '>>>error during resource reservation, createVolume %s >> 501'%(message_data['displayname_volume'])
      #db_update/message_update
      now = time.localtime()
      now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
      update_db(now_date, message_data['displayname_volume'], "501")
      #this message will be apeared 1 hour later
      print '[createVolume] Resquest fail / message will be back : %s %s'%(reservation['errorcode'],reservation['errortext'])
      result ='{"rescode":"2"}'
   else:
      jobid = reservation['jobid']
      now = time.localtime()
      now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
      update_db(now_date, message_data['displayname_volume'], "102")

      while True:
         asyncstatus = cloudstack.queryAsyncJobResult({
            'jobid':jobid
         })

         if asyncstatus.has_key('errorcode'):
            print '[asyncstatus_error01] Resquest fail but i love u: %s %s'%(asyncstatus['errorcode'],asyncstatus['errortext'])
            time.sleep(5)
         elif asyncstatus['jobstatus'] == 1:
            #password = asyncstatus['jobresult']['virtualmachine']['password']
            #ipaddress = asyncstatus['jobresult']['virtualmachine']['nic'][0]['ipaddress']
            #virtual_machine_id = asyncstatus['jobresult']['virtualmachine']['id']
            #print "[deployvirtualmachine] VM was successfuly created %s %s"%(ipaddress, password)
            #result ='{"rescode":"1","ipaddress": "%s","password":"%s"}'%(ipaddress,password)
            result = '{"rescode":"1"}'

            #db_update/message_update
            now = time.localtime()
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db_103(now_date, message_data['displayname_volume'], "103", asyncstatus['jobresult']['volume']['id'])
            update_db_product(message_data['clusteruuid'])
            break
         elif asyncstatus['jobstatus'] == 2:
            result ='{"rescode":"2"}'
            #db_update/message_update
            print '[asyncstatus_error02] job file'
            now = time.localtime()
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db(now_date,message_data['displayname_volume'],"502")
            break
         else:
            time.sleep(5)

   print 'done'
   return result

def read_queue():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue('volume_queue')
   message = request_queue.read(VISIBILITY_TIMEOUT)
   if message is not None:
      print "Get message, read it"
      print message.get_body()
      run(message)
   else:
      pass
   
def run(message):
   try_count = 0
   while True:
      if try_count != MAX_TRY:
         launch_result = create_volume(message)
         result = json.loads(launch_result)
         if result['rescode'] == '1':
            sqs_conn = boto.connect_sqs()
            request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
            request_queue.delete_message(message)
            print "Delete message from volume queue :)"
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
         return 2
         break

#if __name__ == "__main__":
while True:
   thread.start_new_thread(read_queue,())
   ###print "I will read a queue"
   time.sleep(5)
