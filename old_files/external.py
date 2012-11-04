#!/usr/bin/python

import time
import sys
import boto

print "*****************"
print sys.argv[1]
sqs=boto.connect_sqs()
q=sqs.get_queue('my_message_pump')
message=q.read()
q.delete_message(message)
print "*****************"

time.sleep(10)
print "asjdflaskfjajsdfnajsdfljaksdfalsdnflakjsfd"
