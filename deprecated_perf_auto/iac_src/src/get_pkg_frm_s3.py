#!/usr/bin/env python3
import argparse
import boto3
import os
import shutil

class GetPkgFromS3Bucket(object):
    def __init__(self, access_key, secret_key, bucket, target_path):
        self.s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.bucket = bucket
        print("Bucker name: {}, Download path: {}".format(bucket, target_path))
        # create path
        self.path = os.path.join(os.getcwd(), target_path)
        print("Download path absolute: {}".format(self.path))
        if os.path.exists(self.path):
            print("Removing old folder {} ".format(self.path))
            shutil.rmtree(self.path)
        os.mkdir(self.path)

    def list_all_bucket(self):
        response = self.s3.list_buckets()
        # Output the bucket names
        print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')

    def get_package(self, pkg_name):
        # check package exist
        if True not in [True for pkg in self.s3.list_objects_v2(Bucket=self.bucket)['Contents'] if pkg['Key'] == pkg_name]:
            raise Exception("{} Not found in Bucket:{}".format(pkg_name, self.bucket))

        # download package
        self.s3.download_file(self.bucket, pkg_name, os.path.join(self.path, pkg_name))
        # check package
        print("List the packages: {}".format(os.listdir(self.path)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument for S3 operations')
    parser.add_argument('--access_key', type=str, help="Please give AWS Access Key")
    parser.add_argument('--secret_key', type=str, help="Please give AWS Secret Key")
    parser.add_argument('--bucket', type=str, help="Please give S3 bucket name")
    parser.add_argument('--path', type=str, help="Please give Download path")
    args = parser.parse_args()

    pkg_list = ["PCATTCP.zip", "ab.exe", "hey.exe", "nginx-1.19.2ready.zip"]

    get_pkg = GetPkgFromS3Bucket(args.access_key, args.secret_key, args.bucket, args.path)
    get_pkg.list_all_bucket()
    for pkg in pkg_list:
        get_pkg.get_package(pkg)