#!/bin/bash
export LC_MESSAGE="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"
export LC_ALL="en_US.UTF-8"
echo "export LC_MESSAGES="en_US.UTF-8"" >> /root/.bashrc
echo "export LANG="en_US.UTF-8"" >> /root/.bashrc
echo "export LANGUAGE="en_US:en"" >> /root/.bashrc
echo "export LC_ALL="en_US.UTF-8"" >> /root/.bashrc

apt-get update -y
apt-get install mdadm -y
apt-get install git -y
apt-get install unzip -y
apt-get install mercurial -y
apt-get install csh -y
apt-get install chkconfig -y
#apt-get install postgresql -y
apt-get install nfs-kernel-server nfs-common portmap -y

export SGE_ROOT="/opt/sge"
export SGE_CELL="default"
export PATH=$PATH:/opt/sge/bin/linux-x64/
echo "export PATH=$PATH:/opt/sge/bin/linux-x64/" >> /root/.bashrc
echo "export SGE_ROOT="/opt/sge"" >> /root/.bashrc
echo "export SGE_CELL="default"" >> /root/.bashrc
echo "export DRMAA_LIBRARY_PATH=/opt/sge/lib/linux-x64/libdrmaa.so.1.0" >> /root/.bashrc

/usr/bin/wget ftp://172.27.121.128/45ae1916-66e8-4461-9c59-8d426df20cf6.config -O /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6.config
/usr/bin/wget ftp://172.27.121.128/45ae1916-66e8-4461-9c59-8d426df20cf6.hosts -O /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6.hosts
/bin/cat /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6.hosts >> /etc/hosts
/usr/bin/wget ftp://172.27.121.128/sge.tar.gz -O /opt/sge.tar.gz
cd /opt
/bin/tar xvfz /opt/sge.tar.gz 
/bin/cp /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6.config /opt/sge
/usr/sbin/useradd sgeadmin
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*
cd /opt/sge
./inst_sge -m -x -auto /opt/sge/45ae1916-66e8-4461-9c59-8d426df20cf6.config
/bin/chown -R sgeadmin:sgeadmin /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge/*

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
/etc/init.d/nfs-kernel-server restart

#install galaxy
#cd /BIO
#/usr/bin/hg clone https://bitbucket.org/galaxy/galaxy-central
#cd /BIO/galaxy-central
#wget ftp://172.27.121.128/universe_wsgi.ini -O /BIO/galaxy-central/universe_wsgi.ini
#wget ftp://172.27.121.128/galaxy -O /etc/init.d/galaxy
#/bin/chmod 755 /etc/init.d/galaxy
#/sbin/chkconfig -add galaxy
#/etc/init.d/galaxy start

#sending message via AWS SNS
echo "[Credentials]" > /root/.boto
echo "aws_access_key_id = AKIAJ5AR6DNAQZNL3FLQ" >> /root/.boto
echo "aws_secret_access_key = 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" >> /root/.boto

/usr/bin/wget ftp://172.27.121.128/sleeper.sh -O /BIO/sleeper.sh
/usr/bin/wget ftp://172.27.121.128/45ae1916-66e8-4461-9c59-8d426df20cf6_autoscale_client.py -O /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6_autoscale_client.py
/usr/bin/python /tmp/45ae1916-66e8-4461-9c59-8d426df20cf6_autoscale_client.py &

python <<EOF
import os
import boto
sns = boto.connect_sns()
topics = sns.get_all_topics()
mytopics = topics["ListTopicsResponse"]["ListTopicsResult"]["Topics"]
mytopic_arn = mytopics[0]["TopicArn"]
subscriptions = sns.get_all_subscriptions_by_topic(mytopic_arn)
msg = "Hi there. I am sending this message over boto. Bye my bf"
msg = msg + " Master IP: 172.27.196.96 / PW: cU3mbhtiz"
subj="[45ae1916-66e8-4461-9c59-8d426df20cf6] AWS Message Services - Master Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

echo "deploy product from script" >> /tmp/deploy_result.txt
echo "master ip: 172.27.196.96" >> /tmp/deploy_result.txt
echo "master pw: cU3mbhtiz" >> /tmp/deploy_result.txt

#sge init & ssh key stop
/sbin/chkconfig -add sgeexecd.bioinformatics_45ae1916-66e8-4461-9c59-8d426df20cf6
/sbin/chkconfig -add sgemaster.bioinformatics_45ae1916-66e8-4461-9c59-8d426df20cf6
/sbin/chkconfig --del cloud-set-guest-sshkey.in

/bin/rm /etc/init.d/userdata

#insert running master.py
/usr/bin/wget ftp://172.27.121.128/master.py -O /tmp/master.py
/usr/bin/python /tmp/master.py 45ae1916-66e8-4461-9c59-8d426df20cf6 &
