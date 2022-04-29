DSMSETUPFILE=$1
LICENSE_KEY=$2
sudo yum -y install yum-utils
sleep 2
sudo yum-config-manager --enable rhui-REGION-rhel-server-extras
sleep 4
sudo yum -y install wget
sleep 2
sudo yum -y install unzip
sleep 2
#sudo yum -y install docker
#sleep 2
#sudo systemctl stop docker
#sleep 2
#sudo systemctl enable docker
#sleep 2
#sudo systemctl start docker
#sleep 2
sudo docker pull postgres:10
sleep 4
sudo mkdir -p /data/postgresql_data
sleep 2
sudo mkdir -p /tmp/dsa_install
sleep 2
sudo docker run --rm --privileged --name pg-docker -v /data/postgresql_data:/var/lib/postgresql/data -p 5432:5432 -e POSTGRES_PASSWORD=pgsql -e POSTGRES_DB=dsm -d postgres:10
sleep 2
printf 'pgsql\ncreate database dsmtest with owner=postgres encoding=UTF8;\n\q' | sudo docker run -i --rm --link pg-docker:postgres postgres:10 psql -h postgres -U postgres
sleep 2
sudo wget $DSMSETUPFILE -O /tmp/LinuxDSMSetup.sh
sleep 2
sudo chmod +x /tmp/LinuxDSMSetup.sh
sleep 2
sudo chmod +x /tmp/generatePropertiesDSM.sh 
sleep 3
sudo sh /tmp/generatePropertiesDSM.sh $LICENSE_KEY
sleep 3
sudo sh /tmp/LinuxDSMSetup.sh -q -console -varfile /tmp/DSMProperties.properties
sleep 2
cp /tmp/dsm_s.vmoptions /opt/dsm/dsm_s.vmoptions
sleep 1
sudo systemctl stop dsm_s
sleep 2
sudo systemctl start dsm_s
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.webserviceAPIEnabled -value true
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.agentInitiatedActivation -value 1
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionsAllowed -value -1
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.dsruAutoApplyNewDSRUs -value false
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionExceededAction -value 2
sleep 2
echo DSM installation finished with settings
