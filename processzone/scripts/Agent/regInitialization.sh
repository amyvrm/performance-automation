#!/bin/bash
#1009308,1009315,1009319

DSMIP=$1
FILTERS=$2
DSRU=$3
NX_USR=$4
NX_PWD=$5

cd /tmp

sudo python3 /tmp/SecurityCenter/apply_relay.py -i $DSMIP -c supermasteradmin OrangePlant#1980

sleep 30

cd /tmp

sudo python3 /tmp/SecurityCenter/apply_policy.py -i $DSMIP -c supermasteradmin OrangePlant#1980 -v 20

sleep 5

#cd /tmp

#sudo python3 /tmp/download_package.py -u $DSRU -c $NX_USR $NX_PWD

#sleep 5

#cd /tmp

#python3 /tmp/SecurityCenter/download_pcaps.py -c QAuser QAPass -ft $FILTERS

#sleep 5

#python3 /tmp/SecurityCenter/recurse_regression.py -i $DSMIP -c supermasteradmin OrangePlant#1980 -v 20