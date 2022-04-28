#!/bin/bash

sudo apt-get update
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y

# terraform https://learn.hashicorp.com/tutorials/terraform/install-cli
sudo apt-get install -y gnupg software-properties-common curl
sudo curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update
sudo apt-get install terraform=1.1.7

# python dependency
sudo pip3 install boto3
sudo pip3 install boto
sudo pip3 install rsa
sudo pip3 install pypsexec
sudo pip3 install simplejson
sudo apt-get install -y git
sudo apt-get install -y gcc
sudo pip install requests
sudo pip install lxml
sudo pip install pylzma
sudo pip install zeep
sudo pip install urllib3==1.25.8
sudo pip install pandas
sudo pip install matplotlib
sudo pip install seaborn
