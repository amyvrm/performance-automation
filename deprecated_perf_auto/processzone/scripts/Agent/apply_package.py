# Applies the DSRU update package to the DSM

import os
import sys
import re
import argparse
import urllib3
import zeep
import json
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", action="store", help="IP address of DSM")
    parser.add_argument("-c", "--credentials", nargs="+", help="User Credentials")
    args = parser.parse_args()

    dsm_ip = args.ip
    username, password = args.credentials

    urllib3.disable_warnings()
    wsdl = f"https://{dsm_ip}:4119/webservice/Manager?WSDL"
    transport = zeep.Transport()
    transport.session.verify = False  # Bypass self-signed certificate errors

    client = zeep.Client(wsdl=wsdl, transport=transport)
    try:
        session_id = client.service.authenticate(username=username, password=password)

        response = upload_package(client, session_id)
        update_id = response["ID"]
        print(f"Upload successful, update package ID is {update_id}")

        print(f"Saving dsru content information to update-info\n")
        if not os.path.exists("update-info"):
            os.makedirs("update-info")
        with open(os.path.join("update-info", "dsm-added_rules.txt"), "w") as f:
            f.write(response["contentSummary"])

        print("Here are the rules that were added/updated on the DSM:")
        print(response["contentSummary"])

        print("Sanitising result")

        bad_words = ['Decoders', 'decoder', 'decoders', 'Decoder', 'Log Decoders']
        regex = f"^.*(:{'|'.join(bad_words)}).*\n"
        print(regex)
        subst = ""

        sanitised_result = re.sub(regex, subst, response["contentSummary"], flags=re.MULTILINE)
        print(sanitised_result)

        # identifiers = [x[0] for x in re.findall("^\s*(\d+) - (.*)$", response["contentSummary"], re.MULTILINE)]
        identifiers = [x[0] for x in re.findall("^\s*(\d+) - (.*)$", sanitised_result, re.MULTILINE)]
        print(f"Rule identifiers are {identifiers}\n")
        with open(os.path.join("update-info", "rule-identifiers.txt"), "w") as f:
            f.write(",".join(identifiers))

        # Response has the format:
        #   DPIRulesAdded, DPIRulesAddedAndAssigned, DPIRulesDeleted, DPIRulesUpdated,
        #   applicationTypesAdded, applicationTypesDeleted, applicationTypesUpdated,
        #   detailedSummary,
        #   integrityMonitoringRulesAdded, integrityMonitoringRulesDeleted, integrityMonitoringRulesUpdated
        #   logInspectionDecodersAdded, logInspectionDecodersDeleted, logInspectionDecodersUpdated,
        #   logInspectionRulesAdded, logInspectionRulesDeleted, logInspectionRulesUpdated,
        #   portListsAdded, portListsUpdated
        print("Attempting to apply update package", flush=True)
        response = client.service.securityUpdateApply(ID=update_id, detectOnly=False, sID=session_id)
        with open(os.path.join("update-info", f"dsm-assigned_rules.txt"), "w") as f:
            f.write(response["detailedSummary"])
        print("Update package applied successfully")
        print(f"Details saved to update-info.txt\n")

        time.sleep(15)

        save_internal_ids_to_json(client, session_id)

        client.service.endSession(sID=session_id)
        client.transport.session.close()
        print("No problems uploading or applying update package, all tests passed")

    except zeep.exceptions.Fault as e:
        print(e)
        client.service.endSession(sID=session_id)
        client.transport.session.close()
        print("\nError during upload script, exiting")
        sys.exit(-1)


def upload_package(zeep_client, session_id):
    package_name = [filename for filename in os.listdir("/tmp/update-packages")
                    if os.path.splitext(filename)[-1] == ".3bsu" or os.path.splitext(filename)[-1] == ".encrypted" or
                    os.path.splitext(filename)[-1] == ".dsru"][0]
    package_path = os.path.join("/tmp", "update-packages", package_name)
    with open(package_path, "rb") as f:
        update_package = f.read()
    print(f"Uploading {package_name} to DSM", flush=True)
    response = zeep_client.service.securityUpdateStore(securityUpdate=update_package, fileName=package_name,
                                                       sID=session_id)
    return response


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
