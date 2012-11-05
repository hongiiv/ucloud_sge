import time
import boto
from boto.sqs.message import Message
from uuid import uuid4
import sqlite3
import logging

INSTANCE_QUEUE = 'instance_queue'
VOLUME_QUEUE = 'volume_queue'
#Database name & instance/volume table
SQLITE_ADMIN = 'genome_admin'

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
logging.warning('is when this event was logged.')

def update_db(productid, totnodecount):
  try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = "update table_product set totnodecount='%s' where productid='%s'"%(str(totnodecount), productid)
      log.debug(SQL)
      cursor.execute(SQL)
      cursor.close()
      db.commit()
      db.close()
  except sqlite3.OperationalError:
      log.debug("Connot connect database")
   

def delete_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN,timeout=1)
      cursor = db.cursor()
      try:
         #cursor.execute("delete from genome_admin")
         cursor.execute("DROP TABLE IF EXISTS table_instance")
         cursor.execute("DROP TABLE IF EXISTS table_volume")
         cursor.execute("DROP TABLE IF EXISTS table_product")
         db.commit()
         db.close()
         print "Database was deleted"
         break
      except sqlite3.OperationalError:
         print "database locked"

def create_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      try:
         cursor.execute("create table table_instance (displayname, userid, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, date_queued, date_runqueue, date_process_start, date_process_end, date_exception, status_code, clustername, clusteruuid, vm_tot_count, volume_list, private_address, public_address, password, virtual_machine_id)")
         cursor.execute("create table table_volume (displayname_volume, displayname_instance, date_queued, date_runqueue, date_process_start, date_process_end, date_exception, status_code, diskofferingid, virtual_machine_id, clustername, clusteruuid, zoneid, volume_id)")
         cursor.execute("create table table_product (productid, productcode, userid, clustername, status, totnodecount, nodecount, nodeinfo, volumeinfo, datecreate, datefinish, dateterminate,totvolumecount, volumecount)")
         db.commit()
         db.close()
         print "Database created"
         break
      except sqlite3.OperationlError:
         print "database locked"

def insert_db_instance(displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date, cluster_name, cluster_uuid, vm_tot_count):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      datas = (displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date,"","","","","100", cluster_name, cluster_uuid, vm_tot_count,"","","","","")
      try:
         cursor.execute("insert into table_instance values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datas)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully inserted table_instance"
         break
      except sqlite3.OperationlError:
         print "database locked"

def insert_db_volume(displayname_volume, displayname_instance, nowdate, clustername, clusteruuid, zoneid):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      #datas = (displayname_volume, displayname_instance, nowdate, clustername, clusteruuid, "", "","200","","","","", zoneid, "")
      datas = (displayname_volume, displayname_instance, nowdate, "","","","","200","","", clustername, clusteruuid, zoneid,"")
      print datas
      try:
         cursor.execute("insert into table_volume values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datas)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully inserted table_volume"
         break
      except sqlite3.OperationalError:
         print "database locked"

def insert_db_product(productid, productcode, userid, clustername, status, totnodecount, nodecount, nodeinfo, volumeinfo, datecreate, datefinish, dateterminate, totvolumecount, volumecount):
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      datas = (productid, productcode, userid, clustername, status, totnodecount, nodecount, nodeinfo, volumeinfo, datecreate, datefinish, dateterminate, totvolumecount, volumecount)  
      try:
         cursor.execute("insert into table_product values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datas)
         cursor.close()
         db.commit()
         db.close()
         print "Successfully inserted table_prduct"
         break
      except sqlite3.OperationalError:
         print "database locked"

def select_db():
   while(1):
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      try:
         cursor.execute("select * from table_instance")
         print "----------------------------------------------------------------------"
         print "Displayname\tUser\tServiceID\tTemplate\tDisk\tzone\tusage\tqueued\trunqueue\tprocess_start\tprocess_end\texcep\tcode\tculstername\tclusteruuid\tvmtotalcounti\taddress\tpw\tvmid"
         print "----------------------------------------------------------------------"
         for row in cursor:
            print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[17],row[19], row[20])
         cursor.close()
         db.commit()

         cursor = db.cursor()
         cursor.execute("select * from table_volume")
         print "----------------------------------------------------------------------"
         print "volumename\tinstancename\tqueued\trunqueue\tprocess_start\tprocess_end\texcept\tcode\tdiskofferingid\tvm_id\tclustername\tclusteruuid\tzoneid\tvolumeid"
         print "----------------------------------------------------------------------"
         for row in cursor:
            print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
         cursor.close()
         db.commit()

         cursor = db.cursor()
         cursor.execute("select * from table_product")
         print "----------------------------------------------------------------------"
         print "productid\tproductcode\tuserid\tclustername\tstatus\ttotnodecount\tnodecount\tnodeinfo\tvolumeinfo\tdatecreate\tdatefinish\tdateterminate\ttotalvol\tvolcount"
         print "----------------------------------------------------------------------"
         for row in cursor:
            print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13])
         cursor.close()
         db.commit()

         db.close()
         break
      except sqlite3.OperationalError:
         print "database locked"

