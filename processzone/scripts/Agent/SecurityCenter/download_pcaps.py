import errno
import os
import re
import sys
import json
import time
import requests
import argparse
import urllib3
import zeep
from string import Template

urllib3.disable_warnings()

CLASSNAME_PAYLOADFILTER2 = "PayloadFilter2"
SERVER = "https://labsap.thirdbrigade.com:1443"

sc_wsdl_url = "https://labsap.thirdbrigade.com:1443/webservice/SecurityCenter?WSDL"
qa_wsdl_url = "https://labsap.thirdbrigade.com:1443/webservice/Qa?WSDL"
rules_wsdl_url = "https://labsap.thirdbrigade.com:1443/webservice/SourceControl?WSDL"
update_wsdl_url = "https://labsap.thirdbrigade.com:1443/webservice/Update?WSDL"

username = None
password = None

transport = zeep.Transport()
transport.session.verify = False  # Bypass self-signed certificate errors
sc_client = zeep.Client(wsdl=sc_wsdl_url, transport=transport)
qa_client = zeep.Client(wsdl=qa_wsdl_url, transport=transport)
rules_client = zeep.Client(wsdl=rules_wsdl_url, transport=transport)
update_client = zeep.Client(wsdl=update_wsdl_url, transport=transport)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
	parser.add_argument("-ff", "--filter_file", action="store", help="Path to filter file")
	parser.add_argument("-ft", "--filters", action="store", help="Path to filter file")
	args = parser.parse_args()
	
	filter_file = args.filter_file
	if filter_file is not None:
		with open (filter_file, 'r') as readFilterFile:
			filter_file = readFilterFile.readlines()
			print(filter_file)
		
		filter_file = list(map(lambda s: s.strip(), filter_file))
	else:
		#filter_file = (args.filters).split(',')
		if (args.filters).lower() != "na":
			filter_file = (args.filters).split(',')
		else:
			with open(os.path.join("/tmp", "update-info", "rule-identifiers.txt"), "r") as f:
				data = f.readlines()
				filter_file = data
				filter_file = ''.join(data)
				filter_file = (filter_file).split(',')
				print(filter_file)
		
		
	print('Identified filters from list are: ', filter_file)
	
	#login_url = "https://labsap.thirdbrigade.com:1443/AdministratorSignIn.screen"
	
	dsm_v = int(9223372036854775807)
	
	user, pwd = args.credentials
	
	global username 
	global password
	
	username = user
	password = pwd
	
	sourceControlRequest = {"dsmVersion": dsm_v, "password":password, "userName":username}
	
	with requests.Session() as session:
		session.verify = False
		try:
			create_rule_cache(rules_client, sourceControlRequest, filter_file)
			rules, all_rules = read_rule_cache_json()
			apply_identifier_list, required_tbuid_list, required_identifier_list = get_rules_to_apply_list(rules, all_rules)
			pcap_info = pcap_info_for_rules(rules, qa_client)
			download_each_pcap(pcap_info, qa_client, rules)
			
			print('Downloaded all pcaps. Exiting.')
			

		except (zeep.exceptions.Fault, SystemExit) as e:
			print(e)
			sc_client.transport.session.close()
			qa_client.transport.session.close()
			rules_client.transport.session.close()
			update_client.transport.session.close()
			print("\nError executing script, exiting")
			sys.exit(-1)



# Logs in to the SOAP API
def login_sc_SOAP(client, credentials):
	print("Logging in to SOAP")
	username, password = credentials
	return client.service.authenticateAccount(username=username, password=password)

def sync_payload_filter(rules_client, sourceControlRequest):
	print("Logging in to SOAP Source Control")
	return rules_client.service.getAllCheckedIn(sourceControlRequest)
	
def read_rule_cache_json():
	print('Reading Rule Cache')
	with open('rules_cache.json') as f:
		rules = json.load(f)
	with open('rules_cache_all.json') as f:
		all_rules = json.load(f)
	return rules, all_rules
	
