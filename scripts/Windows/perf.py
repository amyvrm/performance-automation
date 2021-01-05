#!/usr/bin/python
import pypsexec
import time
from pypsexec.client import Client
import argparse
import subprocess

def Through_put():
    client = Client("192.168.201.203", username="Administrator", password="perfip", encrypt=False)
    client.connect()
    try:
        client.create_service()
        i = 0
        while i < 10:
            stderr, stdout, rc = client.run_executable('C:\\PCATTCP-0111\\DSRU_16-032\\PCATTCP.exe', arguments='-t -l 490000 192.168.1.3')
            i += 1
            Through_put = stdout.split("=")[1].split(" ")[-8]
            print(Through_put)
    except:
        pass
    finally:
        client.remove_service()
        client.disconnect()

def open_server():
    server = Client("192.168.201.209", username="Administrator", password="hqlocal1", encrypt=False)
    server.connect()
    try:
        server.create_service()
        stderr, stdout, rc = server.run_executable('C:\\PCATTCP-0111\\PCATTCP.exe', arguments='-r 192.168.1.4 -l 490000 -c', asynchronous=True)
        #print stderr
        return rc
    except:
        pass
    finally:
        server.remove_service()
        server.disconnect()

def close_server(pid):
    server = Client("192.168.201.209", username="Administrator", password="hqlocal1", encrypt=False)
    server.connect()
    arg = '/F /PID ' + str(pid)
    try:
        server.create_service()
        stderr, stdout, rc = server.run_executable('taskkill.exe', arguments=arg)
        print(stdout)
    except:
        pass
    finally:
        server.remove_service()
        server.disconnect()

def Sanitize():
    server = Client("192.168.201.209", username="Administrator", password="hqlocal1", encrypt=False)
    server.connect()
    arg = '/IM PCATTCP.exe /F'
    try:
        server.create_service()
        stderr, stdout, rc = server.run_executable('taskkill.exe', arguments=arg)
        print(stderr)

    except:
        print("Error sanitize")
    finally:
        server.remove_service()
        server.disconnect()

def serverUpload():
    Sanitize()
    print("Opening server..")
    time.sleep(4)
    Process_id = open_server()
    print("Analysing Network Throughput")
    time.sleep(2)
    Through_put()
    print("Closing the Server..")
    time.sleep(2)
    close_server(Process_id)


if __name__ == '__main__':
    serverUpload()
    parser = argparse.ArgumentParser(description='Please give argument for performance scenario')
    parser.add_argument('--access_key', type=str, help="Please give AWS Access Key")
    parser.add_argument('--secret_key', type=str, help="Please give AWS Secret Key")
    args = parser.parse_args()