#!/bin/bash
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
msg="Hi there. I am sending this message over boto. Bye my bf"
subj="[6684d32b-ae7a-4c39-9a13-81ed2ae299be] AWS Message Services - Master Node"
res=sns.publish(mytopic_arn,msg,subj)
EOF

echo "deploy product from script" >> /tmp/deploy_result.txt
echo "master ip: 172.27.76.32" >> /tmp/deploy_result.txt
echo "slave ip: iR6uwgwzs" >> /tmp/deploy_result.txt
   