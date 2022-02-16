FROM python
RUN apt-get update && apt-get install -y unzip wget && \
useradd -s /bin/bash -u 501 -U -d /build -m build && groupmod -g 501 build
RUN curl https://releases.hashicorp.com/terraform/0.12.26/terraform_0.12.26_linux_amd64.zip -o terraform.zip && \
unzip terraform.zip -d /usr/local/bin

RUN apt-get install -y python3-pip python3-dev
RUN /usr/local/bin/python -m pip install --upgrade pip
# RUN pip3 install boto3
# RUN pip3 install boto
# RUN pip3 install rsa
# RUN pip3 install pypsexec
# RUN pip3 install simplejson
RUN pip install boto3
RUN pip install boto
RUN pip install rsa
RUN pip install pypsexec
RUN pip install simplejson
RUN apt-get install -y git
RUN apt-get install -y gcc
RUN pip install requests
RUN pip install lxml
RUN pip install pylzma
RUN pip install zeep
RUN pip install urllib3==1.25.8
RUN pip install pandas
RUN pip install matplotlib
RUN pip install seaborn
