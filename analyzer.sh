#!/bin/bash

TYPE=$(cat policy.conf | grep 'select type(1 or 2)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
mail=$(cat policy.conf | grep 'Mail address' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
CPUOK=$(cat policy.conf | grep 'CPU(y/n)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
MEMOK=$(cat policy.conf | grep 'MEMORY(y/n)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
NETOK=$(cat policy.conf | grep 'NETWORK(y/n)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
APAOK=$(cat policy.conf | grep 'APACHE(y/n)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
CPULIM=$(cat policy.conf | grep 'CPU upper limit' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
MEMLIM=$(cat policy.conf | grep 'MEM upper limit' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
NETLIM=$(cat policy.conf | grep 'NET upper limit' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
APALIM=$(cat policy.conf | grep 'APACHE upper limit' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
SCALPERI=$(cat policy.conf | grep 'Scaling period' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )
MONIPERI=$(cat policy.conf | grep 'Monitoring(per minute)' | awk -F"\\\=" '{ print $2 }' | sed 's/ //g' )

while true;do
if [ $TYPE = 1 ] ; then
        if [ "$(ls -A /autoscale/client/monitoredInfo)" ]; then
        loglisttemp=`ls /autoscale/client/monitoredInfo/`
        for loglist in $loglisttemp
        do
                i=0
                while [ $i -lt 4 ]
                do
                        read r b swpd free buff cache si so bi bo in cs us sy id wa st
                        i=$(($i+1))
                done <"/autoscale/client/monitoredInfo/$loglist"
                i=0
                while [ $i -lt 5 ]
                do
                        read NET
                        i=$(($i+1))
                done <"/autoscale/client/monitoredInfo/$loglist"
                i=0
                while [ $i -lt 6 ]
                do
                        read APA
                        i=$(($i+1))
                done <"/autoscale/client/monitoredInfo/$loglist"
                if [ "$free" == "" ]; then
                free=100;buff=0;cache=0;us=0;NET=0;APA=0;fi
                CPU=$us
                MEM=$(( 100 - 100 * $free / ( $free + $buff + $cache ) ))

                if [ $CPU -gt $CPULIM ]; then
                        echo "CPU usage = $CPU"
                        echo "Run autoscale"
                        echo
                        echo "ucloud Autoscale"
			./sleep.sh
                        #./autoscale.php
                        #rm -f /autoscale/client/monitoredInfo/*
                        sleep $SCALPERI
                        #exit
                else
                        echo "CPU usage = $CPU"
                        echo "MEM usage = $MEM"
                        echo "NETWORK SESSIONS = $NET"
                        echo "APACHE SESSIONS = $APA"
                        echo "Noting to do"
                        echo
                        sleep $(( $MONIPERI * 10 ))
                        #rm -f /autoscale/client/monitoredInfo/$loglist
                fi
        done
        else
                echo "There's no log file"
                echo
                sleep $(( $MONIPERI * 10 ))
        fi

fi
sleep 2
done
