#!/usr/bin/python
import argparse
import subprocess
import os
import shutil

class InfraAutomation:

    def __init__(self, access_key, secret_key, agents, agent_urls):
        self.access_key = access_key
        self.secret_key = secret_key
        self.agents = agents
        self.agent_urls = agent_urls
        
    def form_agent_urls(self):
        self.agent_urls = self.agent_urls.replace("|", "~~")
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--access_key', type=str, help="AWS Access Key")
    parser.add_argument('--secret_key', type=str, help="AWS Secret Key")
    parser.add_argument('--agents', type=str, help="Selected agents to spin-up")
    parser.add_argument('--agent_urls', type=str, help="DSA download URLs")
    args = parser.parse_args()
    
    
    infraAutomate = InfraAutomation(args.access_key, args.secret_key, args.agent_urls)
    infraAutomate.form_agent_urls()