def get_rules_to_apply_list(rules, all_rules):
	required_tbuid_list = []
	required_identifier_list = []
	apply_identifier_list = []
	for key in rules:
		apply_identifier_list.append(rules[key]['identifier'])
		if rules[key]['requiresTBUIDs'] not in required_tbuid_list:
			if rules[key]['requiresTBUIDs'] is not None:
				required_tbuid_list.extend((rules[key]['requiresTBUIDs']).split(','))
			
	for onetbuid in required_tbuid_list:
		if all_rules[onetbuid]['identifier'] not in required_identifier_list:
			required_identifier_list.append(all_rules[onetbuid]['identifier'])
			
	required_identifier_json = {}
	required_identifier_json['apply_identifier'] = apply_identifier_list
	required_identifier_json['required_identifier'] = required_identifier_list
	required_identifier_json['required_tbuid'] = required_tbuid_list
	
	with open('rule_summary.json', 'w') as fp:
		json.dump(required_identifier_json, fp, indent=4)
		
	return apply_identifier_list, required_tbuid_list, required_identifier_list
	
def create_rule_cache(rules_client, sourceControlRequest, filter_file):
	payload_filter = sync_payload_filter(rules_client, sourceControlRequest)
	input_dict = zeep.helpers.serialize_object(payload_filter, dict)
	allCheckedInFilters =  json.loads(json.dumps(input_dict))
	
	onlypayloadFilter2s = allCheckedInFilters['payloadFilter2s']
	onlyloginspection = allCheckedInFilters['logInspectionRules']
	onlyintegrityMonitoring = allCheckedInFilters['integrityRules']
	
	one_sc_cache = {}
	one_sc_cache['IPSRules'] = onlypayloadFilter2s
	one_sc_cache['LogInspectionRules'] = onlyloginspection
	one_sc_cache['IntegrityMonitoring'] = onlyintegrityMonitoring
	
	ipsList = getTBUIDwithIdentifier(onlypayloadFilter2s)
	liList = getTBUIDwithIdentifier(onlyloginspection)
	imList = getTBUIDwithIdentifier(onlyintegrityMonitoring)
		
	one_sc_cache['IPSRules'] = ipsList	
	one_sc_cache['LogInspectionRules'] = liList
	one_sc_cache['IntegrityMonitoring'] = imList
	
	
	with open('rules_cache_all.txt', 'w', encoding='utf-8') as outfile:
		outfile.write(json.dumps(onlypayloadFilter2s))
	
	if filter_file[0] != "all":
		requiredPayloadFilter2s = []
		for onefilter in onlypayloadFilter2s:
			if onefilter['identifier'] in filter_file:
				requiredPayloadFilter2s.append(onefilter)
	
		with open('rules_cache.txt', 'w', encoding='utf-8') as outfile:
			outfile.write(json.dumps(requiredPayloadFilter2s))
	else:
		with open('rules_cache.txt', 'w', encoding='utf-8') as outfile:
			outfile.write(json.dumps(onlypayloadFilter2s))
			
	with open('rules_cache.txt') as f:
		data = json.load(f)
	rules_dict = {}
	for onerule in data:
		rules_dict[onerule['TBUID']] = onerule
	with open('rules_cache.json', 'w') as fp:
		json.dump(rules_dict, fp, indent=4)
		
	with open('rules_cache_all.txt') as f:
		data = json.load(f)
	rules_dict = {}
	for onerule in data:
		rules_dict[onerule['TBUID']] = onerule
	with open('rules_cache_all.json', 'w') as fp:
		json.dump(rules_dict, fp, indent=4)
		
	with open('all_rules_in_sc.json', 'w') as fp:
		json.dump(one_sc_cache, fp, indent=4)
			
	print('Required rule details stored in rules_cache.txt')

def getTBUIDwithIdentifier(filterType):
	ruleList = []
	for onefilter in filterType:
		tempRule = {}
		tempRule[onefilter['TBUID']] = onefilter['identifier']
		ruleList.append(tempRule)

	return ruleList

