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

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')

def run(cmd, err=None, ok=None):
   """Convenience method for executing a shell command."""
   if err is None:
      err = "--->PROBLEM"
   if ok is None:
      ok = "'%s' command OK" % cmd
   process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   stdout, stderr = process.communicate()
   if process.returncode == 0:
      log.debug(ok)
      return True
   else:
      log.error("%s, running command '%s' returned code '%s' and following stderr: '%s'"% (err, cmd, process.returncode, stderr))
      return False
