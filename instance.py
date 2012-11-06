import CloudStack
import pexpect
import time
import os
import json
import boto
from uuid import uuid4
#import thread
from boto.sqs.message import Message
import sqlite3
import deploy_product
import sys
import base64
import logging

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
logging.warning('is when this event was logged.')

REQUEST_QUEUE = 'autoscale_queue'
MAX_TRY = 10 #if failed deploy virtual machine we will try 10 times
VISIBILITY_TIMEOUT = 1500 # 25 min
KT_HOST = 'https://api.ucloudbiz.olleh.com/server/v1/client/api'
KT_APIKEY = 'iW59r_QY7T07T-fXY7FH8IRsYbgJ6b-fV4pvCFsYkbx6ArMGFhaL4-sEz7zbpCNUA1I6ovcLIH2dTbXVp34mAA'
KT_SECRET = 'ttteX3ygXMJBHPinj3zVOuHg1WCq3tqX014elUPkMryMhiGP3OjcBijKPkMA7N9DGCZY5RvO9aLMuOh6SfY9dQ'
SQLITE_ADMIN = 'genome_admin'
deploy_server_ip = '172.27.121.128'

def deploy_start_check(productid):
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select totnodecount, nodecount from table_product where productid='%s'"%(productid)
      log.debug(SQL)
      cursor.execute(SQL)
      for row in cursor:
         totnodecount = row[0]
         nodecount = row[1]
      log.debug("Total Nodes: %s Now boot Nodes: %s"%(totnodecount, nodecount))
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Cannot connect database")

   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select totvolumecount, volumecount from table_product where productid='%s'"%(productid)
      log.debug(SQL)
      cursor.execute(SQL)
      for row in cursor:
         totvolumecount = row[0]
         volumecount = row[1]
      log.debug("Total Volumes: %s Now create Volumes: %s"%(totvolumecount, volumecount))
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
      log.debug("Cannot connect database")
      
def update_db_product(productid):
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "select nodecount from table_product where productid='%s'"%(productid)
      log.debug(SQL)
      cursor.execute(SQL)
      for row in cursor:
         nodecount = int(row[0])
      nodecount = nodecount + 1
      cursor.close()
      db.commit()

      log.debug("Now will update total Nodes: %s"%(nodecount))

      cursor = db.cursor()
      SQL = "update table_product set nodecount='%s' where productid='%s'"%(str(nodecount), productid)
      log.debug(SQL)
      cursor.execute(SQL)
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Connot connect database")
   
   dstart = deploy_start_check(productid)
   dstart = json.loads(dstart)
   status = dstart['status']
   product_id = dstart['productid']

   if status == "1":
      log.debug("Starting deploy product: %s"%(product_id))
      #deploy_result = deploy_product.deploy_run(product_id)
      deploy_result = deploy_product.deploy_run_autoscale(product_id)
      if deploy_result == "1":
         log.debug("autoscale success: %s"%(product_id))
      else:
         log.debug("autoscale fail: %s"%(product_id))
   elif status == "2":
      log.debug("Your instance or volume are attached but deploy not yet: %s"%(product_id))

def update_db_103(n_date, displayname, code, private_address, password, virtual_machine_id):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "update table_instance set status_code='%s', date_process_end='%s', private_address='%s', password='%s', virtual_machine_id='%s' where displayname='%s'"%(code,n_date, private_address, password, virtual_machine_id, displayname)
      log.debug(SQL)
      try:
         cursor.execute(SQL)
         cursor.close()
         db.commit()
         db.close()
         log.debug("State update %s: %s"%(displayname, code))
         break
      except sqlite3.OperationalError:
         log.debug("Cannot connect database")

def update_db(n_date, displayname, code):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()

      if code == "101":
         SQL = "update table_instance set status_code='%s', date_process_start='%s', date_queued='%s' where displayname='%s'"%(code, n_date, n_date, displayname)
      elif code == "102":
         SQL = "update table_instance set status_code='%s', date_runqueue='%s' where displayname='%s'"%(code, n_date, displayname)
      elif code == "501":
         SQL = "update table_instance set status_code='%s', date_exception='%s' where displayname='%s'"%(code, n_date, displayname)
      elif code == "502":
         SQL = "update table_instance set status_code='%s', date_exception='%s' where displayname='%s'"%(code, n_date, displayname)

      log.debug(SQL)

      try:
         cursor.execute(SQL)
         cursor.close()
         db.commit()
         db.close()
         log.debug("State update: %s"%(code))
         break
      except sqlite3.OperationalError:
         log.debug("Cannot connect database")

