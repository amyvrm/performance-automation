#!/usr/bin/env python3

import os
import re
import zipfile
import time
from backoff_utils import exponential_backoff_sleep
import requests
import urllib3
import zeep
import xml.etree.ElementTree as ET
import simplejson as json
from string import Template
from get_machine_info import MachineInfo

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class DsmPolicy(object):
    def __init__(self, dsm_ver, jfrog_token, machine, path, policy_name, port, server_rule, client_rule, portlist_file, dsm_server):
        # dsm_ip = machine.get_dsm_public_ip()
        dsm_ip = dsm_server
        print("+ DSM IP: {} +".format(dsm_ip))
        self.header = "-" * 50
        self.policy_name = policy_name
        self.port = port
        self.pkg_path = path
        urllib3.disable_warnings()
        self.wsdl_url = f"https://{dsm_ip}:4119/webservice/Manager?WSDL"
        self.login_url = f"https://{dsm_ip}:4119/SignIn.screen"
        self.policy_url = f"https://{dsm_ip}:4119/SecurityProfiles.screen"
        self.import_policy_url = f"https://{dsm_ip}:4119/ImportWizard.screen"
        self.uname = machine.get_dsm_user()
        self.pwd = machine.get_dsm_pwd()
        self.dsm_ver = dsm_ver
        self.cred = BearerAuth(jfrog_token)
        self.server_rule_file = server_rule
        self.client_rule_file = client_rule
        self.port_list_file = portlist_file
        self.connect()

    def connect(self):
        transport = zeep.Transport()
        transport.session.verify = False  # Bypass self-signed certificate errors
        for retry in range(3):
            print("Attempt-{} to Create DSM Connection...".format(retry+1))
            try:
                self.client = zeep.Client(wsdl=self.wsdl_url, transport=transport)
                break
            except Exception as ex:
                print("Exception!!! {}".format(ex))
                exponential_backoff_sleep(retry, base_delay=5, max_delay=20)

        self.session = requests.Session()
        self.session.verify = False

        self.sID = self.client.service.authenticate(username=self.uname, password=self.pwd)
        self.rID = self.login_gui()
        print("Login successful")

    def login_gui(self):
        data = {"username": self.uname, "password": self.pwd}
        response = self.session.post(self.login_url, data=data)
        if response.status_code != 200:
            print("Problem logging on, please check DSM status")
            print("Status code: {}".format(response.status_code))
            return 0
        rID = re.search(r"window\.sessionStorage\.setItem\('rID','([A-Z0-9]*)'\)", response.text)
        if not rID:
            print("Problem getting session token, please check DSM status")
            return 0
        return rID.group(1)

    def get_policy(self):
        if self.dsm_ver.startswith("20"):
            return os.path.join("templates", "DSM20Policy", "perf_policy.xml")
        elif self.dsm_ver.startswith("12"):
            return os.path.join("templates", "DSM12Policy", "perf_policy.xml")
        else:
            raise Exception("Error!!! Not able to get DSM version")

    def upload_basic_policy(self, change_policy=False):
        fname = self.get_policy()
        if change_policy:
            dest_fname = os.path.join("templates", "perf_policy_changed.xml")
            fname = self.override_portlist(fname, dest_fname)

        xml_root = ET.parse(fname)
        xml_root = xml_root.getroot()
        policy_xml = ET.tostring(xml_root, encoding='utf8', method='xml')
        self.upload_custom_policy(policy_xml)
        print("No problems uploading policy {}, all tests passed".format(self.policy_name))

        policy_id = self.client.service.securityProfileRetrieveByName(name=self.policy_name, sID=self.sID)["ID"]
        get_all_host = self.client.service.hostRetrieveAll(sID=self.sID)

        for idx, host in enumerate(get_all_host):
            host_id = host['ID']
            self.client.service.securityProfileAssignToHost(securityProfileID=policy_id, hostIDs=host_id, sID=self.sID)
            exponential_backoff_sleep(idx, base_delay=10, max_delay=20)

        print("No problems applying policy {}, to all hosts".format(self.policy_name))

    def upload_custom_policy(self, policy_xml_data):
        print("Uploading {} xml file".format(self.policy_name))
        response = self.session.get("{}?type=SecurityProfile".format(self.import_policy_url))
        guid = re.search(r'id="guid" name="guid" type="hidden" value="([-A-Z0-9]*)"', response.text).group(1)
        print("guid: {}".format(guid))
        data = {"guid": (None, guid), "step": (None, "0"), "rID": (None, self.rID), "cmdArguments": (None, ""),
                "command": (None, "NEXTORFINISH"), "changed": (None, "false"),
                "type": (None, "SecurityProfile"), "filePath": (None, ""),
                "file": ("policy", policy_xml_data, "text/xml"),
                "parentProfileID": (None, ""), "parentProfileID_tree_viewstate": (None, "tvi_1"),
                "parentProfileID_tree_selected": (None, "0"), "certificatePurpose": (None, "2"),
                "finish": (None, "Next >")}
        self.session.post(self.import_policy_url, files=data)
        exponential_backoff_sleep(0, base_delay=10, max_delay=15)

        del data["file"]
        del data["finish"]
        data["step"] = (None, "1")
        self.session.post(self.import_policy_url, data=data)
        exponential_backoff_sleep(0, base_delay=5, max_delay=10)

        data["step"] = (None, "2")
        self.session.post(self.import_policy_url, data=data)
        exponential_backoff_sleep(0, base_delay=15, max_delay=20)

    def override_portlist(self, source_fname, dest_fname):
        print("{0}\n# Updating policy to override rule port list with port {1} #\n{0}".format("#" * 50, self.port))
        port1, port2 = "PortLists", "PortList"
        with open(os.path.join(self.port_list_file), "r") as f:
            port_list = json.load(f)
        print("Length of port list: {}".format(len(port_list)))

        tree = ET.parse(source_fname)
        portlist = tree.find(port1)
        count = 0
        for port_info in port_list:
            if port_info:
                count += 1
                print("Updated port_list perf test_{} with port {}".format(count, self.port))
                child = ET.SubElement(portlist, port2)
                child.set("id", port_info["id"])
                gchild = ET.SubElement(child, "TBUID")
                gchild.text = port_info["TBUID"]
                gchild = ET.SubElement(child, "Name")
                gchild.text = "perf test_{}".format(count)
                gchild = ET.SubElement(child, "Description")
                gchild.text = "Assigning 5001 port for perf test"
                gchild = ET.SubElement(child, "Items")
                gchild.text = self.port
                gchild = ET.SubElement(child, "Version")
                gchild.text = port_info["Version"]
                gchild = ET.SubElement(child, "UserEdited")
                gchild.text = "false"

        if os.path.exists(dest_fname):
            os.remove(dest_fname)
        tree.write(dest_fname)
        return dest_fname

    def download_package(self, package_url):
        package_name = package_url.rsplit("/")[-1]
        response = self.session.get(package_url, auth=self.cred)

        package_path = os.path.join("update-packages", package_name)
        if not os.path.isdir("update-packages"):
            os.mkdir("update-packages")
        with open(package_path, "wb") as f:
            f.write(response.content)

        # Program also handles .zip files, though sample updates should usually be .3bsu and not .zip
        if os.path.splitext(package_name)[-1] == ".zip":
            with zipfile.ZipFile(package_path, 'r') as fz:
                fz.extractall("update-packages")
            os.remove(package_path)

    def apply_pkg_create_applied_rule_list(self, rule_file):
        response = self.upload_package()
        update_id = response["ID"]
        print("Upload successful, update package ID is {}".format(update_id))

        print("Saving dsru content information to update-info\n")
        if not os.path.exists("update-info"):
            os.makedirs("update-info")
        with open(os.path.join("update-info", "dsm-added_rules.txt"), "w") as f:
            f.write(response["contentSummary"])

        print("Here are the rules that were added/updated on the DSM:")
        print(response["contentSummary"])
        contentSummary = response["contentSummary"]

        if rule_file == os.path.join("update-info", "rule-identifiers.txt"):
            identifiers = [x[0] for x in re.findall("^\s*(\d+) - (.*)$", response["contentSummary"], re.MULTILINE)]
            with open(rule_file, "w") as f:
                f.write(",".join(identifiers))
        else:
            identifiers = rule_file
            print(f"Rule identifiers are {identifiers}\n")
            with open(os.path.join("update-info", "rule-identifiers.txt"), "w") as f:
                f.write(",".join(identifiers))

        print("Attempting to apply update package", flush=True)
        response = self.client.service.securityUpdateApply(ID=update_id, detectOnly=False, sID=self.sID)
        with open(os.path.join("update-info", f"dsm-assigned_rules.txt"), "w") as f:
            f.write(response["detailedSummary"])
        print("Update package applied successfully")
        print(f"Details saved to update-info.txt\n")
        print("No problems uploading or applying update package, all tests passed")
        print(response["detailedSummary"])
        return contentSummary, identifiers

    def upload_package(self):
        # pkg_name = [filename for filename in os.listdir("update-packages")
        pkg_name = [filename for filename in os.listdir(self.pkg_path) if os.path.splitext(filename)[-1] == ".3bsu" or
                                                                      os.path.splitext(filename)[-1] == ".encrypted" or
                                                                      os.path.splitext(filename)[-1] == ".dsru"][0]
        package_path = os.path.join("update-packages", pkg_name)
        with open(package_path, "rb") as f:
            update_package = f.read()
        print("Uploading {} to DSM".format(pkg_name), flush=True)
        return self.client.service.securityUpdateStore(securityUpdate=update_package, fileName=pkg_name, sID=self.sID)

    def apply_rule(self, scenario_name, rule_list=False):
        if rule_list:
            identifiers = rule_list
        elif scenario_name == "Server Upload" or scenario_name == "Server Download":
            print("{0}{0}\n# With All Server side rule #\n{0}{0}\n".format(self.header))
            with open(self.server_rule_file, "r") as f:
                identifiers = f.read().split(",")
        elif scenario_name == "Client Download":
            print("{0}{0}\n# With All Client side rule #\n{0}{0}\n".format(self.header))
            with open(self.client_rule_file, "r") as f:
                identifiers = f.read().split(",")

        # The rule identifier is not the same as the internal rule ID - the former is guaranteed to be unique across
        #   the entire system, while the latter is only unique within its rule type
        # When using the API, the system only accepts the latter for commands
        print("Finding internal IDs for all rules", flush=True)
        dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids, internal_id_mappings = self.find_internal_ids(identifiers)
        policy_id = self.client.service.securityProfileRetrieveByName(name=self.policy_name, sID=self.sID)["ID"]
        if not policy_id:
            msg = "ERROR: Policy {} not found on the DSM, please check the policy".format(self.policy_name)
            raise zeep.exceptions.Fault(message=msg)
        print("FOUND: Policy ID is {}".format(policy_id))

        print("Attempting to apply rules to policy", flush=True)
        self.upload_policy(policy_id, dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids)
        response = self.client.service.securityProfileRetrieveByName(name=self.policy_name, sID=self.sID)
        print("Appled Rule info: {}".format(response))
        print("Waiting for policies to apply", flush=True)
        exponential_backoff_sleep(1, base_delay=30, max_delay=60)
        self.update_ports(policy_id)

        response = self.client.service.hostRetrieveAll(sID=self.sID)
        ids = [r["ID"] for r in response]
        self.client.service.hostClearWarningsErrors(ids, sID=self.sID)
        # We can now grab the policy XML information
        # This is useful for two reasons: first, we can upload it to Nexus in case we ever want to manually upload it
        #   to a DSM for testing; and second, we can use it as a base for a custom policy if any of the new rules
        #   require configurations
        policy_xml = self.export_policy_xml(policy_id)

        # We collect a list of rules that require configuration to check if any of new ones require it
        print("creating custom policy")
        payloadfilter2s, intergrityrules, loginspectionrules = DsmPolicy.get_require_configuration_ids(policy_xml)
        if len(payloadfilter2s) == 0 and len(intergrityrules) == 0 and len(loginspectionrules) == 0:
            print("No configuration rules present, skipping operation *apply custom policy*.")
        else:
            new_policy_xml = DsmPolicy.create_custom_policy(policy_xml, payloadfilter2s, intergrityrules, loginspectionrules,
                                                  internal_id_mappings)
            self.upload_custom_policy(new_policy_xml)

        # It only takes about 5 seconds to apply, but better safe than sorry
        print("Waiting for policies to apply completely to all hosts...")
        exponential_backoff_sleep(1, base_delay=30, max_delay=60)

        # Finally, once the policy has been uploaded and applied, we check all the computers with the policy applied
        #   to see what their status is
        print("Checking computer status")
        for retry in range(2):
            try:
                status = self.check_host_status(policy_id)
                events = self.retrieveSystemEvents(policy_id)
                if not status:
                    msg = "ERROR: Policy not applied to any hosts, please apply the policy to at least one host"
                    raise zeep.exceptions.Fault(message=msg)
                break
            except Exception as ex:
                print("Error!!! [{}] Failed to get host status".format(ex))

        with open(os.path.join("update-info", "status.txt"), "a+") as f:
            f.write(status + "\n" + events + "\n")

        print("No problems uploading or applying update package, all tests passed")
        return identifiers

    # Returns the internal IDs for each of the identifiers
    def find_internal_ids(self, identifiers):
        internal_id_mappings = {}
        dpi_rule_ids = []
        response = self.client.service.DPIRuleRetrieveAll(sID=self.sID)
        for rule in response:
            if rule["identifier"] in identifiers:
                dpi_rule_ids.append(rule["ID"])
                internal_id_mappings[rule["identifier"]] = rule["ID"]

        integrity_rule_ids = []
        response = self.client.service.integrityRuleRetrieveAll(sID=self.sID)
        for rule in response:
            if rule["identifier"] in identifiers:
                integrity_rule_ids.append(rule["ID"])
                internal_id_mappings[rule["identifier"]] = rule["ID"]

        log_inspection_rule_ids = []
        response = self.client.service.logInspectionRuleRetrieveAll(sID=self.sID)
        for rule in response:
            if rule["identifier"] in identifiers:
                log_inspection_rule_ids.append(rule["ID"])
                internal_id_mappings[rule["identifier"]] = rule["ID"]

        return dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids, internal_id_mappings

    def upload_policy(self, policy_id, dpi_rule_ids, integrity_rule_ids, log_inspection_rule_ids):
        sp = {"ID": policy_id, "description": "DSRU Automation Testing Policy", "name": self.policy_name,
              "DPIRuleIDs": {"item": dpi_rule_ids}, "DPIState": "ON", "integrityRuleIDs": {"item": integrity_rule_ids},
              "integrityState": "ON",
              "logInspectionRuleIDs": {"item": log_inspection_rule_ids}, "logInspectionState": "ON",
              "antiMalwareManualInherit": False, "antiMalwareRealTimeInherit": False,
              "antiMalwareScheduledInherit": False}
        return self.client.service.securityProfileSave(sp=sp, sID=self.sID)

    def update_ports(self, policy_id):
        print("{0}\n# Updating policy to override rule port with {1} port #\n{0}".format("#" * 50, self.port))
        con1, con2 = "ConnectionTypes", "ConnectionType"
        policy_xml_str = self.export_policy_xml(policy_id)
        try:
            root = ET.fromstring(policy_xml_str)
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            print("Ensure the XML is well-formed and properly encoded.")
            raise

        count = 0
        for index, con in enumerate(root.iter(con2), 1):
            print("{}. ConnectionType ID: {}".format(index, con.attrib['id']))
            if con.find('Ports').text:
                count += 1
                DsmPolicy.override_port(count, policy_id, root, con.attrib['id'], con.find('PortType').text, self.port)
        print("-" * 50)
        over1, over2 = "ConnectionTypeOverrides", "ConnectionTypeOverride"
        for over in root.iter(over2):
            print("Overridden Port ID:{}, Ports:{}".format(over.find('ConnectionTypeID').text, over.find('Ports').text))

        policy_xml = ET.tostring(root, encoding='utf8', method='xml')
        self.upload_custom_policy(policy_xml)
        print(f"Waiting after changing perf port {self.port}...")
        exponential_backoff_sleep(1, base_delay=15, max_delay=30)

    def export_policy_xml(self, policy_id):
        data = {"rID": self.rID, "cmdArguments": policy_id, "command": "EXPORT"}
        response = self.session.post(self.policy_url, data=data)
        # For some reason, get extra newline when exporting this way so need to clean the empty lines
        return "\n".join([line.rstrip() for line in response.text.splitlines() if line])

    @staticmethod
    def override_port(count, policy_id, tree, con_id, port_type, port):
        over1, over2 = "ConnectionTypeOverrides", "ConnectionTypeOverride"
        override = tree.find(over1)
        id = len(override) + 1
        print("{}. Override Port id: {}, port: {}".format(count, id, port))
        child = ET.SubElement(override, over2)
        child.set("id", str(id))
        t = ET.SubElement(child, "SecurityProfileID")
        t.text = str(policy_id)
        t = ET.SubElement(child, "HostID")
        t.set("isNull", "true")
        t = ET.SubElement(child, "ConnectionTypeID")
        t.text = str(con_id)
        t = ET.SubElement(child, "OverridePorts")
        t.text = "true"
        t = ET.SubElement(child, "PortType")
        t.text = str(port_type)
        t = ET.SubElement(child, "Ports")
        t.text = str(port)
        t = ET.SubElement(child, "OverrideMetadata")
        t.text = "false"
        t = ET.SubElement(child, "RecommendationsMode")
        t.set("isNull", "true")

    @staticmethod
    def get_require_configuration_ids(policy_xml):
        new_policy_xml = policy_xml
        # xml_root = new_policy_xml.getroot()
        xml_root = ET.fromstring(new_policy_xml)
        policy_id = xml_root.find("SecurityProfiles").find("SecurityProfile").attrib["id"]

        override_count = 1000  # Just so it doesn't interfere with lower-valued override ids
        metadata_override_count = 7000
        payloadfilter2s = []
        intergrityrules = []
        loginspectionrules = []

        rule_types = ["PayloadFilter2s", "IntegrityRules", "LogInspectionRules"]
        metadata_types = ["PayloadFilter2Metadatas", "IntegrityRuleMetadatas", "LogInspectionRuleMetadatas"]

        allpayloadfilter2s = xml_root.find("PayloadFilter2s")
        for eachpayloadfilter2s in allpayloadfilter2s:
            if eachpayloadfilter2s.find("RequiresConfiguration").text == "true":
                payloadfilter2s.append(eachpayloadfilter2s.attrib["id"])

        allintergrityrules = xml_root.find("IntegrityRules")
        for eachintergrityrules in allintergrityrules:
            if eachintergrityrules.find("RequiresConfiguration").text == "true":
                intergrityrules.append(eachintergrityrules.attrib["id"])

        allloginspectionrules = xml_root.find("LogInspectionRules")
        for eachloginspectionrules in allloginspectionrules:
            if eachloginspectionrules.find("RequiresConfiguration").text == "true":
                loginspectionrules.append(eachloginspectionrules.attrib["id"])

        return payloadfilter2s, intergrityrules, loginspectionrules

    @staticmethod
    def create_custom_policy(policy_xml, payloadfilter2s, intergrityrules, loginspectionrules, internal_id_mappings):
        new_policy_xml = policy_xml
        # xml_root = new_policy_xml.getroot()
        xml_root = ET.fromstring(new_policy_xml)
        policy_id = xml_root.find("SecurityProfiles").find("SecurityProfile").attrib["id"]

        override_count = 1000  # Just so it doesn't interfere with lower-valued override ids
        metadata_override_count = 7000

        rule_types = ["PayloadFilter2s", "IntegrityRules", "LogInspectionRules"]
        metadata_types = ["PayloadFilter2Metadatas", "IntegrityRuleMetadatas", "LogInspectionRuleMetadatas"]

        payloadfilter2s_metadata_ids = []
        intergrityrules_metadata_ids = []
        loginspectionrules_metadata_ids = []

        for eachpayloadfilter2s in payloadfilter2s:
            payloadfilter2s_metadata_ids.append(DsmPolicy.get_metadata_id(xml_root, metadata_types[0], eachpayloadfilter2s))

        for eachintergrityrules in intergrityrules:
            intergrityrules_metadata_ids.append(DsmPolicy.get_metadata_id(xml_root, metadata_types[1], eachintergrityrules))

        for eachloginspectionrules in loginspectionrules:
            loginspectionrules_metadata_ids.append(DsmPolicy.get_metadata_id(xml_root, metadata_types[2], eachloginspectionrules))

        for rule_type in rule_types:

            with open(os.path.join("templates", f"{rule_type[:-1]}Override.txt")) as f:
                override = Template(f.read())

            if rule_type == "PayloadFilter2s":
                require_config_ids = payloadfilter2s
                metadata_override_ids = payloadfilter2s_metadata_ids
            elif rule_type == "IntegrityRules":
                require_config_ids = intergrityrules
                metadata_override_ids = intergrityrules_metadata_ids
            else:
                require_config_ids = loginspectionrules
                metadata_override_ids = loginspectionrules_metadata_ids

            for identifier in require_config_ids:

                rule_id = list(internal_id_mappings.keys())[list(internal_id_mappings.values()).index(int(identifier))]

                if os.path.exists("templates/" + f"{rule_type[:-1]}MetadataOverrides/" + f"{rule_id}.txt"):
                    print(rule_id + '.txt found file')
                    with open(
                            os.path.join("templates/" + f"{rule_type[:-1]}MetadataOverrides", f"{rule_id}.txt")) as mf:
                        override_metadata = Template(mf.read())
                else:
                    print('Configuration missing')
                    continue

                internal_id = identifier
                override_data = {"rule_type": rule_type[:-1], "override_id": override_count,
                                 "security_profile_id": policy_id, "filter_id": internal_id}
                override_metadata_data = {"metadata_override_id": metadata_override_count,
                                          "security_profile_id": policy_id, "filter_metadata_id": metadata_override_ids[
                        require_config_ids.index(identifier)]}
                override_element = ET.fromstring(override.substitute(override_data))
                override_metadata_element = ET.fromstring(override_metadata.substitute(override_metadata_data))

                xml_root.find(f"{rule_type[:-1]}Overrides").append(override_element)
                xml_root.find(f"{rule_type[:-1]}MetadataOverrides").append(override_metadata_element)

                override_count += 1
                metadata_override_count += 1

        xmlstring = ET.tostring(xml_root, encoding='utf8', method='html')
        return xmlstring

    @staticmethod
    def get_metadata_id(xml, filter_type, filter_id):
        metadata_id = None
        findIdTag = None

        if filter_type == "PayloadFilter2Metadatas":
            findIdTag = "PayloadFilter2ID"
        elif filter_type == "IntegrityRuleMetadatas":
            findIdTag = "IntegrityRuleID"
        else:
            findIdTag = "LogInspectionRuleID"

        allfilter_metadata = xml.find(filter_type)
        for eachfilter_metadata in allfilter_metadata:
            if eachfilter_metadata.find(findIdTag).text == filter_id:
                metadata_id = eachfilter_metadata.attrib["id"]
        return metadata_id

    # Returns the status for all hosts with the given policy applied
    def check_host_status(self, policy_id):
        response = self.client.service.hostRetrieveAll(sID=self.sID)
        message = ""
        for host in response:
            if host["securityProfileID"] == policy_id:
                status = self.client.service.hostGetStatus(id=host["ID"], sID=self.sID)
                # Status can be green, yellow or red depending on the severity of the problem
                # Even if status is not green, pipeline will continue (but a note will be added to the slack message)
                message += host['platform'] + ': ' + status['overallStatus']
                if status["overallStatus"] != "Managed (Online)":
                    print(f"{host['platform']} : Issue applying policy, host state is {status['overallStatus']}")
                    message += " :red_circle:"
                else:
                    print("No problems with status, policy applied successfully")
                    message += ", no issues :green_circle:"  # Just makes message a bit clearer
                message += "\n"
        time.sleep(5)
        return message

    def retrieveSystemEvents(self, policy_id):
        eventMessage = ""
        # timeRange = "LAST_HOUR"
        timeRange = "LAST_24_HOURS"
        timeFilter = {"rangeFrom": None, "rangeTo": None, "specificTime": None, "type": timeRange}
        hostFilter = {"hostGroupID": None, "hostID": None, "securityProfileID": policy_id,
                      "type": "HOSTS_USING_SECURITY_PROFILE"}
        eventIdFilter = {"id": 0, "operator": "GREATER_THAN"}
        events = self.client.service.systemEventRetrieve(timeFilter, hostFilter, eventIdFilter,
                                                         includeNonHostEvents=False, sID=self.sID)
        for event in events['systemEvents']['item']:
            if event['type'] == 'Error' and ("Rule Compiler Failed" in event['event'] or "Rules Failed" in event[
                'event']) and "DS_Agent.Log" not in event['description'] and "Expose Hidden Error Rule" not in event[
                'description']:
                eventMessage += "Event: " + event['event'] + "\n"
                eventMessage += "Event description: " + event['description'] + "\n"
                eventMessage += "Event Host: " + event['target'] + "\n"
                eventMessage += "\n\n"
        if eventMessage == "":
            eventMessage = "No rules have errors."
        return eventMessage

    def clean_rules_from_dsm(self):
        policy_id = self.client.service.securityProfileRetrieveByName(name=self.policy_name, sID=self.sID)["ID"]
        print("Attempting to clear all applied rules", flush=True)
        self.upload_policy(policy_id, [], [], [])
        response = self.client.service.securityProfileRetrieveByName(name=self.policy_name, sID=self.sID)
        print("Appled Rule info: {}".format(response))
        print("Waiting 30 secs, for policies to apply", flush=True)
        time.sleep(30)

    def disconnect(self):
        print("Disconnecting DSM")
        self.client.service.endSession(sID=self.sID)
        self.client.transport.session.close()

if __name__ == '__main__':
    pass