import rsa
import boto.ec2
import base64
from pypsexec.client import Client
import simplejson as json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import time
import os
import re


class PerfCommon(object):
    def __init__(self, stats, graph):
        self.header = "-" * 50
        self.stats = stats
        self.graph = graph
        self.rule_file = os.path.join("update-info", "rule-identifiers.txt")
        self.server_rule_file = os.path.join("update-info", "server-rule-identifiers.txt")
        self.client_rule_file = os.path.join("update-info", "client-rule-identifiers.txt")
        self.portlist_file = os.path.join("update-info", "port_list.txt")

    def create_html_table(self, df, scenario_name):
        print(df)
        fname = "{}_{}".format(scenario_name.replace(" ", "_"), self.stats)
        if os.path.exists(fname):
            os.remove(fname)
        # create table
        with open(fname, "a") as fin:
            fin.write(self.create_html_header())
            fin.write("<div class=\"container\"><div class=\"row\">")
            fin.write(df.to_html(classes='table table-striped', justify='center'))
            fin.write("</div></div>")
            fin.write("</body>\n</html>\n")

    def create_bar_chart(self, avg, scenario_name):
        # if scenario_name == "Server Upload" or scenario_name == "Server Download":
        #     self.col.append('Server Rule (No. of Rules: {})'.format(len(self.server_rule)))
        # elif scenario_name == "Client Download":
        #     self.col.append('Client Rule (No. of Rules: {})'.format(len(self.client_rules)))

        ind = np.arange(0, len(avg))
        scenario_sort = ["WOFD", "WFD", "OGR", "SR_U"]

        df = pd.DataFrame()
        df["ind"] = ind
        df["avg"] = avg
        df["sce_sort"] = scenario_sort

        # specify the colors
        colors = sns.color_palette('pastel', n_colors=len(df))
        plt.figure(figsize=(16, 10))
        sns.set_style('ticks')
        ax = sns.barplot(data=df, x="sce_sort", y="avg", palette=colors)
        for index, row in df.iterrows():
            ax.text(row.ind, row.avg, row.avg, color='black', ha="center", fontsize=16)

        ax.set_xlabel("Scenario", fontsize=16, alpha=0.8)
        ax.set_ylabel("Throughput (MBps)", fontsize=16, alpha=0.8)
        ax.set_title(scenario_name, fontsize=18)
        ax.set_xticklabels(scenario_sort, fontsize=14)

        # map names to colors
        cmap = dict(zip(self.col, colors))
        from matplotlib.patches import Patch
        # create the rectangles for the legend
        patches = [Patch(color=v, label=k) for k, v in cmap.items()]
        # add the legend
        lgd = plt.legend(title='Scenario Stats', handles=patches, bbox_to_anchor=(0.5, -0.1))
        text = ax.text(-0.2, 1.05, "Scenario: {}".format(scenario_name), transform=ax.transAxes)
        ax.grid('on')
        sns.despine()
        # plt.show()
        fname = "{}_{}".format(scenario_name.replace(" ", "_"), self.graph)
        if os.path.exists(fname):
            os.remove(fname)
        plt.savefig(fname, bbox_extra_artists=(lgd, text), bbox_inches='tight')

    def create_html_header(self):
        html_header = "<html><head>\n" \
                      "<link rel=\"stylesheet\" href=\"https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css\" integrity=\"sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh\" crossorigin=\"anonymous\">\n" \
                      "<script src=\"https://code.jquery.com/jquery-3.4.1.slim.min.js\" integrity=\"sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n\" crossorigin=\"anonymous\"></script>\n" \
                      "<script src=\"https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js\" integrity=\"sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo\" crossorigin=\"anonymous\"></script>\n" \
                      "<script src=\"https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js\" integrity=\"sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6\" crossorigin=\"anonymous\"></script>\n" \
                      "</head>\n<body>\n"
        return html_header

    def run_band_test(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name):
        if scenario_name == "Server Download":
            # Run Nginx
            self.run_nginx(cip, cuser, cpwd)
            # Run Apache Bench
            through_put = self.run_ab(sip, suser, spwd, c_priv_ip)
            print("Through put: {}".format(through_put))
        elif scenario_name == "Client Download":
            # Run Nginx
            self.run_nginx(sip, suser, spwd)
            # Run Apache Bench
            through_put = self.run_ab(cip, cuser, cpwd, s_priv_ip)
            print("Through put: {}".format(through_put))
        elif scenario_name == "Server Upload":
            self.clean(cip, cuser, cpwd)
            self.clean(sip, suser, spwd)
            time.sleep(4)
            # receiver
            pid = self.run_pcattcp_rec(cip, cuser, cpwd, s_priv_ip, asynchronous=True)
            time.sleep(2)
            # transmitter
            through_put = self.run_pcattcp_tran(sip, suser, spwd, c_priv_ip, bandwidth=True)
            print("Through put: {}".format(through_put))
            # print("sum: {}, len: {}, Average: {} MBps".format(sum(map(float, through_put)), len(through_put),
            #                                                   round(sum(map(float, through_put)) / len(through_put), 2)))
            time.sleep(2)
            self.clean(cip, cuser, cpwd, pid=pid)
            self.clean(sip, suser, spwd)
        return through_put

    def execute_cmd(self, cmd, ip, user, pwd, tool="Powershell.exe", iteration=10, bandwidth=False, asynchronous=False):
        machine = Client(ip, username=user, password=pwd, encrypt=False)
        machine.connect()
        try:
            machine.create_service()
            print("# IP: {}, Tool: {}, Command: {} #".format(ip, tool, cmd))
            if tool == "Powershell.exe":
                if bandwidth:
                    print("- Taking Bandwidth Reading...")
                    all_through_put = []
                    for i in range(iteration):
                        stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                        print("Tool: {}, Output: [{}], Error: {}".format(tool, stdout, stderr))
                        PerfCommon.get_bandwidth(cmd, stdout, stderr, all_through_put, i)
                        time.sleep(1)
                    all_through_put.sort(reverse=True)
                    return all_through_put
                else:
                    print("- Running Remote Command...")
                    stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                    print("Tool: {}, Output: [{}], Error: {}".format(tool, stdout, stderr))
                if stdout:
                    return stdout.decode("utf-8").split("\r")[0]
            else:
                stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                print("{} Output: [{}], pid: {}, Error: {}".format(tool, stdout, rc, stderr))
                return rc
        except Exception as e:
            print("Error!!! {} while accessing {}".format(e, ip))
        finally:
            machine.remove_service()
            machine.disconnect()

    @staticmethod
    def get_bandwidth(cmd, stdout, stderr, all_through_put, index):
        if "PCATTCP" in cmd:
            if stderr:
                out = stderr.decode("utf-8")
                through_put = out.split("=")[1].split(" ")[-8]
                t_mbps = round(float(through_put) / 1024.0, 2)
                print("{}: {} KBps, {} MBps".format(index + 1, through_put, t_mbps))
                all_through_put.append(t_mbps)
        elif "ab" in cmd:
            if stdout:
                out = stdout.decode("utf-8")
                for line in out.split("\r\n"):
                    if "Transfer rate" in line:
                        through_put = re.findall("\d+\.\d+", line)[0]
                        t_mbps = round(float(through_put) / 1024.0, 2)
                        print("{}: {} KBps, {} MBps".format(index + 1, through_put, t_mbps))
                        all_through_put.append(t_mbps)

    @staticmethod
    def get_pwd(region, access_key, secret_key, instance_id, pem_file_loc, mtype):
        print("# get_pwd #")
        ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        # Get all instance
        reservations = ec2_conn.get_all_reservations()
        # Get all the instances and search for the instance based on the provided Tag - Name
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instance_id:
                    print("Found instance id: {}".format(instance_id))
                    priv_ip = instance.private_ip_address
                    print("Private IP: {}".format(priv_ip))
                    # Get the encrypted password and decrypt
                    try:
                        print("Public IP: {}".format(instance.ip_address))
                    except Exception as e:
                        print("Failed to get public ip: {}".format(e))
                    pwd = base64.b64decode(ec2_conn.get_password_data(instance.id).strip())
                    if pwd:
                        with open(pem_file_loc, 'r') as priv_key:
                            priv = rsa.PrivateKey.load_pkcs1(priv_key.read())
                        key = rsa.decrypt(pwd, priv)
                    else:
                        key = 'Wait at least 4 minutes after creation before the admin password is available'
                    print("* {}-{} Machine Password: {}".format(mtype, instance.ip_address, key.decode("utf-8")))
                    return key.decode("utf-8")

    def get_adaptor_name(self, ip, user, pwd):
        print("# get_adaptor_name #")
        tool = "Powershell.exe"
        cmd = "Get-NetAdapter -Name *|select Name|%{$_.Name}"
        name = self.execute_cmd(cmd, ip, user, pwd, tool=tool)
        return name.replace(" ", "` ") if " " in name else name

    def enable_filter(self, ip, user, pwd, adaptor_name):
        print("{0}\n # {2}-{1} Enable Filter #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        for retry in range(2):
            tool = "Powershell.exe"
            cmd = 'Enable-NetAdapterBinding -Name "{}" -DisplayName "Trend` Micro` LightWeight` Filter` Driver"'.format(
                adaptor_name)
            self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def disable_filter(self, ip, user, pwd, adaptor_name):
        print("{0}\n # {2}-{1} Disable Filter #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        for retry in range(2):
            tool = "Powershell.exe"
            cmd = 'Disable-NetAdapterBinding -Name "{}" -DisplayName "Trend` Micro` LightWeight` Filter` Driver"'.format(
                adaptor_name)
            self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def clean(self, ip, user, pwd, pid=False):
        print("# clean pid: {} #".format(pid))
        tool = 'taskkill.exe'
        if not pid:
            cmd = '/IM PCATTCP.exe /F'
        else:
            cmd = '/F /PID {}'.format(pid)
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def clean_ab(self, ip, user, pwd):
        print("# Clean Apache Bench in {}-{} #".format(self.ip_type[ip], ip))
        tool = 'taskkill.exe'
        cmd = '/IM ab.exe /F'
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def clean_nginx(self, ip, user, pwd):
        print("# Clean Nginx in {}-{} #".format(self.ip_type[ip], ip))
        tool = 'taskkill.exe'
        cmd = '/IM nginx.exe /F'
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def run_pcattcp_rec(self, ip, user, pwd, target_ip, asynchronous=False):
        print("# Run PCATTCP on {}-{} #".format(self.ip_type[ip], ip))
        tool = "Powershell.exe"
        cmd = '{}PCATTCP\PCATTCP.exe -r -l 490000 {} -c'.format(self.path, target_ip)
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=False, asynchronous=asynchronous)

    def run_pcattcp_tran(self, ip, user, pwd, target_ip, bandwidth=False, asynchronous=False):
        print("# Run PCATTCP on {}-{} and take Reading #".format(self.ip_type[ip], ip))
        print("# run_pcattcp_tran #")
        tool = "Powershell.exe"
        cmd = '{}PCATTCP\PCATTCP.exe -t -l 490000 {}'.format(self.path, target_ip)
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=bandwidth, asynchronous=asynchronous)

    def run_nginx(self, ip, user, pwd):
        print("# Run nginx on {}-{} #".format(self.ip_type[ip], ip))
        self.clean_nginx(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = "cd {0}nginx-1.19.2; start {0}nginx-1.19.2\\nginx.exe".format(self.path)
        self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=False, asynchronous=True)

    def run_ab(self, ip, user, pwd, target_ip):
        print("# Run Apache Bench {}-{} #".format(self.ip_type[ip], ip))
        self.clean_ab(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = "{}ab.exe -k -n 100 -c 10 http://{}/test.htm".format(self.path, target_ip)
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=True, asynchronous=False)

    def disable_dsa(self, ip, user, pwd):
        print("{0}\n # {2}-{1} Disable DSA #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        for retry in range(2):
            tool = "Powershell.exe"
            cmd = "Stop-Service -Name \"Trend` Micro` Deep` Security` Agent\""
            self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def activate_dsa(self, ip, user, pwd):
        print("{0}\n # {2}-{1} Activate DSA #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        for retry in range(2):
            tool = "Powershell.exe"
            cmd = "Start-Service -Name \"Trend` Micro` Deep` Security` Agent\""
            self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def reboot_instance(self, instance_id, access_key, secret_key, region):
        print("{0}\n # Reboot {1} Instance #\n{0}".format(self.header, instance_id))
        ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        # Get all instance
        reservations = ec2_conn.get_all_reservations()
        # Get all the instances and search for the instance based on the provided Tag - Name
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instance_id:
                    print("Found instance id: {}".format(instance_id))
                    ec2_conn.stop_instances(instance_ids=[instance_id, ])
                    print("{} instance has been stoped and waiting for 2 min".format(instance_id))
                    time.sleep(120)
                    ec2_conn.start_instances(instance_ids=[instance_id, ])
                    print("{} instance has been started and waiting for 2 min".format(instance_id))
                    time.sleep(120)

        ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        # Get all instance
        reservations = ec2_conn.get_all_reservations()
        # Get all the instances and search for the instance based on the provided Tag - Name
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instance_id:
                    print("Found instance id: {}".format(instance_id))
                    return instance.ip_address, instance.private_ip_address
        raise Exception("{} Instance is not running...".format(instance_id))

    def get_dependency_portlist(self, path, grule):
        server_rules = []
        client_rules = []
        non_dpi_rules = []
        all_dep_rules = set()
        client_dep_rules = set()
        portlist_set = set()
        grule_list = [grule]

        with open(self.rule_file, "r") as f:
            all_identifier = f.read().split(",")
        print("Rules: {}".format(all_identifier))

        json_file = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        print("Json File: {}".format(json_file))
        with open(os.path.join(path, json_file[0]), "r") as fout:
            self.src_pkg_json = json.load(fout)

        # Get all server Rule with dependency and portlist
        for identifier in all_identifier:
            rule = self.check_dpi_server_rule(identifier)
            if rule:
                rule_type = self.check_server_rule(rule)
                if rule_type == "server":
                    server_rules.append(identifier)
                    if rule["RequiresTBUIDs"]:
                        dep_rule = self.get_depend_rule(rule)
                        all_dep_rules.add(dep_rule["Identifier"])
                        self.get_port_info(dep_rule, portlist_set)
                elif rule_type == "client":
                    client_rules.append(identifier)
                    if rule["RequiresTBUIDs"]:
                        dep_rule = self.get_depend_rule(rule)
                        client_dep_rules.add(dep_rule["Identifier"])
                        self.get_port_info(dep_rule, portlist_set)
                self.get_port_info(rule, portlist_set)
            else:
                non_dpi_rules.append(identifier)
        # Get Good Rule dependency
        for identifier in grule_list:
            rule = self.check_dpi_server_rule(identifier)
            if rule:
                if rule["RequiresTBUIDs"]:
                    dep_rule = self.get_depend_rule(rule)
                    grule_list.append(dep_rule["Identifier"])
                    self.get_port_info(dep_rule, portlist_set)
                self.get_port_info(rule, portlist_set)

        port_list = [dict(port) for port in portlist_set if port]
        identifiers = server_rules[:]
        print("{}\nAll Rules: {}\nServer Rules: {}\nDependency of Server Rules: {}".format("*"*100, all_identifier,
                                                                                       server_rules, all_dep_rules))
        client_rules_iden = client_rules[:]
        print("{}\nClient Rules: {}\nDependency of Client Rules: {}".format("*" * 100, client_rules, client_dep_rules))
        print("Good Rule with Dependency: {}\nNon DPI Rule: {}\n".format(grule_list, non_dpi_rules))
        print("PortList: {}\n{}".format(port_list, "*"*100))

        if len(all_dep_rules) > 0:
            server_rules.extend(list(all_dep_rules))

        if len(client_dep_rules) > 0:
            client_rules.extend(list(client_dep_rules))

        server_rules.extend(non_dpi_rules)
        if os.path.exists(self.server_rule_file):
            os.remove(self.server_rule_file)
        with open(self.server_rule_file, "w") as f:
            f.write(",".join(server_rules))
        with open(self.portlist_file, "w") as f:
            json.dump(port_list, f)
        client_rules.extend(non_dpi_rules)
        if os.path.exists(self.client_rule_file):
            os.remove(self.client_rule_file)
        with open(self.client_rule_file, "w") as f:
            f.write(",".join(client_rules))
        return grule_list, identifiers, client_rules_iden

    def check_dpi_server_rule(self, identifier):
        iden1, iden2 = "PayloadFilter2s", "PayloadFilter2"
        for rules in self.src_pkg_json[iden1][iden2]:
            if rules["Identifier"] == identifier:
                return rules
        return False

    def get_depend_rule(self, rule):
        iden1, iden2 = "PayloadFilter2s", "PayloadFilter2"
        for dep_rule in self.src_pkg_json[iden1][iden2]:
            if dep_rule["TBUID"] in rule["RequiresTBUIDs"].split(","):
                print("{} Dependency Found of {} Rule".format(dep_rule["Identifier"], rule["Identifier"]))
                return dep_rule

    def get_port_info(self, rule, portlist_set):
        port1, port2 = "PortLists", "PortList"
        con1, con2 = "ConnectionTypes", "ConnectionType"
        port_id = "PortListTBUID"
        con_tbuid = "ConnectionTypeTBUID"

        for con in self.src_pkg_json[con1][con2]:
            if rule[con_tbuid] in con["TBUID"].split(","):
                if con[port_id]:
                    for port in self.src_pkg_json[port1][port2]:
                        if con[port_id] in port["TBUID"].split(","):
                            print("- {} Rule PortList, {}".format(rule["Identifier"], port))
                            try:
                                sani_port = {}
                                for k, v in port.items():
                                    if v is None:
                                        sani_port[k] = ""
                                    elif k == "Issued":
                                        pass
                                    else:
                                        sani_port[k] = v
                                return portlist_set.add(tuple(sani_port.items()))
                            except Exception as exc:
                                print("Exception: {} at Port List: {}".format(exc, port))
                else:
                    break

    def check_server_rule(self, rules):
        con1, con2 = "ConnectionTypes", "ConnectionType"
        con_tbuid = "ConnectionTypeTBUID"
        for con in self.src_pkg_json[con1][con2]:
            if rules[con_tbuid] in con["TBUID"].split(","):
                print(rules["Identifier"], con["Name"], con["Direction"])
                if con["Direction"] == "1":
                    return "server"
                elif con["Direction"] == "2":
                    return "client"
                else:
                    return False

    def enable_agent_filter(self, sip, suser, spwd, cip, cuser, cpwd):
        self.enable_filter(sip, suser, spwd, self.s_adap_name)
        self.enable_filter(cip, cuser, cpwd, self.c_adap_name)
        self.activate_dsa(sip, suser, spwd)
        self.activate_dsa(cip, cuser, cpwd)
        print("Waiting 30 sec, Both machine Agent: Enabled, Filter Driver: Enable")
        time.sleep(30)