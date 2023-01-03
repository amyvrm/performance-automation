# Uploads the update packages to Nexus

import argparse
import requests
import os
import sys
import re
from datetime import datetime

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--jfrog_token", action="store", help="JFrog Credentials")
    args = parser.parse_args()

    jfrog_token = args.jfrog_token
    full_jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"

    now = datetime.now()
    timestamp = datetime.timestamp(now)
    print("timestamp =", timestamp)
    timestamp = datetime.fromtimestamp(timestamp)
    folder_name = timestamp.strftime('%Y-%m-%d_%H-%M')
    # print(type(folder_name))
    # today = today.strftime("%m/%d/%y")

    with requests.Session() as s:
        s.auth = BearerAuth(jfrog_token)
        upload_update(s, f"{full_nexus_url}/PCAPRegression/{folder_name}", 'pcap_regression_report.html')
        print('Report uploaded Successfully')

        # if not check_upload(s, f"{version}00", "PCAPRegression", args.nexus_url, args.nexus_repository):
        # print("Nexus upload failed, update packages not found. Please check the status of the Nexus repository")
        # sys.exit(-1)


def upload_update(session, upload_url, filename, file_location="/tmp"):
    with open(os.path.join(file_location, filename), "rb") as f:
        data = f.read()
        session.put(f"{upload_url}/{filename}", verify=False, data=data)

"""
def check_upload(session, version, update_type, nexus_url, nexus_repository):
    test_url = f"{nexus_url.replace('repository', 'service/rest/repository/browse/')}/{nexus_repository}/{update_type}/{version}"
    r = session.get(test_url)
    if r.status_code == 404:
        return False
    return True
"""

if __name__ == '__main__':
    main()
