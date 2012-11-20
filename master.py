import os
import json
import boto
from uuid import uuid4
import thread
from boto.sqs.message import Message
import logging
import time
import misc

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
VISIBILITY_TIMEOUT = 3 
worker_dict = {}
master_dict = {'host':['master_hostname','master_hostipaddress','clustername']}

sqs_conn = boto.connect_sqs()

def build_hosts(newhost):
   misc.run("echo '%s' >> /etc/hosts" % (newhost))
   misc.run("cat /etc/hosts > /tmp/hosts")
   return 1

def build_cert():
   misc.run('ssh-keygen -t dsa -N "" -f /tmp/id_dsa')
   return 1

def remove_cert():
   misc.run('rm -rf /tmp/id_dsa*')
   return 1
   
def read_queue():
   #request_queue = sqs_conn.create_queue(master_dict['host'][2])
   request_queue = sqs_conn.create_queue('master_ea081736-0667-4e56-a2cc-61be41d305c6')
   message = request_queue.read(VISIBILITY_TIMEOUT)
   if message is not None:
      #handle_message
      get_message = message.get_body()
      log.debug("Get Message: %s" % (get_message))
      
      #recv message from new worker, read message and send new hosts information
      if get_message.startswith("MASTER"):
         host_name = get_message.split('|')[1]
         host_ip = get_message.split('|')[2]
         log.debug("Get slave hostname/hostipaddress %s %s" %(host_name, host_ip))

         worker_dict_size = len(worker_dict)
         worker_alias = 'node0' + str(worker_dict_size + 1)
         worker_dict[worker_dict_size+1] = [host_name, host_ip, worker_alias]
      
         #build hosts file, send hosts file, sge config file
         ret_code = build_hosts("%s	%s	%s" % (host_ip, host_name, worker_alias))
         if ret_code:
            f = open('/tmp/hosts','r')
            hosts = ''
            i = 0
            while 1:
               line = f.readline()
               i = i + 1
               if not line:
                  break
               hosts = hosts + line
            log.debug("final hosts: %s" % (hosts))
            f.close()
         else:
            log.error("Error retrieving hostname")
            return None
         
         remove_cert()
         ret_code = build_cert()
         if ret_code:
            f = open('/tmp/id_dsa', 'r')
            cert = ''
            while 1:
               line = f.readline()
               if not line:
                  break
               cert = cert + line
            log.debug("final cert: %s" % (cert))
            f.close()
         else:
            log.error("Error retrieving cert")
            return None

         request_queue.delete_message(message)
         log.debug("Delete Message from SQS")
         log.debug(worker_dict)
         #new hosts message send to worker nodes (worker nodes have their queue, worker's iid)
         for j in range(len(worker_dict)):
	        worker_queue_name = 'worker_'+ worker_dict[j+1][0] #worker_hostname
	        log.debug('worker queue name: %s' % (worker_queue_name))

	        new_message = Message()
	        setup_hosts_msg = "setup_hosts|%s" % (hosts)
	        new_message.set_body(setup_hosts_msg)
	        request_queue = sqs_conn.create_queue(worker_queue_name)
	        log.debug(setup_hosts_msg)
	        status = request_queue.write(new_message)


                new_message = Message()
                setup_cert_msg = "setup_cert|%s" % (cert)
                new_message.set_body(setup_cert_msg)
                request_queue = sqs_conn.create_queue(worker_queue_name)
                log.debug(setup_cert_msg)
                status = request_queue.write(new_message)

   else:
      log.debug("SQS Server Message 0 :)")
      pass

if __name__ == "__main__":
   while True:
      thread.start_new_thread(read_queue,())
      time.sleep(10)
