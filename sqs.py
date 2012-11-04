import boto
import time
import autoscale
from boto.sqs.message import Message
import thread
import datetime
from subprocess import *


now = time.localtime()
queue_name = "%04d-%02d-%02d-%02d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,now.tm_sec)
#queue_name = 'my_message_pump'
viztime=20*60

sqs_conn = boto.connect_sqs()
#request_queue = sqs_conn.create_queue(queue_name,viztime)
request_queue = sqs_conn.create_queue(queue_name,10)

#write message -given virtual machine
vm_count = 2
for i in range(0,2):
   m = Message()
   m.set_body('vm_%d'%i)
   request_queue.write(m)

id = 0
while True:
   time.sleep(3)
   num_queue = request_queue.count()
   print ">>>>>>>>>number of messages %s<<<<<<<<<<<<"%(num_queue)
   if num_queue == 0:
      print 'total message are zero'
      #sqs_conn.delete_queue(request_queue)
   else:
      print "total messages: %d"%(num_queue)
      rs = request_queue.get_messages()
      if len(rs) != 0:
         print "now message: %s"%(rs[0].get_body())
         #do some works
         request_queue.delete_message(rs[0])
