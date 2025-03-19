#!/bin/bash
#1009308,1009315,1009319

DSMIP=$1
FILTERS=$2
DSRU=$3
LABS_JFROG_TOKEN=$4

sudo chmod 777 /tmp

cd /tmp

sudo bash /tmp/download_dsru.sh $DSRU $LABS_JFROG_TOKEN

sleep 5

cd /tmp

sudo python3 /tmp/apply_package.py -i $DSMIP -c supermasteradmin OrangePlant#1980

sleep 5

#cd /tmp

#sudo python3 /tmp/save_internal_id.py -i $DSMIP -c supermasteradmin OrangePlant#1980

#sleep 5

cd /tmp

python3 /tmp/SecurityCenter/download_pcaps.py -c QAAutomation qa3blabs789 -ft $FILTERS

sleep 5

echo '########### Uploading PCAPS to s3://regression-testing-jenkins/pcaps ##############'

sudo aws s3 sync /tmp/pcaps s3://dslabs-pcaps/pcaps

echo '########### PCAP uploaded successfully ##############'

sleep 5

#python3 /tmp/SecurityCenter/recurse_regression.py -i $DSMIP -c supermasteradmin OrangePlant#1980 -v 20