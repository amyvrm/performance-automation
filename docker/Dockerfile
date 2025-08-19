FROM python:3

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gnupg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Terraform
RUN curl -sSL https://releases.hashicorp.com/terraform/1.2.6/terraform_1.2.6_linux_amd64.zip -o terraform.zip && \
    unzip terraform.zip -d /usr/local/bin && \
    rm terraform.zip

RUN apt-get install python3-pip -y
RUN pip install requests==2.27.1
RUN pip install boto3==1.26.70
#RUN pip install lxml
#RUN pip install pylzma
#RUN pip install zeep
#RUN pip install urllib3==1.25.8
#RUN pip3 install boto3
#RUN pip3 install boto
#RUN pip3 install rsa
#RUN apt-get install -y git
#RUN apt-get install -y gcc
