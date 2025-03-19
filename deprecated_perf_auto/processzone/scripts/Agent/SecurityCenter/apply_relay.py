# Applies a custom policy to all DSAs which includes the new/updated rules in the package

import argparse
import sys
import time
import requests
import urllib3
import zeep


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--ip", action="store", help="IP address of DSM")
	parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
	args = parser.parse_args()

	dsm_ip = args.ip

	urllib3.disable_warnings()

	wsdl_url = f"https://{dsm_ip}:4119/webservice/Manager?WSDL"

	transport = zeep.Transport()
	transport.session.verify = False  # Bypass self-signed certificate errors
	client = zeep.Client(wsdl=wsdl_url, transport=transport)

	with requests.Session() as session:
		session.verify = False
		try:
			sID = login_SOAP(client, args.credentials)
			if not sID:
				sys.exit(-1)
			print("Login successful")

			get_replay_info(client, sID)

			time.sleep(60)

		except (zeep.exceptions.Fault, SystemExit) as e:
			print(e)
			client.service.endSession(sID=sID)
			client.transport.session.close()
			print("\nError applying custom configurations, exiting")
			sys.exit(-1)


def get_replay_info(client, sID):
	hostID = 0
	hostIDs = getAllHostsIds(client, sID)
	for eachHost in hostIDs:
		if 'Amazon Linux 2' in eachHost['platform']:
			hostID = eachHost['ID']
			print(hostID)

	editableSetting = {"settingKey": "CONFIGURATION_RELAYSTATE", "settingUnit": "NONE", "settingValue": "true"}
	hostSettingResponse = client.service.hostSettingSet(hostID=hostID, editableSettings=editableSetting, sID=sID)
	print(hostSettingResponse)


# Get all hosts IDS
def getAllHostsIds(client, sID):
	print("Getting All Hosts IDs")
	hostsInfoResponse = client.service.hostRetrieveAll(sID=sID)
	return hostsInfoResponse


# Logs in to the SOAP API
def login_SOAP(client, credentials):
	print("Logging in to SOAP")
	username, password = credentials
	return client.service.authenticate(username=username, password=password)


if __name__ == '__main__':
	main()
