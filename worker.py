import os
import json
import boto
from uuid import uuid4
import thread
from boto.sqs.message import Message
import logging
import time
import urllib
import subprocess
import misc
import sys

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')

VISIBILITY_TIMEOUT = 3
local_hostname = None
local_ipaddress = None
#MASTER_QUEUE = 'master_ea081736-0667-4e56-a2cc-61be41d305c6'
master_queue_name = '%s_master' % sys.argv[1]
#WORKER_QUEUE = None
worker_queue_name = None

def get_hostname():
   try:
      rvm_host = get_rvm_hostname()
      fp = urllib.urlopen('http://%s/latest/meta-data/local-hostname' % rvm_host)
      worker_hostname = fp.read()
      fp.close()
      return worker_hostname
   except IOError:
	  pass

def get_rvm_hostname():
   ret_code = misc.run("grep 'option dhcp-server-identifier' /var/lib/dhcp3/dhclient.eth0.leases | tail -1 | awk '{print $NF}' | tr '\;' ' ' | tr -d ' ' > /tmp/hostname")
   if ret_code:
      f = open('/tmp/hostname','r')
      rvm_host = f.readline()
      f.close()
      return rvm_host 
   else:
      log.error("Error retrieving host name")
      return None

def wake_up_message_send():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue(master_queue_name)
   rvm_host = get_rvm_hostname()
   if True:
      for i in range(0, 5):
         try:
            log.debug("Attempted to get hostname")
            fp = urllib.urlopen('http://%s/latest/meta-data/local-hostname' % rvm_host)
            local_hostname = fp.read()
            fp.close()
            if local_hostname:
               break
         except IOError:
            pass

      for i in range(0, 5):
         try:
            log.debug("Attempted to get hostip")
            fp = urllib.urlopen('http://%s/latest/meta-data/local-ipv4' % rvm_host)
            local_ipaddress = fp.read()
            fp.close()
            if local_ipaddress:
               break
         except IOError:
            pass

   new_message = Message()
   msg = "MASTER|%s|%s" % (local_hostname, local_ipaddress)
   new_message.set_body(msg)
   status = request_queue.write(new_message)
   log.debug("sending message '%s'" % msg)

def read_queue():
   sqs_conn = boto.connect_sqs()
   request_queue = sqs_conn.create_queue(worker_queue_name)
   message = request_queue.read(VISIBILITY_TIMEOUT)
   if message is not None:
      #handle_message
      get_message = message.get_body()
      msg = get_message.split('|')[1]
      log.debug("Get Message: %s" % (msg))

      if get_message.startswith("setup_hosts"):
         print get_message
         misc.run("echo %s > /etc/hosts" % (msg))
      elif get_message.startswith("setup_cert"):
         print get_message
         misc.run("echo '%s' > ~/.ssh/authorized_keys" % (msg))
         misc.run("chmod 700 ~/.ssh")
         misc.run("chmod 644 ~/.ssh/authorized_keys")

      request_queue.delete_message(message)
      log.debug("Delete Message from SQS")
   else:
      log.debug("SQS Server - Slave Message 0 :)")
      pass

if __name__ == "__main__":
   wake_up_message_send()
   worker_queue_name = "'%s_worker_'+get_hostname()" % sys.argv[1]
   while True:
      thread.start_new_thread(read_queue,())
      time.sleep(10)
