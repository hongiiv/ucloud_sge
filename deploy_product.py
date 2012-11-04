#!/usr/bin/python
import CloudStack
import time
import sqlite3
import os
import sys

SQLITE_ADMIN = 'genome_admin'
KT_HOST = 'https://api.ucloudbiz.olleh.com/server/v1/client/api'
KT_APIKEY = 'iW59r_QY7T07T-fXY7FH8IRsYbgJ6b-fV4pvCFsYkbx6ArMGFhaL4-sEz7zbpCNUA1I6ovcLIH2dTbXVp34mAA'
KT_SECRET = 'ttteX3ygXMJBHPinj3zVOuHg1WCq3tqX014elUPkMryMhiGP3OjcBijKPkMA7N9DGCZY5RvO9aLMuOh6SfY9dQ'
local_pwd = "/autoscale/client"
deploy_server_ip = "172.27.121.128"
deploy_server_port = "22"

def build_script(productid):
   try:
      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = 'select virtual_machine_id, displayname, private_address, password from table_instance where clusteruuid="%s" and vm_tot_count="1 of 2"'%(productid)
      print SQL
      cursor.execute(SQL)
      for row in cursor:
         address = row[2]
         password = row[3]
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      print ":( build_script database locked"

   script = '''#!/bin/bash
export LC_MESSAGES="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"
export LC_ALL="en_US.UTF-8"
apt-get update -y
apt-get install mdadm -y
apt-get install nfs-kernel-server -y
apt-get install nfs-common -y
apt-get install portmap -y
apt-get install git -y
cd /root
git clone https://github.com/boto/boto
cd boto
/usr/bin/python setup.py install
sudo /etc/init.d/portmap restart
sudo /etc/init.d/portmap restart
mkdir -p /BIO
mdadm --create --verbose /dev/md0 --level=0 --raid-devices=6 /dev/xvdb /dev/xvdc /dev/xvde /dev/xvdf /dev/xvdg /dev/xvdh
echo "n" >> swap.in
echo "p" >> swap.in
echo "1" >> swap.in
echo "" >>  swap.in
echo "" >> swap.in
echo "w" >> swap.in
/sbin/fdisk /dev/md0 < swap.in
/sbin/mkfs.ext3 /dev/md0
echo "/dev/md0     /BIO     ext3     defaults     0 0" >> /etc/fstab
mount -a

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
msg = msg + "\n Master IP: %s / PW: %s"
subj="[%s] AWS Message Services - Master Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

echo "deploy product from script" >> /tmp/deploy_result.txt
echo "master ip: %s" >> /tmp/deploy_result.txt
echo "slave ip: %s" >> /tmp/deploy_result.txt
   '''%(address, password, productid, address, password)

   script_name = ("master_%s.sh")%(productid)
   f = file(script_name,"w")
   f.write(script)
   f.close()
   command = "/usr/bin/scp %s/%s root@%s:/cloudfiles/%s"%(local_pwd, script_name, deploy_server_ip,script_name)
   print command
   command_external = os.system(command)
   if not command_external == 0:
      print ':( error, error'

def deploy_run(clusteruuid):
   result1 = attach_volume(clusteruuid)
   result2 = build_script(clusteruuid)
   return result1
   """
   preprocessing()
   processing()
   finalprocessing()
   return "1"
   """

def attach_volume(clusteruuid):
   #find master node from instance_table 
   try:
      db = sqlite3.connect(SQLITE_ADMIN, timeout=1)
      cursor = db.cursor()
      SQL = "select virtual_machine_id, vm_tot_count from table_instance where clusteruuid='%s' and vm_tot_count='1 of 2'"%(clusteruuid)
      cursor.execute(SQL)
      for row in cursor:
         virtual_machine_id = row[0]
      print "debug>> seleted master node: %s"%(virtual_machine_id)
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      print ":( database locked"
   
   #find volumes from volume_table
   volume_list =[]
   try:
      db = sqlite3.connect(SQLITE_ADMIN, timeout=1)
      cursor = db.cursor()
      SQL = "select volume_id from table_volume where clusteruuid='%s'"%(clusteruuid)
      print SQL
      cursor.execute(SQL)
      for row in cursor:
        volume_list.append(row[0])
      print "debug>> selected volume list"
      print volume_list
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      print ":( database locked"

   #attach volume
   cloudstack = CloudStack.Client(KT_HOST, KT_APIKEY, KT_SECRET)
   for i in range(len(volume_list)):
      print "debug>> %d - %s volume attach %s"%(i, volume_list[i], virtual_machine_id)
      reservation = cloudstack.attachVolume({
         'id':volume_list[i], 
         'virtualmachineid':virtual_machine_id,
      })
      jobid = reservation['jobid']
      while True:
         asyncstatus = cloudstack.queryAsyncJobResult({'jobid':str(jobid)})      
         if asyncstatus['jobstatus'] == 1:
            print "debug>> %d - %s volume attached %s"%(i, volume_list[i], virtual_machine_id)
            print
            result = "1"
            break
         elif asyncstatus['jobstatus'] == 2:
            print ":( disk attach job fail"
            result = "2"
            break
         else:
            time.sleep(5)

   #build_script(clusteruuid)
   
   return result

def preprocessing():
   return "1"

def processing():
   return "1"

def finalprocessing():
   return "1"
