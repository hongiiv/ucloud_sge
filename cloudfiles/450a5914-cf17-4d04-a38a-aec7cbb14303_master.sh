#!/bin/bash
export LC_MESSAGE="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"
export LC_ALL="en_US.UTF-8"
echo "export LC_MESSAGES="en_US.UTF-8"" >> /root/.bashrc
echo "export LANG="en_US.UTF-8"" >> /root/.bashrc
echo "export LANGUAGE="en_US:en"" >> /root/.bashrc
echo "export LC_ALL="en_US.UTF-8"" >> /root/.bashrc

export SGE_ROOT="/opt/sge"
export SGE_CELL="default"
export PATH=$PATH:/opt/sge/bin/linux-x64/
echo "export PATH=$PATH:/opt/sge/bin/linux-x64/" >> /root/.bashrc
echo "export SGE_ROOT="/opt/sge"" >> /root/.bashrc
echo "export SGE_CELL="default"" >> /root/.bashrc
echo "export DRMAA_LIBRARY_PATH=/opt/sge/lib/linux-x64/libdrmaa.so.1.0" >> /root/.bashrc

/usr/bin/wget ftp://172.27.121.128/450a5914-cf17-4d04-a38a-aec7cbb14303.config -O /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.config
/usr/bin/wget ftp://172.27.121.128/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts -O /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts
/bin/cat /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts >> /etc/hosts
/usr/bin/wget ftp://172.27.121.128/sge.tar.gz -O /opt/sge.tar.gz
cd /opt
/bin/tar xvfz /opt/sge.tar.gz 
/bin/cp /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.config /opt/sge
/usr/sbin/useradd sgeadmin
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*
cd /opt/sge
./inst_sge -m -x -auto /opt/sge/450a5914-cf17-4d04-a38a-aec7cbb14303.config
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*

apt-get update -y
apt-get install mdadm -y
apt-get install git -y
apt-get install unzip -y
apt-get install mercurial -y
apt-get install csh -y
apt-get install chkconfig -y
#apt-get install postgresql -y
apt-get install nfs-kernel-server nfs-common portmap -y

cd /root
/usr/bin/git clone https://github.com/boto/boto
cd boto
/usr/bin/python setup.py install

/bin/mkdir -p /BIO

#/sbin/mdadm --create --verbose /dev/md0 --level=0 --raid-devices=6 /dev/xvdb /dev/xvdc /dev/xvde /dev/xvdf /dev/xvdg /dev/xvdh
#echo "n" >> swap.in
#echo "p" >> swap.in
#echo "1" >> swap.in
#echo "" >>  swap.in
#echo "" >> swap.in
#echo "w" >> swap.in
#/sbin/fdisk /dev/md0 < swap.in
#/sbin/mkfs.ext3 /dev/md0
#echo "/dev/md0     /BIO     ext3     defaults     0 0" >> /etc/fstab
#mount -a

echo "/BIO *(rw,no_root_squash,no_all_squash,async,no_subtree_check)" >> /etc/exports 
echo "/opt/sge *(rw,no_root_squash,no_all_squash,async,no_subtree_check)" >> /etc/exports

#/usr/sbin/service portmap restart
#/etc/init.d/nfs-kernel-server restart

#install galaxy
cd /BIO
/usr/bin/hg clone https://bitbucket.org/galaxy/galaxy-central
cd /BIO/galaxy-central
wget ftp://172.27.121.128/universe_wsgi.ini -O /BIO/galaxy-central/universe_wsgi.ini
wget ftp://172.27.121.128/galaxy -O /etc/init.d/galaxy
/bin/chmod 755 /etc/init.d/galaxy
/sbin/chkconfig -add galaxy
/etc/init.d/galaxy start

#sge init & ssh key stop 
/sbin/chkconfig -add sgeexecd.bioinformatics_450a5914-cf17-4d04-a38a-aec7cbb14303
/sbin/chkconfig -add sgemaster.bioinformatics_450a5914-cf17-4d04-a38a-aec7cbb14303 
/sbin/chkconfig --del cloud-set-guest-sshkey.in

#sending message via AWS SNS
echo "[Credentials]" > /root/.boto
echo "aws_access_key_id = AKIAJ5AR6DNAQZNL3FLQ" >> /root/.boto
echo "aws_secret_access_key = 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" >> /root/.boto

python <<EOF
import os
import boto
sns = boto.connect_sns()
topics = sns.get_all_topics()
mytopics = topics["ListTopicsResponse"]["ListTopicsResult"]["Topics"]
mytopic_arn = mytopics[0]["TopicArn"]
subscriptions = sns.get_all_subscriptions_by_topic(mytopic_arn)
msg = "Hi there. I am sending this message over boto. Bye my bf"
msg = msg + " Master IP: 172.27.41.107 / PW: iT3wnkdhw"
subj="[450a5914-cf17-4d04-a38a-aec7cbb14303] AWS Message Services - Master Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

echo "deploy product from script" >> /tmp/deploy_result.txt
echo "master ip: 172.27.41.107" >> /tmp/deploy_result.txt
echo "master pw: iT3wnkdhw" >> /tmp/deploy_result.txt

/bin/rm /etc/init.d/userdata

python <<EOF
import sys
import os
import subprocess
import datetime
import re
import time
from xml.etree import ElementTree
import client_side
import logging
import boto
from boto.sqs.message import Message

AUTOSCALE_QUEUE = 'autoscale_queue'
cluster_uuid = 450a5914-cf17-4d04-a38a-aec7cbb14303

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
      else:
         log.debug("not yet: %s %d"%(delta.seconds, queue_size))

if __name__ == "__main__":
    while True:
        main()
        time.sleep(2)
EOF
   