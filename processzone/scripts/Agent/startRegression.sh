#!/bin/bash

#1009315

DSMIP=$1
FILTER=$2
NX_USR=$3
NX_PWD=$4

cd /tmp

python3 /tmp/SecurityCenter/runRegression.py -i $DSMIP -c supermasteradmin OrangePlant#1980 -p /tmp/pcaps -r $FILTER -t 30 --teams $5 --build_user "$6" --jenkins_url $7

cd /tmp

sudo python3 /tmp/nexus_upload.py -c $NX_USR $NX_PWD