
#!/usr/bin/python
import sys
import os
import subprocess
import datetime
import re
import time
from xml.etree import ElementTree
import logging
import boto
from boto.sqs.message import Message

AUTOSCALE_QUEUE = 'autoscale_queue'
cluster_uuid = 'c9863ed4-0e10-4692-83d0-f2e56fd98082'

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
logging.warning('is when this event was logged.')

def insert_message_instance():
   now = time.localtime()
   autoscale_queue_instance_message = '{"clusteruuid":"%s"}'%(cluster_uuid)
   log.debug(autoscale_queue_instance_message)
   sqs_conn = boto.connect_sqs()
   autoscale_queue_instance = sqs_conn.create_queue(AUTOSCALE_QUEUE)
   new_message = Message()
   new_message.set_body(autoscale_queue_instance_message)
   status = autoscale_queue_instance.write(new_message)
   if status is not None:
      log.debug('cool :)')
   else:
      log.debug('bad :(')

def main():
   qstat_cmd = "qstat -xml -u '*'"
   qstat_proc = subprocess.Popen(qstat_cmd,
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      env=os.environ)
   stdout, stderr = qstat_proc.communicate()

   try:
      root = ElementTree.fromstring(stdout)
   except:
      parse_error(qstat_cmd, stdout, stderr)

   queue_info = root.find('job_info')
   if queue_info is None:
      parse_error(qstat_cmd, stdout, stderr)

   queue_size = len(queue_info)

   for job_list in queue_info:
      job = {}
      job['id'] = job_list.find("JB_job_number").text
      stime = datetime.datetime.strptime(job_list.find("JB_submission_time").text, "%Y-%m-%dT%H:%M:%S")
      job['submitted'] = stime.strftime("%Y-%m-%d %H:%M:%S.%f")
      re = "%s %s %s"%(job['id'], job['submitted'], datetime.datetime.today())
      delta = datetime.datetime.now() - stime
      if delta.seconds > 120:
         log.debug("autoscaling start: %s %d"%(delta.seconds, queue_size))
         insert_message_instance()
         log.debug('Wait for new instance....')
         #20 min sleep for new instance
         for i in range(1200):
            time.sleep(1)
            percent = i/12
            sys.stdout.write("\r%d%%" %percent)
            sys.stdout.flush()
         break
      else:
         log.debug("not yet: %s %d"%(delta.seconds, queue_size))

if __name__ == "__main__":
    while True:
        main()
        time.sleep(2)

   