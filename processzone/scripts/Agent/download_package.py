# Downloads the DSRU update from the given link
# If the update is zipped, automatically extracts the .dsru file itself

import os
import zipfile
import argparse
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--package_url", action="store", help="URL of package to download")
    parser.add_argument("-c", "--nexus_cred", nargs="+", help="Nexus Credentials")
    args = parser.parse_args()
    nexus_username, nexus_password = args.nexus_cred

    with requests.Session() as session:
        session.auth = (nexus_username, nexus_password)
        # Most general way of looking for package name is to try and grab it from the URL itself
        package_name = args.package_url.rsplit("/")[-1]

        response = session.get(args.package_url)

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


if __name__ == '__main__':
    main()
