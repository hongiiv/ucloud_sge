#!/usr/bin/python
import CloudStack
import time
import sqlite3
import os
import sys
import logging

log = logging.getLogger('bioinformatics')
log.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s')
logging.warning('is when this event was logged.')

SQLITE_ADMIN = 'genome_admin'
KT_HOST = 'https://api.ucloudbiz.olleh.com/server/v1/client/api'
KT_APIKEY = 'iW59r_QY7T07T-fXY7FH8IRsYbgJ6b-fV4pvCFsYkbx6ArMGFhaL4-sEz7zbpCNUA1I6ovcLIH2dTbXVp34mAA'
KT_SECRET = 'ttteX3ygXMJBHPinj3zVOuHg1WCq3tqX014elUPkMryMhiGP3OjcBijKPkMA7N9DGCZY5RvO9aLMuOh6SfY9dQ'
local_pwd = "/autoscale/client"
deploy_server_ip = "172.27.121.128"
deploy_server_port = "22"

def build_script_master(productid):
   try:
      slave_host_name = []
      slave_private_address = []
      master_private_address = ''
      master_password = ''
      master_host_name = ''

      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = 'select virtual_machine_id, displayname, private_address, password, vm_tot_count from table_instance where clusteruuid="%s"'%(productid)
      log.debug(SQL)
      cursor.execute(SQL)

      for row in cursor:
         if row[4] == '1':
            master_private_address = row[2]
            master_password = row[3]
            master_host_name =row[0]
         else:
            slave_host_name.append(row[0])
            slave_private_address.append(row[2])
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Cannot connect database")

   #hosts file for sge script
   hosts_file = "%s	%s	master"%(master_private_address, master_host_name)
   sge_admin_host_list = "%s"%(master_host_name)
   for j in range(len(slave_private_address)):
      now_host = '''
%s	%s	node0%s'''%(slave_private_address[j], slave_host_name[j],j+1)
      hosts_file = hosts_file + now_host
      sge_admin_host_list = sge_admin_host_list + " %s"%(slave_host_name[j])
   sge_host_file = "%s.hosts"%(productid)
   #print sge_host_file
   f = file(sge_host_file,"w")
   f.write(hosts_file)
   f.close()
   local_pwd = "/autoscale/client"
   command = "/bin/mv %s/%s /cloudfiles/%s"%(local_pwd, sge_host_file, sge_host_file)
   log.debug("Deploy your cluster computer: %s"%(command))
   command_external = os.system(command)
   if not command_external == 0:
      log.debug("Deploy job fail: mv fail :(")

   #sge config file for sge script
   sge_config ='''SGE_ROOT="/opt/sge"
SGE_QMASTER_PORT="6444"
SGE_EXECD_PORT="6445"
CELL_NAME="default"
ADMIN_USER="sgeadmin"
SGE_CLUSTER_NAME="bioinformatics_%s"
QMASTER_SPOOL_DIR="/opt/sge/default/spool/qmaster"
EXECD_SPOOL_DIR="/opt/sge/default/spool/execd"
HOSTNAME_RESOLVING="true"
SHELL_NAME="ssh"
COPY_COMMAND="scp"
DEFAULT_DOMAIN="none"
ADMIN_MAIL="none"
ADD_TO_RC="true"
SET_FILE_PERMS="true"
RESCHEDULE_JOBS="wait"
SCHEDD_CONF="1"
SHADOW_HOST=""
EXEC_HOST_LIST_RM=""
REMOVE_RC="true"
WINDOWS_SUPPORT="false"
WIN_ADMIN_NAME="Administrator"
WIN_DOMAIN_ACCESS="false"
GID_RANGE="50700-50800"
SPOOLING_METHOD="classic"
DB_SPOOLING_SERVER="none"
DB_SPOOLING_DIR="/opt/sge/default/spooldb"
ADMIN_HOST_LIST="%s"
SUBMIT_HOST_LIST="%s"
EXEC_HOST_LIST="%s"
EXECD_SPOOL_DIR_LOCAL=""
RESCHEDULE_JOBS="wait"
SGE_ENABLE_SMF="0"
CSP_RECREATE="true"
CSP_COPY_CERTS="false"
CSP_COUNTRY_CODE="KR"
CSP_STATE="Korea"
CSP_LOCATION="Building"
CSP_ORGA="Organisation"
CSP_ORGA_UNIT="Organisation_unit"
CSP_MAIL_ADDRESS="hongiiv@gmail.com"
   '''%(productid, sge_admin_host_list, sge_admin_host_list, sge_admin_host_list)

   sge_config_file = "%s.config"%(productid)
   f = file(sge_config_file,"w")
   f.write(sge_config)
   f.close()
   local_pwd="/autoscale/client"
   command = "/bin/mv %s/%s /cloudfiles/%s"%(local_pwd, sge_config_file, sge_config_file)
   log.debug("Deploy your cluster computer: %s"%(command))
   command_external = os.system(command)
   if not command_external == 0:
      log.debug("Deploy job fail: mv fail :(")

