#!/bin/bash
set -euo pipefail

AGENTURLS=${1:-}
TARGET_DIR="/tmp/AgentPackages"

sudo mkdir -p "$TARGET_DIR"

IFS='~~' read -ra all_agents <<< "$AGENTURLS"

echo "Starting parallel agent downloads (count: ${#all_agents[@]})"
pids=()
for url in "${all_agents[@]}"; do
	echo "Download: $url"
	# Download in background with retry, quiet output
	(sudo wget -q --show-progress --tries=3 --timeout=20 -P "$TARGET_DIR" "$url") &
	pids+=("$!")
done

# Wait for all downloads to complete
for pid in "${pids[@]}"; do
	wait "$pid" || { echo "A download failed (pid=$pid)"; exit 1; }
done

sudo chmod -R a+rwx "$TARGET_DIR"

cd /tmp

# Speed up package installs: combine into single yum call and quiet pip installs
PKGS=(libxml2-devel libxslt-devel python3.11-devel gcc)
echo "Installing build dependencies: ${PKGS[*]}"
sudo yum install -y "${PKGS[@]}"

echo "Upgrading pip and installing Python dependencies"
sudo python3 -m pip install --upgrade --quiet pip setuptools
sudo python3 -m pip install --quiet lxml zeep

echo "Uploading DSAs to DSM"
python3 uploadDSAToDSM.py --dsmHost 127.0.0.1 --dsmUser supermasteradmin --dsmPasswd OrangePlant#1980 --agentFolder "$TARGET_DIR"
