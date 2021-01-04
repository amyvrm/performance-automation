#!/usr/bin/python
import argparse
import subprocess
import os
import shutil

class InfraAutomation:

    def __init__(self, access_key, secret_key, agent_urls, dsm_url, dsm_license):
        self.access_key = access_key
        self.secret_key = secret_key
        self.agent_urls = agent_urls
        self.dsm_url = dsm_url
        self.dsm_license = dsm_license
        
    def form_agent_urls(self):
        self.agent_urls = self.agent_urls.replace("|", "~~")
        
    def plan_processzone(self):
        print('\n=================================')
        print('Planning Staging template...')
        
        cmd_ret = subprocess.call([
            'terraform',
            'plan',
            '-input=false',
            '-out=staging_plan.out',
            '-var',
            'access_key='+self.access_key,
            '-var',
            'secret_key='+self.secret_key,
            '-var',
            'all_agent_urls='+self.agent_urls,
            '-var',
            'dsm_redhat_url='+self.dsm_url,
            '-var',
            'dsm_license='+self.dsm_license,
            'processzone'])
            
        if cmd_ret != 0:
            raise ChildProcessError('Failed to plan templates')
        else:
            print('Directory Planned successfully.')
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--access_key', type=str, help="AWS Access Key")
    parser.add_argument('--secret_key', type=str, help="AWS Secret Key")
    parser.add_argument('--agent_urls', type=str, help="DSA download URLs")
    parser.add_argument('--dsm_url', type=str, help="DSM download URL")
    parser.add_argument('--dsm_license', type=str, help="DSM License Key")
    args = parser.parse_args()
    
    
    infraAutomate = InfraAutomation(args.access_key, args.secret_key, args.agent_urls, args.dsm_url, args.dsm_license)
    infraAutomate.form_agent_urls()
    infraAutomate.plan_processzone()
