#!/bin/sh
#chkconfig: 345 97 93
#description: Autoscaling monitoring script
period=$(cat policy.conf | grep 'Monitoring(per minute)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
pvmip=$(cat policy.conf | grep 'PVMIP' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
while true;do
        time=`date +%Y%m%d%H%M%S`
        host=`hostname`
        vmstat 1 2 > result_$host$time
        netstat -an | grep ESTABLISHED | wc -l >> result_$host$time
        netstat -an | grep :80.*ESTABLISHED | wc -l >> result_$host$time
        #scp -r ./result_* root@$pvmip:/root/pvm/monitoredInfo
        #rm -f result*
        sleep $(( $period * 60 ))
done
