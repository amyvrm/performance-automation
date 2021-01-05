#!/usr/bin/python
import argparse
import subprocess
import os
import shutil

class InfraAutomation:

    def __init__(self):
        print('Already initialized')

    def apply_processzone(self):
        print('\n=================================')
        print('Applying staging template...')
        
        cmd_ret = subprocess.call([
            'terraform',
            'apply',
            '-input=false',
            '-auto-approve',
            'staging_plan.out'])
            
        if cmd_ret != 0:
            raise ChildProcessError('Failed to apply templates')
        else:
            print('Infrastructure created successfully.')
  
if __name__ == '__main__':
    infraAutomate = InfraAutomation()
    infraAutomate.apply_processzone()
