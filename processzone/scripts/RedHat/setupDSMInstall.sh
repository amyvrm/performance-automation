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

# Wait for DSM Manager port (4119) to be listening before returning
echo "Waiting for DSM Manager service to be ready on port 4119..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
	if sudo ss -tlnp 2>/dev/null | grep -q ':4119 '; then
		echo "✓ DSM Manager port 4119 is now listening"
		break
	fi
	attempt=$((attempt + 1))
	if [ $((attempt % 10)) -eq 0 ]; then
		echo "  Still waiting... (attempt $attempt/$max_attempts)"
	fi
	sleep 1
done

if [ $attempt -ge $max_attempts ]; then
	echo "⚠️  WARNING: DSM port 4119 did not become ready after ${max_attempts}s"
	echo "DSM service status:"
	sudo service dsm_s status || true
	echo "Recent DSM logs:"
	sudo tail -20 /opt/dsm/log/dsm_s/catalina.out || sudo tail -20 /var/log/dsm_s.log || echo "No logs found"
	exit 1
fi

echo "DSM installation finished with settings and service confirmed ready"