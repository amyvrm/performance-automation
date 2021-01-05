#!/usr/bin/python
import argparse
import subprocess
import os
import shutil

class InfraAutomation:

    def __init__(self, agents):
        self.agents = agents
        
    def move_to_processzone(self, agent_name):
        #RHEL,Amazon Linux 1,Amazon Linux 2,Windows Server 2019,Ubuntu,Solaris
        if (agent_name == 'Windows Server 2019'):
            shutil.move("aws_agent_windows_book.tf", "processzone/aws_agent_windows_book.tf")
        if (agent_name == 'Windows Server 2019 A2'):
            shutil.move("aws_agent_windows_book2.tf", "processzone/aws_agent_windows_book2.tf")
        else:
            print('Invalid Agent Choice.')
        
    def move_files_to_holdzone(self):
        agentlist = self.agents.split(',')
        for agent in agentlist:
            self.move_to_processzone(agent)
        
        
if __name__ == '__main__':
    #python intializeProcesszone.py --agents "RHEL,Amazon Linux 1,Amazon Linux 2,Windows Server 2019"
    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('--agents', type=str, help="Selected agents to spin-up")
    args = parser.parse_args()

    infraAutomate = InfraAutomation(args.agents)
    infraAutomate.move_files_to_holdzone()