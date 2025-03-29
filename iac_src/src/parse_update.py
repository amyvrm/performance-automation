# Parses the information stored in the DSRU update packages

import os
import json
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import sys

def main():
    for filename in os.listdir(sys.argv[1]):
        if os.path.splitext(filename)[-1] == ".decrypted":
            parse(os.path.join(sys.argv[1], filename))

def parse(update_package_loc):
    # Even though the extension is .decrypted, the files themselves are zipfiles which contain the xml data inside them
    with zipfile.ZipFile(update_package_loc) as zipped_update:
        package_xml_fileinfo = [fileinfo for fileinfo in zipped_update.infolist() if "3bsu2" in fileinfo.filename]
        if not package_xml_fileinfo:
            print(f"{update_package_loc} is not an update package, skipping")
            return

        package_xml = zipped_update.read(package_xml_fileinfo[0])

        # Update package has all the information stored under the VSU tag
        # The tags under it are XSD (b64 encoded schema definition), Info (version, date, if package is sample),
        #   PortLists (list of common ports and their corresponding programs), ConnectionTypes (list of connection protocols),
        #   the filters which are separated into groups depending on type, each with a corresponding meta
        #   (PayloadFilter2s, IntegrityRules, LogInspectionRules, and LogInspectionDecoders)
        #   DetectionRules, DetectionExpressions, RuleGroups, VDB and DeleteTargets
        package_root = ET.fromstring(package_xml)

        # List of fields that should be included as hash-only
        # NOTE: If you want all information to be uploaded, including encoded b64 rule data, use the top hash line instead
        #   This generally shouldn't be done, since it will include sensitive information, so use at your own risk
        # hash = []
        hash = ["XSD", "EngineXML", "RuleXML", "FileXML", "DecoderXML", "DetectionRuleXML", "DetectionExpressionXML", "GDL", "IconData"]

        # First, need to collect some meta information about the package
        # This is needed in order to find what rules are new from the last package, and whether or not the update is a sample one
        info_root = package_root.find("Info")
        package_date = info_root.find("Available").text
        package_version = info_root.find("Version").text
        package_type = info_root.find("Sample").text
        if package_type == "true":
            is_sample = True
        else:
            is_sample = False

        package_folder = os.path.dirname(update_package_loc)
        package_name = os.path.basename(update_package_loc).rsplit(".", 2)[0]

        changed_rules = find_new_and_updated(package_root, package_date, is_sample)

        formatted = f"The following rules were added/updated in version {package_version}\n"
        for filter_type in changed_rules:
            formatted += f"\n{filter_type}:\n"
            formatted += f"\tNew:\n" + "".join([f"\t\t{x}\n" for x in changed_rules[filter_type]["new"]])
            formatted += f"\tUpdated:\n" + "".join([f"\t\t{x}\n" for x in changed_rules[filter_type]["updated"]])

        try:
            with open(os.path.join(package_folder, package_name + ".txt"), "w", encoding='utf-8') as f:
                f.write(formatted)
            rule_ids = []
            for filter_type in changed_rules:
                for rule in changed_rules[filter_type]["new"]:
                    rule_id = rule.split(" - ")[0]
                    rule_ids.append(rule_id)
                for rule in changed_rules[filter_type]["updated"]:
                    rule_id = rule.split(" - ")[0]
                    rule_ids.append(rule_id)
            print(len(rule_ids), rule_ids)
        except Exception as e:
            print("Error! {}. Failed to dump parsing data into text file".format(e))

        package_info = collect_package_info(package_root, hash)

        with open(os.path.join(package_folder, package_name + ".json"), "w") as f:
            json.dump(package_info, f, indent=2)

        


# Collects any new/updated rules in the package
def find_new_and_updated(xml_root, date, is_sample):
    changed = {}

    # IP, LI and IM all use the same format
    filter_types = ["PayloadFilter2s", "IntegrityRules", "LogInspectionRules"]
    for filter_type in filter_types:
        changed[filter_type] = {"new": [], "updated": []}
        for filter_info in xml_root.find(filter_type):
            # For sample, updated rules have Issued tag as isNull="true" and FirstIssued as an epoch. New rules have both as isNull="true"
            if is_sample:
                if "isNull" in filter_info.find("Issued").attrib and filter_info.find("Issued").attrib["isNull"] == "true":
                    data = f"{filter_info.find('Identifier').text} - {filter_info.find('Name').text} (V{filter_info.find('Version').text})"
                    if "isNull" in filter_info.find("FirstIssued").attrib and filter_info.find("FirstIssued").attrib["isNull"] == "true":
                        changed[filter_type]["new"].append(data)
                    else:
                        changed[filter_type]["updated"].append(data)
            # For issued, we search for any Issued epochs that match the package epochs. Then, if Issued matches FirstIssued the rule
            else:
                if filter_info.find("Issued").text == date:
                    data = f"{filter_info.find('Identifier').text} - {filter_info.find('Name').text} (V{filter_info.find('Version').text})"
                    if filter_info.find("FirstIssued").text == date:
                        changed[filter_type]["new"].append(data)
                    else:
                        changed[filter_type]["updated"].append(data)

    # LogInspectionDecoders are slightly different, since they lack FirstIssued.
    # Instead, we look only to see if Issued has been changed (in which case it has been updated)
    # Also, there is only ever one decoder
    changed["LogInspectionDecoders"] = {"new": [], "updated": []}
    for filter_info in xml_root.find("LogInspectionDecoders"):
        if filter_info.find("Issued").text == date:
            data = f"{filter_info.find('Identifier').text} - {filter_info.find('Name').text} (V{filter_info.find('Version').text})"
            changed["LogInspectionDecoders"]["updated"] = [data]

    return changed


# We do know the structure of the XML file ahead of time, but to write specific parsing code would be quite lengthy
# Hence, we just recursively crawl the XML tree to collect the data
# Any tags that are part of "hash" are not directly added to the output; instead, their SHA-256 hash is added instead
def collect_package_info(xml_root, hash):
    package_info = {}
    for section in xml_root:
        if section.tag in hash:
            hashed = ""
            if section.text:
                hashed = hashlib.sha256(section.text.encode("utf-8")).hexdigest()
            package_info[f"{section.tag}-hash"] = hashed
        else:
            section_info = collect_package_info(section, hash)
            for attrib in section.attrib:  # Some of the XML tags also have attributes attached to them
                if not section_info:  # Some tags have nothing but attributes, and so return null above
                    section_info = {}
                section_info[attrib] = section.attrib[attrib]
            if section.tag not in package_info:
                package_info[section.tag] = section_info
            else:
                # We don't know ahead of time whether or not a given section is a single element or is a list
                # We assume it is single to begin with, and if we see it twice we convert to a list
                if not isinstance(package_info[section.tag], list):
                    package_info[section.tag] = [package_info[section.tag]]
                package_info[section.tag].append(section_info)
    if not package_info:  # We have reached the bottom of the XML tree
        return xml_root.text
    return package_info

if __name__ == '__main__':
    main()