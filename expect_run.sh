#!/usr/bin/expect -f\n

spawn "scp -r /autoscale/client/test.sh root@172.27.121.128:/root\n"
expect "password:\n"
send "bio1234!\r"