def launch_vm(m):
   cloudstack = CloudStack.Client(KT_HOST, KT_APIKEY, KT_SECRET)
   message_data = json.loads(m.get_body())

   slave_userdata='''#!/bin/bash
python <<EOF
import os
import time
while True:
   command_external = os.system("/usr/bin/wget ftp://%s/%s_slave.sh -O /tmp/%s_slave.sh")
   if os.path.isfile("/tmp/%s_slave.sh") and os.path.getsize("tmp/%s_slave.sh") > 0:
      command_external = os.system("/bin/bash /tmp/%s_slave.sh")
      if not command_external == 0:
         print ":( error during external command from deploy server"
      break
   else:
      time.sleep(5)
EOF
'''%(deploy_server_ip, message_data['clusteruuid'], message_data['clusteruuid'], message_data['clusteruuid'], message_data['clusteruuid'], message_data['clusteruuid'])


   userdata = slave_userdata

   userdata = base64.b64encode(userdata)
   now = time.localtime()
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
      'userdata': userdata
   })

   if reservation.has_key('errorcode'):
      log.debug("Error during deployVirtualMachine: %s"%(message_data['displayname']))
      #db_update/message_update
      now = time.localtime()
      now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
      update_db(now_date,message_data['displayname'],"501")
      #this message will be apeared 1 hour later
      log.debug("Eorror code: %s"%(reservation['errorcode']))
      log.debug("Error message: %s"%(reservation['errortext']))
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
            log.debug("Error during deployVirtualMachine's asyncstatus job: %s"%(message_data['displayname']))
            log.debug("Eorror code: %s"%(asyncstatus['errorcode']))
            log.debug("Error message: %s"%(asyncstatus['errortext']))
            time.sleep(20)
         elif asyncstatus['jobstatus'] == 1:
            password = asyncstatus['jobresult']['virtualmachine']['password']
            ipaddress = asyncstatus['jobresult']['virtualmachine']['nic'][0]['ipaddress']
            virtual_machine_id = asyncstatus['jobresult']['virtualmachine']['id']
            log.debug("VM was successfully created: %s %s"%(ipaddress, password))
            result ='{"rescode":"1","ipaddress": "%s","password":"%s"}'%(ipaddress,password)

            #db_update/message_update
            now = time.localtime()
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db_103(now_date,message_data['displayname'],"103", ipaddress, password, virtual_machine_id)
            update_db_product(message_data['clusteruuid'])
            break
         elif asyncstatus['jobstatus'] == 2:
            result ='{"rescode":"2"}'
            #db_update/message_update
            log.debug("Error during deployVirtualMachine's asyncstatus job: %s - result job status is 2"%(message_data['displayname']))
            now = time.localtime()
            now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            update_db(now_date,message_data['displayname'],"502")
            break
         else:
            time.sleep(20)

   log.debug("deployVirtualMachine job end: %s"%(message_data['displayname']))
   log.debug(result)
   return result

def read_queue():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
   message = request_queue.read(VISIBILITY_TIMEOUT) #3600 sec, 1 hour
   if message is not None:
      log.debug("Get Message from SQS: %s"%(message.get_body()))
      run(message)
   log.debu(':(((((((((')
   
def run(message, m):
   try_count = 0
   while True:
      if try_count != MAX_TRY:
         launch_result = launch_vm(m)
         result = json.loads(launch_result)
         log.debug(result)
         if result['rescode'] == '1':
            sqs_conn = boto.connect_sqs()
            request_queue = sqs_conn.create_queue(REQUEST_QUEUE)
            request_queue.delete_message(message)
            log.debug("Delete Message from SQS")
            return 1
            break
         elif result['rescode'] == '2':
            log.debug("Read SQS job and run it but fail :(")
            try_count = try_count +1
      else:
         log.debug("This message total %d try but fail, message will be back"%(try_count))
         return 2
         break