def get_rule_list(zeep_client, session_id):
	return zeep_client.service.DPIRuleRetrieveAll(sID=session_id)
	
def pcap_info_for_rules(rules, qa_client):
	
	pcap_info = {}
	for key in rules:
		pcapinfo = getPcapInfo(qa_client, key, username, password)
		pcap_info[key] = pcapinfo
	
	with open('pcap_info.json', 'w') as fp:
		json.dump(pcap_info, fp, indent=4)
		
	return pcap_info
	
def filter_results(rule_list, string_literal):
	new_rule_list = []
	for rule in rule_list:
		if string_literal in rule['name'].lower():
			new_rule_list.append(rule)
	return new_rule_list
	
def getPcapInfo(client, filterTBUID, username, password):
	print("Logging in to SOAP QA Centre")
	pcapinfo = client.service.getPcapInfo(in0=filterTBUID, in1=CLASSNAME_PAYLOADFILTER2, in2=username, in3=password)
	return zeep.helpers.serialize_object(pcapinfo, dict)
	
def getPcapURL(client, pcapinfo, username, password):
	pcapTBUID = pcapinfo['pcapTBUID']
	print('Getting pcap URL for '+pcapTBUID)
	print("Logging in to SOAP QA Centre")
	return client.service.getPcapUrl(in0=pcapTBUID, in1=username, in2=password)
	
def downloadPcap(pcapinfo, identifier):
	pcapURL = getPcapURL(qa_client, pcapinfo, username, password)
	
	#Use the folder name as per preference
	folder_name = identifier
	#folder_name = pcapinfo['payloadFilterTBUID']
	
	filepath = checkDirectories(pcapURL, folder_name, pcapinfo['pcapType'], pcapinfo['pcapName'])
	if filepath == "skip":
		print("Not downloading this pcap")
	else:
		url = SERVER + '/' + pcapURL
		r = requests.get(url, allow_redirects=True)
		pcapfile = os.path.splitext(pcapURL)[0]
		open(filepath, 'wb').write(r.content)
		
def download_each_pcap(pcap_info, qa_client, rules):
	for key in pcap_info:
		rulepcapinfo = pcap_info[key]
		identifier = rules[key]['identifier']
		for eachrulepcapinfo in rulepcapinfo:
			downloadPcap(eachrulepcapinfo, identifier)
			
	
def checkDirectories(pcapURL, filtertbuid, pcaptype, pcapname):
	pcapfile = os.path.splitext(pcapURL)[0]
	print("pcap name")
	print(pcapname)
	print(pcapfile)
	if pcaptype == 0:
		filename = "pcaps/"+filtertbuid+"/block/"+pcapname+".pcap"
	elif pcaptype == 2:
		filename = "pcaps/"+filtertbuid+"/pass/"+pcapname+".pcap"
	else:
		print("Skipping this pcap")
		filename = "skip"
		return filename
	if not os.path.exists(os.path.dirname(filename)):
		try:
			os.makedirs(os.path.dirname(filename))
			return filename
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	return filename


# Mimics logging in as a user to the DSM GUI
# Note that this is distinct from logging into SOAP or REST, and is mainly used when we need to access functions
#   that do not have APIs
def login_securitycenter_gui(session, credentials, login_url):
	print("Logging in to DSM GUI")
	username, password = credentials
	data = {"username": username, "password": password}
	response = session.post(login_url, data=data)
	if response.status_code != 200:
		print("Problem logging on, please check Security Center status")
		print(f"Status code: {response.status_code}")
		return 0
	print(response.text)
	rID = re.search(r"window\.sessionStorage\.setItem\('rID','([A-Z0-9]*)'\)", response.text)
	if not rID:
		print("Problem getting session token, please check Security Center status")
		return 0
	return rID.group(1)

if __name__ == '__main__':
	main()
