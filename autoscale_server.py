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
import sys
import base64
import logging
import instance
import message_server

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
logging.warning('is when this event was logged.')

AUTOSCALE_QUEUE = 'autoscale_queue'
SQLITE_ADMIN = 'genome_admin'
VISIBILITY_TIMEOUT = 1500 # 25 min

def read_queue():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue(AUTOSCALE_QUEUE)
   message = request_queue.read(VISIBILITY_TIMEOUT) #3600 sec, 1 hour

   #create autoscale message
   if message is not None:
      log.debug("Get Message from SQS: %s"%(message.get_body()))
      queue_message = json.loads(message.get_body())
      clusteruuid = queue_message['clusteruuid']

      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      try:
         SQL = "select * from table_instance where clusteruuid='%s'"%(clusteruuid)
         cursor.execute(SQL)
         log.debug(SQL)
         row_count = 0

         for row in cursor:
            row_count = row_count + 1

            now = time.localtime()
            queued_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            displayname = str(uuid4())

            message_dict = {
               'serviceofferingid':'94341d94-ccd4-4dc4-9ccb-05c0c632d0b4',
               'templateid':'10baa5f8-a790-4f37-b9e6-b18453fda37b',
               'diskofferingid':'cc85e4dd-bfd9-4cec-aa22-cf226c1da92f',
               'zoneid':'eceb5d65-6571-4696-875f-5a17949f3317',
               'usageplantype':'hourly',
               'user_name':row[1],
               'queued_date':queued_date,
               'displayname':displayname,
               'clustername':row[13],  
               'clusteruuid':row[14],
               'vm_tot_count':row_count+1,
            }

         m = Message()
         m.set_body(json.dumps(message_dict)) 

         message_server.insert_db_instance(displayname, row[1], message_dict['serviceofferingid'], message_dict['templateid'], message_dict['diskofferingid'], message_dict['zoneid'], message_dict['usageplantype'], message_dict['queued_date'], message_dict['clustername'], message_dict['clusteruuid'], message_dict['vm_tot_count'])
         message_server.update_db(message_dict['clusteruuid'], message_dict['vm_tot_count'])
         instance.run(message, m)

         cursor.close()
         db.commit()
         db.close()
      except sqlite3.OperationalError:
         log.debug("Database locked")

#if __name__ == "__main__":
while True:
   thread.start_new_thread(read_queue,())
   time.sleep(10)
