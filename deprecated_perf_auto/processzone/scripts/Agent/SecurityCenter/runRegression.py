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
from json2html import *
from subprocess import PIPE, run
import re
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", action="store", help="IP address of DSM")
    parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
    parser.add_argument("-p", "--path", action="store", help="Path to pcap folder")
    parser.add_argument("-r", "--rule", action="store", help="Rule Indentifier to run PCAP for")
    parser.add_argument("-t", "--time", action="store", help="Time to wait between replay")
    parser.add_argument("--teams", type=str, help="Teams notification")
    parser.add_argument("--build_user", type=str, help="Build User")
    parser.add_argument("--jenkins_url", type=str, help="Jenkins URL")
    args = parser.parse_args()

    urllib3.disable_warnings()
    sleepTime = args.time
    dsm_ip = args.ip

    wsdl_url = f"https://{dsm_ip}:4119/webservice/Manager?WSDL"
    policy_name = "au_testing"

    ruleIdentifiers = args.rule
    if ruleIdentifiers.lower() != "na":
        ruleIdentifiers = ruleIdentifiers.split(",")
    else:
        # with open("rule-identifiers.txt", "r") as f:
        with open(os.path.join("/tmp", "update-info", "rule-identifiers.txt"), "r") as f:
            data = f.readlines()
            ruleIdentifiers = ''.join(data)
            ruleIdentifiers = ruleIdentifiers.split(",")
            print(ruleIdentifiers)

    transport = zeep.Transport()
    transport.session.verify = False  # Bypass self-signed certificate errors
    client = zeep.Client(wsdl=wsdl_url, transport=transport)
    event_history = {}

    with requests.Session() as session:
        session.verify = False
        try:
            sID = login_SOAP(client, args.credentials)
            if not sID:
                sys.exit(-1)
            print("Login successful")

            policy_id = get_policy_id(client, sID, policy_name)

            # save_internal_ids_to_json(client, sID)

            ruleIdentifiers = apply_rule_to_policy(client, sID, policy_name, ruleIdentifiers)

            print("No problems applying rules")

            allHostsInfo = getAllHostsIds(client, sID)

            for eachruleIdentifier in ruleIdentifiers:
                ruleIdentifier = eachruleIdentifier
                searchString = args.path + '/' + ruleIdentifier + '/**/*.pcap'
                clearWarningandErrors(client, sID, allHostsInfo[0]['ID'])
                #apply_rule_to_policy(client, sID, policy_name, ruleIdentifier)

                allEventsOfRule = {}

                for filename in glob.iglob(searchString, recursive=True):
                    ipList, portList = get_connection_ids(filename)
                    replay_pcap(filename)
                    time.sleep(int(args.time))
                    events = retrieveSystemEvents(client, sID, policy_id, ruleIdentifier, portList)
                    print(events)

                    eventFound = {}
                    eventFound['message'] = events

                    if "block" in filename:
                        eventFound['pcap_type'] = "BLOCK"
                        if ("No Events" in events) or ("No events found" in events):
                            eventFound['status'] = "FAIL"
                        else:
                            eventFound['status'] = "PASS"
                    else:
                        eventFound['pcap_type'] = "PASS"
                        if ("No Events" in events) or ("No events found" in events):
                            eventFound['status'] = "PASS"
                        else:
                            eventFound['status'] = "FAIL"

                    allEventsOfRule[str(os.path.basename(filename))] = eventFound
                    clearWarningandErrors(client, sID, allHostsInfo[0]['ID'])

                event_history[ruleIdentifier] = allEventsOfRule

            client.service.endSession(sID=sID)
            client.transport.session.close()
            print("No problems uploading or applying update package, all tests passed")

            print(event_history)
            eventtext = pcap_reg_status(event_history)
            print("eventtext: {}".format(eventtext))
            filename = os.path.join("/tmp", "eventtext.txt")
            with open(filename, 'w') as f:
                f.write(eventtext)
            send_teams_notification(args.teams, filename, args.jenkins_url, args.build_user)
            htmlcode = json2html.convert(json=event_history)
            print(htmlcode)
            endTags = ["</body>", "</html>"]
            htmlcode = htmlcode + (''.join(endTags))

            with open(os.path.join("/tmp", "pcap_regression_report.html"), 'a') as f:
                f.write(htmlcode)

            print("Regression completed Successfully")


        except (zeep.exceptions.Fault, SystemExit) as e:
            print(e)
            client.service.endSession(sID=sID)
            client.transport.session.close()
            print("\nError applying custom configurations, exiting")
            sys.exit(-1)

