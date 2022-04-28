FROM python:3
RUN apt-get update
RUN useradd -s /bin/bash -u 501 -U -d /build -m build && groupmod -g 501 build

# terraform https://learn.hashicorp.com/tutorials/terraform/install-cli
RUN apt-get install -y gnupg software-properties-common curl
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
RUN apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
RUN apt-get update
RUN apt-get install terraform=1.1.7

RUN apt-get install python3-pip -y
RUN pip install requests
RUN pip install lxml
RUN pip install pylzma
RUN pip install zeep
RUN pip install urllib3==1.25.8
RUN pip3 install boto3
RUN pip3 install boto
RUN pip3 install rsa
#RUN pip3 install simplejson
RUN apt-get install -y git
RUN apt-get install -y gcc