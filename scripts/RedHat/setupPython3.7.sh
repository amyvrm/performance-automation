sudo yum -y install gcc openssl-devel bzip2-devel libffi-devel make wget
sudo wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz -O /tmp/Python-3.7.4.tgz
sudo mkdir /tmp/Python-3.7.4
sudo tar xzf /tmp/Python-3.7.4.tgz -C /tmp/Python-3.7.4
sudo chmod -R a+rwx /tmp/Python-3.7.4
cd /tmp/Python-3.7.4/Python-3.7.4
./configure --enable-optimizations
sudo make altinstall
echo Python 3.7.4 installed.