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

sudo curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.7 get-pip.py

python3.7 -m pip install zeep

python3.7 uploadDSAToDSM.py --dsmHost 127.0.0.1 --dsmUser masteradmin --dsmPasswd AppleTree#1975! --agentFolder /tmp/AgentPackages/
