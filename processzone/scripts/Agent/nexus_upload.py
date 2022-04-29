# Uploads the update packages to Nexus

import argparse
import requests
import os
import sys
import re
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--nexus_cred", nargs="+", help="Nexus Credentials")
    args = parser.parse_args()

    nexus_username, nexus_password = args.nexus_cred
    full_nexus_url = "https://dsnexus.trendmicro.com:443/nexus/repository/dslabs-regression"

    now = datetime.now()
    timestamp = datetime.timestamp(now)
    print("timestamp =", timestamp)
    timestamp = datetime.fromtimestamp(timestamp)
    folder_name = timestamp.strftime('%Y-%m-%d_%H-%M')
    # print(type(folder_name))
    # today = today.strftime("%m/%d/%y")

    with requests.Session() as s:
        s.auth = (nexus_username, nexus_password)
        upload_update(s, f"{full_nexus_url}/PCAPRegression/{folder_name}", 'pcap_regression_report.html')
        print('Report uploaded Successfully')

        # if not check_upload(s, f"{version}00", "PCAPRegression", args.nexus_url, args.nexus_repository):
        # print("Nexus upload failed, update packages not found. Please check the status of the Nexus repository")
        # sys.exit(-1)


def upload_update(session, upload_url, filename, file_location="/tmp"):
    with open(os.path.join(file_location, filename), "rb") as f:
        data = f.read()
        session.put(f"{upload_url}/{filename}", verify=False, data=data)


def check_upload(session, version, update_type, nexus_url, nexus_repository):
    test_url = f"{nexus_url.replace('repository', 'service/rest/repository/browse/')}/{nexus_repository}/{update_type}/{version}"
    r = session.get(test_url)
    if r.status_code == 404:
        return False
    return True


if __name__ == '__main__':
    main()
