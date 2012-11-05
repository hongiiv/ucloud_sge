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

wget ftp://172.27.121.128/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts -O /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts
/bin/cat /tmp/450a5914-cf17-4d04-a38a-aec7cbb14303.hosts >> /etc/hosts
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

/bin/mount -t nfs -o nolock 172.27.41.107:/BIO /BIO
/bin/mount -t nfs -o nolock 172.27.41.107:/opt/sge /opt/sge

cd /opt/sge
./inst_sge -x -auto /opt/sge/450a5914-cf17-4d04-a38a-aec7cbb14303.config

echo "450a5914-cf17-4d04-a38a-aec7cbb14303:/BIO	/BIO	nfs	timeo=14,intr" >> /etc/fstab
echo "172.27.41.107:/opt/sge	/opt/sge	nfs	timeo=14,intr" >> /etc/fstab

#sge init & ssh key stop
/sbin/chkconfig -add sgeexecd.bioinformatics_172.27.41.107
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

   