# event_history to text message
def pcap_reg_status(jsonstr):
    text = ''
    # obj = json.loads(jsonstr, strict=False)
    pass_count = 0
    fail_count = 0
    pass_rule = 0
    fail_rule = 0
    for rule in jsonstr.items():
        rpc = 0
        rfc = 0
        for pcap in rule[1].items():
            if pcap[1]['status'] == 'FAIL':
                fail_count += 1
                rfc += 1
            else:
                pass_count += 1
                rpc += 1
        if rfc == 0:
            pass_rule += 1
        else:
            fail_rule += 1
            text += rule[0] + ' ' + str(rfc) + ' FAILED PCAP\n'
    text = str(pass_rule) + ' PASSED RULE\n' + str(fail_rule) + ' FAILED RULE (' + str(fail_count) + ' PCAP FAILED)\n\nFailed:\n' + text
    return text

# Logs in to the SOAP API
def login_SOAP(client, credentials):
    print("Logging in to SOAP")
    username, password = credentials
    return client.service.authenticate(username=username, password=password)

def clearWarningandErrors(client, sID, hostIDs):
    return client.service.hostClearWarningsErrors(hostIDs=hostIDs, sID=sID)

# Returns the internal IDs for each of the identifiers
def save_internal_ids_to_json(zeep_client, sID):
    dpi_dict = {}
    response = zeep_client.service.DPIRuleRetrieveAll(sID=sID)
    for eachresponse in response:
        dpi_dict[eachresponse['identifier']] = eachresponse['ID']

    with open('/tmp/internal_id.json', 'w') as fp:
        json.dump(dpi_dict, fp, indent=4)

# Get all hosts IDS
def getAllHostsIds(client, sID):
    print("Getting All Hosts IDs")
    hostsInfoResponse = client.service.hostRetrieveAll(sID=sID)
    return hostsInfoResponse

def apply_rule_to_policy(client, sID, policy_name, rules):
    print(f"Finding policy ID for policy {policy_name}")
    policy_id = get_policy_id(client, sID, policy_name)
    if not policy_id:
        raise zeep.exceptions.Fault(
            message=f"ERROR: Policy {policy_name} not found on the DSM, please double check if the policy has been created")
    print(f"Found, policy ID is {policy_id}")
    print("Attempting to apply rules to policy")
    identifiers = []
    identifiers.extend(rules)

    with open('/tmp/rule_summary.json') as f:
        reqdrules = json.load(f)

    identifiers.extend(reqdrules['required_identifier'])

    #dpi_rule_ids = get_dpi_ids(identifiers)
    dpi_rule_ids, dpi_rules_to_iterate, internal_id_mappings = find_internal_ids_from_dsm(client, sID, identifiers)
    print(dpi_rule_ids)
    print(internal_id_mappings)
    integrity_rule_ids = []
    log_inspection_rule_ids = []
    upload_policy(client, sID, policy_name, policy_id, dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids)
    response = client.service.securityProfileRetrieveByName(name=policy_name, sID=sID)
    print("Policy Data: ")
    print(response)
    return dpi_rules_to_iterate

# Returns the internal ID for the given policy
# Also useful to check if policies have been uploaded properly, or if policies are already on the DSM
def get_policy_id(client, sID, policy_name):
    return client.service.securityProfileRetrieveByName(name=policy_name, sID=sID)["ID"]

