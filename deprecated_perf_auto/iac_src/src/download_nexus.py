import requests
import argparse
import os
import shutil
import zipfile


def get_pkg(url, path, uname, pwd):
    print("# {} Downloading.... #".format(url))
    name, ext = os.path.splitext(url.rsplit("/", 1)[-1])
    pkg = requests.get(url, auth=(uname, pwd))
    if os.path.exists(path):
        print("Removing old folder {} ".format(path))
        shutil.rmtree(path)
    print("Creating folder {} ".format(path))
    os.makedirs(path)
    if ext == ".zip":
        package_name = url.rsplit("/")[-1]
        package_path = os.path.join(path, package_name)
        with open(package_path, "wb") as fin:
            fin.write(pkg.content)

        # Program also handles .zip files, though sample updates should usually be .3bsu and not .zip
        if os.path.splitext(package_name)[-1] == ".zip":
            with zipfile.ZipFile(package_path, 'r') as fz:
                fz.extractall(path)
            os.remove(package_path)
    else:
        fname = "{}.dsru".format(os.path.join(path, name.split(".")[0]))
        if fname.split("/")[-1] == "sample.dsru":
            fname_split = fname.split(".")
            fname = "{}_{}.{}".format(fname_split[0], name.split(".")[2], fname_split[1])
        print("File name: {}".format(fname))
        with open(fname, "wb") as fin:
            fin.write(pkg.content)

    dsru_file = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.dsru')]
    print("Downloaded Files: {} ".format(dsru_file))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--url', type=str, help="Nexus Package URL")
    parser.add_argument('--path', type=str, help="Nexus Package URL")
    parser.add_argument('--uname', type=str, help="Nexus Package URL")
    parser.add_argument('--pwd', type=str, help="Nexus Package URL")
    args = parser.parse_args()

    get_pkg(args.url, args.path, args.uname, args.pwd)
