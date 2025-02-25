#!/usr/bin/python
import argparse
import subprocess
import os
import shutil
import re

class InfraAutomation:

    def __init__(self, access_key, secret_key, resource_list, terraform_dir):
        self.access_key = access_key
        self.secret_key = secret_key
        self.resource_list = resource_list
        self.terraform_dir = terraform_dir
        self.currentresource = None
    
    def performDestruction(self):
        resource_list = self.resource_list.split(',')
        resource_list = [x.strip(' ') for x in resource_list]
        sorted_resource_list = sorted(resource_list, key = lambda x: x.split('-')[0])
        
        for resource in sorted_resource_list:
            #self.refreshTerraform()
            self.currentresource = resource
            self.importTerraform(resource)
            self.destroyTerraform()
            
        print('Destruction complete successfully')
            
            
    def importTerraform(self, resource):
        print('\n=================================')
        print('Importing resource...')
        
        if resource.startswith('i-'):
            cmd_ret = subprocess.call([
                'terraform', '-chdir=' + self.terraform_dir,
                'import',
                '-var',
                'access_key='+self.access_key,
                '-var',
                'secret_key='+self.secret_key,
                'aws_instance.dsm_dsa_machine',
                resource])
            
        if cmd_ret != 0:
            raise ChildProcessError('{} - Failed to import resource'.format(cmd_ret))
        else:
            print('Resource imported successfully.')
            
    def initializeTerraform(self):
        
        print('\n=================================')
        print('Initializing terraform template...')
        
        cmd_ret = subprocess.call([
            'terraform', '-chdir=' + self.terraform_dir,
            'init'])
            
        if cmd_ret != 0:
            raise ChildProcessError('Failed to initialize templates')
        else:
            print('Directory initialized successfully.')
            
    def refreshTerraform(self):
        
        print('\n=================================')
        print('Refreshing terraform template...')
        
        cmd_ret = subprocess.call([
            'terraform', '-chdir=' + self.terraform_dir,
            '-var',
            'access_key='+self.access_key,
            '-var',
            'secret_key='+self.secret_key,
            'refresh'])
            
        if cmd_ret != 0:
            raise ChildProcessError('Failed to refresh templates')
        else:
            print('Directory refreshed successfully.')
            
    def destroyTerraform(self):
        
        print('\n=================================')
        print('Destroying terraform template...')
        
        cmd_ret = subprocess.call([
            'terraform', '-chdir=' + self.terraform_dir,
            'destroy',
            '-var',
            'access_key='+self.access_key,
            '-var',
            'secret_key='+self.secret_key,
            '--auto-approve'])
            
        if cmd_ret != 0 and self.currentresource.startswith('sg-'):
            print('Resouces destroyed successfully.')
        elif cmd_ret != 0:
            raise ChildProcessError('Failed to destroy templates')
        else:
            print('Resouces destroyed successfully.')
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--access_key', type=str, help="AWS Access Key")
    parser.add_argument('--secret_key', type=str, help="AWS Secret Key")
    parser.add_argument('--resource_list', type=str, help="Resouce list for destruction")
    parser.add_argument('--terraform_dir', type=str, help="Terraform directory")
    args = parser.parse_args()
    
    
    infraAutomate = InfraAutomation(args.access_key, args.secret_key, args.resource_list, args.terraform_dir)
    infraAutomate.initializeTerraform()
    infraAutomate.performDestruction()
