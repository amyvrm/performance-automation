set -euo pipefail

DSMSETUPFILE=$1
LICENSE_KEY=$2

# Ensure Docker is running
sudo systemctl stop docker || true
sudo systemctl enable --now docker

# Start Postgres container (idempotent: recreate if exists)
if sudo docker ps -a --format '{{.Names}}' | grep -q '^pg-docker$'; then
	sudo docker rm -f pg-docker || true
fi
sudo docker run --rm --privileged --name pg-docker -v /data/postgresql_data:/var/lib/postgresql/data -p 5432:5432 -e POSTGRES_PASSWORD=pgsql -e POSTGRES_DB=dsm -d postgres:10

# Wait for Postgres readiness
echo "Waiting for Postgres to be ready..."
for i in {1..30}; do
	if sudo docker run --rm --link pg-docker:postgres postgres:10 pg_isready -h postgres -U postgres >/dev/null 2>&1; then
		break
	fi
	sleep 2
done

# Initialize database
printf 'pgsql\ncreate database dsmtest with owner=postgres encoding=UTF8;\n\q' | sudo docker run -i --rm --link pg-docker:postgres postgres:10 psql -h postgres -U postgres || true

# Download DSM setup script
echo "Downloading DSM setup from: $DSMSETUPFILE"
sudo wget -q "$DSMSETUPFILE" -O /tmp/LinuxDSMSetup.sh
sudo chmod +x /tmp/LinuxDSMSetup.sh
sudo chmod +x /tmp/generatePropertiesDSM.sh 

# Generate properties and run installer
sudo sh /tmp/generatePropertiesDSM.sh "$LICENSE_KEY"
sudo sh /tmp/LinuxDSMSetup.sh -q -console -varfile /tmp/DSMProperties.properties

# Apply DSM settings
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.webserviceAPIEnabled -value true
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.agentInitiatedActivation -value 1
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionsAllowed -value -1
sudo /opt/dsm/dsm_c -action changesetting -name settings.configuration.dsruAutoApplyNewDSRUs -value false
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.activeSessionExceededAction -value 1
sudo /opt/dsm/dsm_c -action changesetting -name settings.security.minutesToTimeout -value 240.0

# Tune JVM and restart service
sudo bash -lc 'cat > /opt/dsm/dsm_s.vmoptions <<EOF1
-Xmx8g
-Xms3g
EOF1'
sudo service dsm_s restart

echo "DSM installation finished with settings"