#!/user/bin/python
import os

hostsfile ='''172.27.236.251	98b11739-6bec-48a6-8fb9-4faf7374aa0b	master
172.27.59.149	3349f9a9-c4b3-44af-9f15-df0011cdc19e	slave
'''
get_file = "/usr/bin/wget ftp://172.27.121.128/sge.config"
sge_config = "sge.config"

#ssh key-gen and share it
#shared filesystem

bashrc = '''export SGE_ROOT="/opt/sge"
export SGE_CELL="default"'''

script_hosts = '''#!/bin/bash
echo "%s" >> /etc/hosts_1'''%(hostsfile)

script_bashrc = '''#!/bin/bash

echo %s >> /root/.bashrc_1
/usr/sbin/useradd sgeadmin
cd /opt
/usr/bin/wget ftp://172.27.121.128/sge.tar.gz
/bin/tar xvfz sge.tar.gz
cd /opt/sge
/bin/chown -R sgeadmin:sgeadmin /opt/sge
./inst_sge -m -x -auto /opt/sge/%s
'''%(bashrc,sge_config)

print script_hosts
print
print script_bashrc

"""
command_external = os.system(script_hosts)
command_external = os.system(script_bashrc)

if not command_external == 0:
   print ':( error, error'
"""
