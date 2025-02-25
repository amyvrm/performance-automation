#!/usr/bin/python3

import argparse
import glob
import subprocess
import urllib3
import requests
import time
import zeep
import json
import datetime
import os
from datetime import timezone


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--ip", action="store", help="IP address of DSM")
	parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
	args = parser.parse_args()

	urllib3.disable_warnings()

	dsm_ip = args.ip

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

			save_internal_ids_to_json(client, sID)

			print("Saved Internal IDs to /tmp/internal_id.json")

		except (zeep.exceptions.Fault, SystemExit) as e:
			print(e)
			client.service.endSession(sID=sID)
			client.transport.session.close()
			print("\nError downloading internal ids, exiting")
			sys.exit(-1)


# Logs in to the SOAP API
def login_SOAP(client, credentials):
	print("Logging in to SOAP")
	username, password = credentials
	return client.service.authenticate(username=username, password=password)



# Returns the internal IDs for each of the identifiers
def save_internal_ids_to_json(zeep_client, sID):
	dpi_dict = {}
	response = zeep_client.service.DPIRuleRetrieveAll(sID=sID)
	for eachresponse in response:
		dpi_dict[eachresponse['identifier']] = eachresponse['ID']

	with open('/tmp/internal_id.json', 'w') as fp:
		json.dump(dpi_dict, fp, indent=4)


if __name__ == '__main__':
	main()
