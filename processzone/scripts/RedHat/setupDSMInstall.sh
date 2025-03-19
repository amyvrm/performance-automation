DSMSETUPFILE=$1
LICENSE_KEY=$2
# sleep 2
sudo systemctl stop docker
# sleep 2
sudo systemctl enable --now docker  # Enables and starts Docker in one step
# sleep 2
sudo docker run --rm --privileged --name pg-docker -v /data/postgresql_data:/var/lib/postgresql/data -p 5432:5432 -e POSTGRES_PASSWORD=pgsql -e POSTGRES_DB=dsm -d postgres:10
# sleep 20
printf 'pgsql\ncreate database dsmtest with owner=postgres encoding=UTF8;\n\q' | sudo docker run -i --rm --link pg-docker:postgres postgres:10 psql -h postgres -U postgres
# sleep 20
sudo wget $DSMSETUPFILE -O /tmp/LinuxDSMSetup.sh
sleep 20
sudo chmod +x /tmp/LinuxDSMSetup.sh
sleep 2
sudo chmod +x /tmp/generatePropertiesDSM.sh 
sleep 3
sudo sh /tmp/generatePropertiesDSM.sh $LICENSE_KEY
sleep 3
sudo sh /tmp/LinuxDSMSetup.sh -q -console -varfile /tmp/DSMProperties.properties
sleep 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.webserviceAPIEnabled -value true
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.agentInitiatedActivation -value 1
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionsAllowed -value -1
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.dsruAutoApplyNewDSRUs -value false
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionExceededAction -value 2
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.minutesToTimeout -value 120.0
sleep 2
sudo cat > /opt/dsm/dsm_s.vmoptions<<EOF1
-Xmx8g
-Xms3g
EOF1
sudo service dsm_s restart
sleep 15
echo "DSM installation finished with settings"