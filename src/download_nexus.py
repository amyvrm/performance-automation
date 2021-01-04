import requests
import argparse
import os
import shutil


def get_pkg(url, path, uname, pwd):
    name, ext = os.path.splitext(url.rsplit("/", 1)[-1])
    pkg = requests.get(url, auth=(uname, pwd))
    if os.path.exists(path):
        shutil.rmtree()
    os.makedirs(path)
    fname = "{}.dsru".format(os.path.join(path, name.split(".")[0]))
    print("File name: {}".format(fname))
    with open(fname, "wb") as fin:
        fin.write(pkg.content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--url', type=str, help="Nexus Package URL")
    parser.add_argument('--path', type=str, help="Nexus Package URL")
    parser.add_argument('--uname', type=str, help="Nexus Package URL")
    parser.add_argument('--pwd', type=str, help="Nexus Package URL")
    args = parser.parse_args()

    get_pkg(args.url, args.path, args.uname, args.pwd)