# Returns the internal IDs for each of the identifiers
def find_internal_ids_from_dsm(zeep_client, sID, identifiers):
    internal_id_mappings = {}
    dpi_rule_ids = []
    dpi_rules_to_iterate = []
    response = zeep_client.service.DPIRuleRetrieveAll(sID=sID)
    for rule in response:
        if rule["identifier"] in identifiers:
            dpi_rules_to_iterate.append(rule["identifier"])
            dpi_rule_ids.append(rule["ID"])
            internal_id_mappings[rule["identifier"]] = rule["ID"]

    '''
    integrity_rule_ids = []
    response = zeep_client.service.integrityRuleRetrieveAll(sID=sID)
    for rule in response:
        if rule["identifier"] in identifiers:
            integrity_rule_ids.append(rule["ID"])
            internal_id_mappings[rule["identifier"]] = rule["ID"]

    log_inspection_rule_ids = []
    response = zeep_client.service.logInspectionRuleRetrieveAll(sID=sID)
    for rule in response:
        if rule["identifier"] in identifiers:
            log_inspection_rule_ids.append(rule["ID"])
            internal_id_mappings[rule["identifier"]] = rule["ID"]
    '''

    return dpi_rule_ids, dpi_rules_to_iterate, internal_id_mappings


def get_dpi_ids(identifiers):
    with open('/tmp/internal_id.json') as f:
        rules = json.load(f)

    dpi_ids = []
    for identifier in identifiers:
        dpi_ids.append(rules[identifier])
    print(dpi_ids)
    return dpi_ids

# Passing empty arrays to the three ids variables will empty the policy
def upload_policy(zeep_client, session_id, policy_name, policy_id, dpi_rule_ids, integrity_rule_ids,
                  log_inspection_rule_ids):
    sp = {"ID": policy_id, "description": "DSRU Automation Testing Policy", "name": policy_name,
          "DPIRuleIDs": {"item": dpi_rule_ids}, "DPIState": "ON", "integrityRuleIDs": {"item": integrity_rule_ids},
          "integrityState": "ON",
          "logInspectionRuleIDs": {"item": log_inspection_rule_ids}, "logInspectionState": "ON",
          "antiMalwareManualInherit": False, "antiMalwareRealTimeInherit": False, "antiMalwareScheduledInherit": False}
    return zeep_client.service.securityProfileSave(sp=sp, sID=session_id)

def retrieveSystemEvents(client, sID, policy_id, rule, portList):
    eventMessage = ""
    # timeRange = "LAST_HOUR"
    # timeRange = "LAST_24_HOURS"
    timeRange = "CUSTOM_RANGE"
    currtime = datetime.datetime.now(timezone.utc).replace(microsecond=0)
    lastoneminute = currtime - datetime.timedelta(seconds=100)
    # timeFilter = {"rangeFrom": None, "rangeTo": None, "specificTime": None, "type": timeRange}
    timeFilter = {"rangeFrom": lastoneminute, "rangeTo": currtime, "specificTime": None, "type": timeRange}
    hostFilter = {"hostGroupID": None, "hostID": None, "securityProfileID": policy_id,
                  "type": "HOSTS_USING_SECURITY_PROFILE"}
    eventIdFilter = {"id": 0, "operator": "GREATER_THAN"}
    # return client.service.systemEventRetrieveShortDescription(timeFilter, hostFilter, eventIdFilter, includeNonHostEvents=False, sID=sID)
    # return client.service.systemEventRetrieveShortDescription2(timeFilter, hostFilter, eventIdFilter, includeNonHostEvents=False, sID=sID)
    events = client.service.DPIEventRetrieve(timeFilter, hostFilter, eventIdFilter, sID=sID)
    # print(events)

    if events['DPIEvents'] == None:
        return "No Events"

    for event in events['DPIEvents']['item']:
        #print(event)
        if (rule in event['reason']):
            # print(event)
            eventMessage += "Event: " + event['reason'] + "\n"
            eventMessage += "DPI Rule ID: " + str(event['DPIRuleID']) + "\n"
            eventMessage += "Action: " + event['action'] + "\n"
            eventMessage += "\n"
    if eventMessage == "":
        eventMessage = "No events found"

    return eventMessage

