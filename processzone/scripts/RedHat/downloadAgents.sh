#!/bin/bash

AGENTURLS=$1

sudo mkdir /tmp/AgentPackages

IFS='~~' read -ra all_agents <<< "$AGENTURLS"

for i in "${all_agents[@]}"
do
	echo $i
	sudo wget $i -P /tmp/AgentPackages/
done

sudo chmod -R a+rwx /tmp/AgentPackages

cd /tmp

#sudo curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
#python3.7 get-pip.py

#python3.7 -m pip install zeep

sudo yum install -y libxml2-devel libxslt-devel python3.6-devel gcc
sudo pip3 install --upgrade pip setuptools
sudo pip3 install lxml
sudo pip3 install zeep

python3 uploadDSAToDSM.py --dsmHost 127.0.0.1 --dsmUser supermasteradmin --dsmPasswd OrangePlant#1980 --agentFolder /tmp/AgentPackages/