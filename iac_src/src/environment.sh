#!/bin/bash

sudo apt-get update -y
python3 --version
sudo apt-get install python3-wheel -y
sudo apt-get install python3-dev -y
sudo apt-get install python3-pip -y
pip install requests
pip install pypsexec
pip install rsa
pip install boto3
pip install boto
pip install lxml
pip install pylzma
pip install zeep
pip install urllib3==1.25.8
pip install pandas
pip install matplotlib
pip install seaborn