#script for master node init script

   script = '''#!/bin/bash
export LC_MESSAGE="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"
export LC_ALL="en_US.UTF-8"
echo "export LC_MESSAGES=\"en_US.UTF-8\"" >> /root/.bashrc
echo "export LANG=\"en_US.UTF-8\"" >> /root/.bashrc
echo "export LANGUAGE=\"en_US:en\"" >> /root/.bashrc
echo "export LC_ALL=\"en_US.UTF-8\"" >> /root/.bashrc

export SGE_ROOT="/opt/sge"
export SGE_CELL="default"
export PATH=$PATH:/opt/sge/bin/linux-x64/
echo "export PATH=$PATH:/opt/sge/bin/linux-x64/" >> /root/.bashrc
echo "export SGE_ROOT=\"/opt/sge\"" >> /root/.bashrc
echo "export SGE_CELL=\"default\"" >> /root/.bashrc
echo "export DRMAA_LIBRARY_PATH=/opt/sge/lib/linux-x64/libdrmaa.so.1.0" >> /root/.bashrc

/usr/bin/wget ftp://172.27.121.128/%s -O /tmp/%s
/usr/bin/wget ftp://172.27.121.128/%s -O /tmp/%s

/bin/cat /tmp/%s >> /etc/hosts

/usr/bin/wget ftp://172.27.121.128/sge.tar.gz -O /opt/sge.tar.gz
cd /opt
/bin/tar xvfz /opt/sge.tar.gz 
/bin/cp /tmp/%s /opt/sge
/usr/sbin/useradd sgeadmin
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*
cd /opt/sge
./inst_sge -m -x -auto /opt/sge/%s
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*

apt-get update -y
apt-get install mdadm -y
apt-get install git -y
apt-get install unzip -y
apt-get install mercurial -y
apt-get install csh -y
apt-get install chkconfig -y
apt-get install postgresql -y
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

apt-get install nfs-kernel-server nfs-common portmap -y
echo "/BIO *(rw,no_root_squash,no_all_squash,async,no_subtree_check)" >> /etc/exports 
echo "/opt/sge *(rw,no_root_squash,no_all_squash,async,no_subtree_check)" >> /etc/exports

#/usr/sbin/service portmap restart
#/etc/init.d/nfs-kernel-server restart

#install galaxy
cd /BIO
/usr/bin/hg clone https://bitbucket.org/galaxy/galaxy-central
cd /BIO/galaxy-central
wget ftp://172.27.121.128/universe_wsgi.ini -O /BIO/galaxy-central/universe_wsgi.ini
#/bin/sh run.sh &

wget ftp://172.27.121.128/galaxy -O /etc/init.d/galaxy
/bin/chmod 755 /etc/init.d/galaxy
/sbin/chkconfig -add galaxy
/etc/init.d/galaxy start

#sge init & ssh key stop 
/sbin/chkconfig -add sgeexecd.bioinformatics_%s
/sbin/chkconfig -add sgemaster.bioinformatics_%s 
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
msg = msg + " Master IP: %s / PW: %s"
subj="[%s] AWS Message Services - Master Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

echo "deploy product from script" >> /tmp/deploy_result.txt
echo "master ip: %s" >> /tmp/deploy_result.txt
echo "slave ip: %s" >> /tmp/deploy_result.txt

/bin/rm /etc/init.d/userdata

   '''%(sge_config_file, sge_config_file, sge_host_file, sge_host_file, sge_host_file, sge_config_file, sge_config_file, productid, productid, master_private_address, master_password, productid, master_private_address, master_password)

   script_name = ("%s_master.sh")%(productid)
   f = file(script_name,"w")
   f.write(script)
   f.close()
   command = "/bin/mv %s/%s /cloudfiles/%s"%(local_pwd, script_name, script_name)
   log.debug("Deploy your cluster computer: %s"%(command))
   command_external = os.system(command)
   if not command_external == 0:
      log.debug("Deploy job fail: mv fail :(")

