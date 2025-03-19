# Applies a custom policy to all DSAs which includes the new/updated rules in the package

import os
import re
import sys
import json
import time
import requests
import argparse
import urllib3
import zeep
import xml.etree.ElementTree as ET
from string import Template

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--ip", action="store", help="IP address of DSM")
	parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
	parser.add_argument("-r", "--rule", action="store", help="Rule Identifier to apply")
	args = parser.parse_args()
	
	dsm_ip = args.ip
	
	urllib3.disable_warnings()
	
	wsdl_url = f"https://{dsm_ip}:4119/webservice/Manager?WSDL"
	login_url = f"https://{dsm_ip}:4119/SignIn.screen"
	policy_url = f"https://{dsm_ip}:4119/SecurityProfiles.screen"
	import_policy_url = f"https://{dsm_ip}:4119/ImportWizard.screen"
	
	transport = zeep.Transport()
	transport.session.verify = False  # Bypass self-signed certificate errors
	client = zeep.Client(wsdl=wsdl_url, transport=transport)
	policy_name = "au_testing"

	with requests.Session() as session:
		session.verify = False
		try:
			sID = login_SOAP(client, args.credentials)
			if not sID:
				sys.exit(-1)
			print("Login successful")
			
			save_internal_ids_to_json(client, sID)
			
			apply_rule_to_policy(client, sID, policy_name, args.rule)

			print("No problems applying rules")

		except (zeep.exceptions.Fault, SystemExit) as e:
			print(e)
			client.service.endSession(sID=sID)
			client.transport.session.close()
			print("\nError applying custom configurations, exiting")
			sys.exit(-1)

# Equivalent to pressing the import button and choosing an XML file
# There is no SOAP/REST API for uploading custom policy XML files, so we need to mimic the import wizard process
#   in order to import the policies
# The DSM is pretty picky about the exact formatting of the wizard requests/responses, so be careful when modifying
# Policy name is read directly from the policy xml file when uploading
# Since this is a bit of a hack to bypass API limitations, one should always double check the policy was uploaded
#   properly after since it is difficult to get that information here (posts will always return status code 200)
def upload_custom_policy(session, rID, policy_xml_data, import_policy_url):
    print("Uploading au_testing policy xml")
    response = session.get(f"{import_policy_url}?type=SecurityProfile")
    guid = re.search(r'id="guid" name="guid" type="hidden" value="([-A-Z0-9]*)"', response.text).group(1)
    data = {"guid": (None, guid), "step": (None, "0"), "rID": (None, rID), "cmdArguments": (None, ""),
            "command": (None, "NEXTORFINISH"), "changed": (None, "false"),
            "type": (None, "SecurityProfile"), "filePath": (None, ""),
            "file": ("policy", policy_xml_data, "text/xml"),
            "parentProfileID": (None, ""), "parentProfileID_tree_viewstate": (None, "tvi_1"),
            "parentProfileID_tree_selected": (None, "0"), "certificatePurpose": (None, "2"),
            "finish": (None, "Next >")}
    session.post(import_policy_url, files=data)
    time.sleep(10)  # Waiting for the policy to be parsed

    del data["file"]
    del data["finish"]
    data["step"] = (None, "1")
    session.post(import_policy_url, data=data)
    time.sleep(5)

    data["step"] = (None, "2")
    session.post(import_policy_url, data=data)
	
# Get all hosts IDS
def getSecurityProfileByName(client, securityProfileName, sID):
    print("Getting Security Profile ID")
    securityProfileResponse = client.service.securityProfileRetrieveByName(name=securityProfileName, sID=sID)
    return securityProfileResponse
	
# Get all hosts IDS
def getAllHostsIds(client, sID):
    print("Getting All Hosts IDs")
    hostsInfoResponse = client.service.hostRetrieveAll(sID=sID)
    return hostsInfoResponse

# Apply policy to hosts
def applySecurityProfileToHost(client, sID, hostID, securityProfileID):
    print("Applying security profile to host")
    response = client.service.securityProfileAssignToHost(securityProfileID=securityProfileID, hostIDs=hostID, sID=sID)
    return response
	
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

	with open('internal_id.json', 'w') as fp:
		json.dump(dpi_dict, fp, indent=4)
		
def apply_rule_to_policy(client, sID, policy_name, rule):
	print(f"Finding policy ID for policy {policy_name}", flush=True)
	policy_id = get_policy_id(client, sID, policy_name)
	if not policy_id:
		raise zeep.exceptions.Fault(message=f"ERROR: Policy {policy_name} not found on the DSM, please double check if the policy has been created")
	print(f"Found, policy ID is {policy_id}")
	print("Attempting to apply rules to policy", flush=True)
	identifiers = []
	identifiers.append(rule)
	
	with open('rule_summary.json') as f:
		reqdrules = json.load(f)
	
	identifiers.extend(reqdrules['required_identifier'])
	
	dpi_rule_ids = get_dpi_ids(identifiers)
	integrity_rule_ids = []
	log_inspection_rule_ids = []
	upload_policy(client, sID, policy_name, policy_id, dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids)
	response = client.service.securityProfileRetrieveByName(name=policy_name, sID=sID)
	print("Policy Data: ")
	print(response)
	
# Returns the internal ID for the given policy
# Also useful to check if policies have been uploaded properly, or if policies are already on the DSM
def get_policy_id(client, sID, policy_name):
    return client.service.securityProfileRetrieveByName(name=policy_name, sID=sID)["ID"]
	
def get_dpi_ids(identifiers):
	
	with open('internal_id.json') as f:
		rules = json.load(f)
	
	dpi_ids = []
	for identifier in identifiers:
		dpi_ids.append(rules[identifier])
	print(dpi_ids)
	return dpi_ids

# Passing empty arrays to the three ids variables will empty the policy
def upload_policy(zeep_client, session_id, policy_name, policy_id, dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids):
	sp = {"ID": policy_id, "description": "DSRU Automation Testing Policy", "name": policy_name,
			"DPIRuleIDs": {"item":dpi_rule_ids}, "DPIState": "ON", "integrityRuleIDs": {"item":integrity_rule_ids}, "integrityState": "ON",
			"logInspectionRuleIDs": {"item":log_inspection_rule_ids}, "logInspectionState": "ON",
			"antiMalwareManualInherit": False, "antiMalwareRealTimeInherit": False, "antiMalwareScheduledInherit": False}
	return zeep_client.service.securityProfileSave(sp=sp, sID=session_id)
	
# Returns the internal IDs for each of the identifiers
def save_internal_ids_to_json(zeep_client, sID):
	dpi_dict = {}
	response = zeep_client.service.DPIRuleRetrieveAll(sID=sID)
	for eachresponse in response:
		dpi_dict[eachresponse['identifier']] = eachresponse['ID']

	with open('internal_id.json', 'w') as fp:
		json.dump(dpi_dict, fp, indent=4)

# Mimics logging in as a user to the DSM GUI
# Note that this is distinct from logging into SOAP or REST, and is mainly used when we need to access functions
#   that do not have APIs
def login_dsm_gui(session, credentials, login_url):
    print("Logging in to DSM GUI")
    username, password = credentials
    data = {"username": username, "password": password}
    response = session.post(login_url, data=data)
    if response.status_code != 200:
        print("Problem logging on, please check DSM status")
        print(f"Status code: {response.status_code}")
        return 0
    rID = re.search(r"window\.sessionStorage\.setItem\('rID','([A-Z0-9]*)'\)", response.text)
    if not rID:
        print("Problem getting session token, please check DSM status")
        return 0
    return rID.group(1)
	
if __name__ == '__main__':
    main()