def replay_pcap(pcapFile):
    print(f"Replaying pcap...{pcapFile}")

    cmd_ret = subprocess.call([
        '/bin/bash',
        '/tmp/pplay/replay_pcap.sh',
        '-p',
        pcapFile])

    if cmd_ret != 0:
        raise ChildProcessError(f"Failed to replay pcap {pcapFile}")
    else:
        print(f"Pcap {pcapFile} replayed sucessfully. Check IPS events")

def get_connection_ids(pcapFile):
    print(f"Getting connection list for pcap...{pcapFile}")
    command = ["pplay.py", "--pcap", pcapFile, "--list"]  # pplay.py --pcap pcapFile --list
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    print("Using connection ++++++++ ")
    connection_msg = result.stderr
    connection_msg = connection_msg.replace("== no sctp support", "")
    connection_msg = connection_msg.replace("# >>> Usable connection IDs:", "")
    connection_msg = connection_msg.replace("* ", "")
    connection_msg = connection_msg.replace(" # 2 simplex flows", "")

    connection_msg = connection_msg.replace("\x1b[33m", "")
    connection_msg = connection_msg.replace("\x1b[0m", "")
    connection_msg = connection_msg.replace("\x1b[32m", "")
    connection_msg = connection_msg.replace("\x1b[31m", "")

    connection_msg = connection_msg.strip()
    connection_msg = connection_msg.split("\n")
    print(type(connection_msg))
    # ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # result = ansi_escape.sub('', connection_msg)
    # connection_msg = connection_msg.rstrip("\n")
    connection_msg = [x.strip(' ') for x in connection_msg]
    print(connection_msg)

    iplist = []
    portlist = []

    connection_string = "\"" + connection_msg[0] + "\""

    if 'select yourself' in connection_msg:
        connection_string = "\""+connection_msg[0]+"\n"+"no candidate"+"\""

    command = ["echo", connection_string, ">", "/tmp/pcap_connection.txt"]  # writing connection to file
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    for eachconnection in connection_msg:
        ip_port = eachconnection.split(":")
        iplist.append(ip_port[0].strip())
        portlist.append(ip_port[-1].strip())

    return iplist, portlist

def send_teams_notification(webhook, filename, jenkins_url, build_user):
    print("called send_teams_notification...")
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "00ff00",
        "summary": "Pcap Regression Pipeline Notification",
        "sections":
            [
                {
                    "activityTitle": "Pcap Regression Pipeline - Job Number - {}".format(jenkins_url.split("/")[-2]),
                    "activitySubtitle": "Pcap Regression Status",
                    "activityImage": "https://teamsnodesample.azurewebsites.net/static/img/image5.png",
                    "facts":
                        [
                            {
                                "name": "Pcap Regression Status",
                                "value": "SUCCESS"
                            },
                            {
                                "name": "Build Run By",
                                "value": build_user
                            }
                        ],
                    "markdown": True
                },
                {
                    'text': '<p>{}</p>'.format(parse_message(filename))
                }
            ],
        "potentialAction":
            [
                {
                    "@type": "OpenUri",
                    "name": "View Jenkins Build",
                    "targets":
                        [
                            {
                                "os": "default",
                                "uri": jenkins_url
                            }
                        ]
                }
            ]
    }
    headers = {'content-type': 'application/json'}
    requests.post(webhook, data=json.dumps(message), headers=headers)

def parse_message(file_name):
    msg = ""
    with open(file_name, "r") as fout:
        for line in fout:
            msg += line
            msg += "<br>"
    return msg


if __name__ == '__main__':
    main()