#####
def build_script_slave(productid):
   try:
      slave_host_name = []
      slave_private_address = []
      master_private_address = ''
      master_password = ''
      master_host_name = ''

      db = sqlite3.connect(SQLITE_ADMIN)
      cursor = db.cursor()
      SQL = 'select virtual_machine_id, displayname, private_address, password, vm_tot_count from table_instance where clusteruuid="%s"'%(productid)
      #print SQL
      cursor.execute(SQL)

      for row in cursor:
         #print row
         if row[4] == '1':
            master_private_address = row[2]
            master_password = row[3]
            master_host_name =row[0]
         else:
            slave_host_name.append(row[0])
            slave_private_address.append(row[2])
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Cannot connect database")

   script = '''#!/bin/bash
export LC_MESSAGE="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"
export LC_ALL="en_US.UTF-8"
echo "export LC_MESSAGES=\"en_US.UTF-8\"" >> /root/.bashrc
echo "export LANG=\"en_US.UTF-8\"" >> /root/.bashrc
echo "export LANGUAGE=\"en_US:en\"" >> /root/.bashrc
echo "export LC_ALL=\"en_US.UTF-8\"" >> /root/.bashrc

export SGE_ROOT="/opt/sge"
export SGE_CELL="default"
export PATH=$PATH:/opt/sge/bin/linux-x64/
echo "export PATH=$PATH:/opt/sge/bin/linux-x64/" >> /root/.bashrc
echo "export SGE_ROOT=\"/opt/sge\"" >> /root/.bashrc
echo "export SGE_CELL=\"default\"" >> /root/.bashrc
echo "export DRMAA_LIBRARY_PATH=/opt/sge/lib/linux-x64/libdrmaa.so.1.0" >> /root/.bashrc

wget ftp://172.27.121.128/%s.hosts -O /tmp/%s.hosts
/bin/cat /tmp/%s.hosts >> /etc/hosts
/usr/sbin/useradd sgeadmin

#creating file system
mkdir -p /DATA
echo "n" >> swap.in
echo "p" >> swap.in
echo "1" >> swap.in
echo "" >>  swap.in
echo "" >> swap.in
echo "w" >> swap.in
/sbin/fdisk /dev/xvdb < swap.in
/sbin/mkfs.ext3 /dev/xvdb1
echo "/dev/xvdb1     /DATA     ext3     defaults     0 0" >> /etc/fstab
mount -a

apt-get update -y
apt-get install nfs-common -y
apt-get install portmap -y
apt-get install git -y
apt-get install unzip -y
apt-get install mercurial -y
apt-get install csh -y
apt-get install chkconfig -y
cd /root
git clone https://github.com/boto/boto
cd boto
/usr/bin/python setup.py install

mkdir -p /BIO
mkdir -p /opt/sge

/bin/mount -t nfs -o nolock %s:/BIO /BIO
/bin/mount -t nfs -o nolock %s:/opt/sge /opt/sge

cd /opt/sge
./inst_sge -x -auto /opt/sge/%s.config

echo "%s:/BIO	/BIO	nfs	timeo=14,intr" >> /etc/fstab
echo "%s:/opt/sge	/opt/sge	nfs	timeo=14,intr" >> /etc/fstab

#sge init & ssh key stop
/sbin/chkconfig -add sgeexecd.bioinformatics_%s
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
subj="AWS Message Services - Slave Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

/bin/rm /etc/init.d/userdata

   '''%(productid, productid, productid, master_private_address, master_private_address, productid, productid, master_private_address, master_private_address)

   script_name = ("%s_slave.sh")%(productid)
   f = file(script_name,"w")
   f.write(script)
   f.close()
   command = "/bin/mv %s/%s /cloudfiles/%s"%(local_pwd, script_name, script_name)
   log.debug("Deploy your cluster computer: %s"%(command))
   command_external = os.system(command)
   if not command_external == 0:
      log.debug("Deploy job fail: mv fail :(")

def deploy_run(clusteruuid):
   result1 = attach_volume(clusteruuid)
   result2 = build_script_master(clusteruuid)
   result3 = build_script_slave(clusteruuid)
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
      SQL = "select virtual_machine_id, vm_tot_count from table_instance where clusteruuid='%s' and vm_tot_count='1'"%(clusteruuid)
      cursor.execute(SQL)
      for row in cursor:
         virtual_machine_id = row[0]
      log.debug("Seleted Master Node for Disk Attach: %s"%(virtual_machine_id))
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Cannot connect database")
   
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
      log.debug("Selected volume lists for cluster: %s"%(clusteruuid))
      print volume_list
      cursor.close()
      db.commit()
      db.close()
   except sqlite3.OperationalError:
      log.debug("Cannot connect database")

   #attach volume
   cloudstack = CloudStack.Client(KT_HOST, KT_APIKEY, KT_SECRET)
   for i in range(len(volume_list)):
      log.debug("Volume attach [%d] start %s: %s"%(i, volume_list[i], virtual_machine_id))
      reservation = cloudstack.attachVolume({
         'id':volume_list[i], 
         'virtualmachineid':virtual_machine_id,
      })
      jobid = reservation['jobid']
      while True:
         asyncstatus = cloudstack.queryAsyncJobResult({'jobid':str(jobid)})      
         if asyncstatus['jobstatus'] == 1:
            log.debug("Volume attach [%d] end %s: %s"%(i, volume_list[i], virtual_machine_id))
            print
            result = "1"
            break
         elif asyncstatus['jobstatus'] == 2:
            log.debug("Volume attach [%d] fail :( %s: %s"%(i, volume_list[i], virtual_machine_id))
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