def insert_message_instance(serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, user_name, vm_tot_count, displayname, now_date, cluster_name, cluster_uuid):
   now = time.localtime()
   queued_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
   request_queue_instance_message = '{"serviceofferingid":"%s","templateid": "%s","diskofferingid":"%s","zoneid":"%s","usageplantype":"%s","user_name":"%s","queued_date":"%s","displayname":"%s", "clustername":"%s","clusteruuid":"%s", "vm_tot_count":"%s"}'%(serviceofferingid,templateid,diskofferingid, zoneid, usageplantype, user_name, queued_date, displayname, cluster_name, cluster_uuid, vm_tot_count)
   print request_queue_instance_message
   sqs_conn = boto.connect_sqs()
   request_queue_instance = sqs_conn.create_queue(INSTANCE_QUEUE)
   new_message = Message()
   new_message.set_body(request_queue_instance_message)
   status = request_queue_instance.write(new_message)
   if status is not None:
      insert_db_instance(displayname, user_name, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, queued_date, cluster_name, cluster_uuid, vm_tot_count)
      return 1
   else:
      return 2

def insert_message_volume(displayname_volume, displayname_instance, nowdate, clustername, clusteruuid, zoneid):
   now = time.localtime()
   queued_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
   sqs_conn = boto.connect_sqs()
   request_queue_volume = sqs_conn.create_queue(VOLUME_QUEUE)
   request_queue_volume_message = '{"displayname_volume":"%s","displayname_instance":"%s", "now_date":"%s", "clustername":"%s", "clusteruuid":"%s", "zoneid":"%s"}'%(displayname_volume, displayname_instance, nowdate, clustername, clusteruuid, zoneid)
   print request_queue_volume_message
   new_message = Message()
   new_message.set_body(request_queue_volume_message)
   status = request_queue_volume.write(new_message)
   if status is not None:
      insert_db_volume(displayname_volume,displayname_instance, nowdate, clustername, clusteruuid, zoneid)
      return 1
   else:
      return 2
   
def run_request(node_count, cluster_name, autoscale, user_account):
   #master_serviceofferingid = '94341d94-ccd4-4dc4-9ccb-05c0c632d0b4' #CPU, Memory
   #slave_serviceofferingid = '94341d94-ccd4-4dc4-9ccb-05c0c632d0b4' #CPU, Memory
   master_serviceofferingid = 'c504e367-20d6-47c6-a82c-183b12d357f2'
   slave_serviceofferingid = 'c504e367-20d6-47c6-a82c-183b12d357f2'
   #master_templateid = 'e24c0475-07ae-441c-acdd-e01ab5f0a732'
   #slave_templateid = 'e24c0475-07ae-441c-acdd-e01ab5f0a732'
   master_templateid = '10baa5f8-a790-4f37-b9e6-b18453fda37b'
   slave_templateid = '10baa5f8-a790-4f37-b9e6-b18453fda37b'
   diskofferingid = 'cc85e4dd-bfd9-4cec-aa22-cf226c1da92f'
   #diskofferingid = '277d1cea-d51a-4570-af16-0b271795d2a0'
   zoneid = 'eceb5d65-6571-4696-875f-5a17949f3317'
   usageplantype = 'hourly'
   user_account = user_account
   now = time.localtime()
   now_date = "%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
   vm_counts = "2"
   cluster_uuid = str(uuid4())

   node_count = int(node_count)

   #product table update
   insert_db_product(cluster_uuid, node_count, user_account, cluster_name, "100", node_count, "0", "", "", now_date, "", "","5","0")

   for j in range(node_count):
      displayname_instance = str(uuid4())
      #vm_tot_count = '%d of %d'%(j+1, node_count)
      vm_tot_count = '%d'%(j+1)
      if j == 1: #master node
         result_instance = insert_message_instance(master_serviceofferingid, master_templateid, diskofferingid, zoneid, usageplantype, user_account, vm_tot_count, displayname_instance, now_date, cluster_name, cluster_uuid)
         #total 5 volume in master node
         for i in range(5):
            displayname_volume = str(uuid4())
            result_volume = insert_message_volume(displayname_volume, displayname_instance,  now_date, cluster_name, cluster_uuid, zoneid)
         if result_instance == 1:
            print "Message inserted"
         else:
            print "Message fail"
      else: #slave nodes
         result_instance = insert_message_instance(slave_serviceofferingid, slave_templateid, diskofferingid, zoneid, usageplantype, user_account, vm_tot_count, displayname_instance, now_date, cluster_name, cluster_uuid)   
         if result_instance == 1:
            print "Message inserted"
         else:
            print "Message fail"


#if __name__ == "__main__":
   #run_request('2','bio_cluster','yes','hongiiv') #node_counts, cluster_name, autoscale, user_account
