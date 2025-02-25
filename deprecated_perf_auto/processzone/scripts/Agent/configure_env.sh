#!/bin/bash

sudo /bin/bash /tmp/pplay/initializepplay.sh

sudo pip3 install -r /tmp/SecurityCenter/requirements.txt

sudo docker build -t pplay_server -f /tmp/pplay/Dockerfile .

sudo pip3 install --upgrade pip3

sudo pip3 install --upgrade pip

sudo python3 -m pip install pplay

#sudo pip3 install pplay

#sudo python3 -m pip install -U pip

#sleep 2

#pip install pplay

#pip3 install pplay
