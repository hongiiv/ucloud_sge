import sys
import os
import subprocess
import datetime
import re
import time
from xml.etree import ElementTree

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
         print "autoscaling start: %s %d"%(delta.seconds, queue_size)
      else:
         print "not yet: %s %d"%(delta.seconds, queue_size)
   print '------'

if __name__ == "__main__":
    while True:
        main()
        time.sleep(2)

