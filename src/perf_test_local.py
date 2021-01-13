import argparse
from perf_common import PerfCommon
import time
import simplejson as json
import pandas as pd
from dsm_operation import DsmPolicy
from get_machine_info import MachineInfo
import requests


class PerformanceScenario(PerfCommon):
    def __init__(self, machine_info, ver, access_key, secret_key, stats, graph, path_json, nexus_uname, nexus_pwd, scenario):
        machine = MachineInfo(machine_info)
        PerfCommon.__init__(self, stats, graph)

        grule = "1006436"
        port = "80,5001"
        self.policy_name = "perf_policy"
        self.best_iteration = 5

        self.dsm = DsmPolicy(ver, nexus_uname, nexus_pwd, machine, path_json, self.policy_name, port,
                             self.server_rule_file, self.client_rule_file)
        # self.dsm.upload_basic_policy()
        # self.dsm.apply_pkg_create_applied_rule_list(self.rule_file)

        instance1 = machine.get_instance_one_id()
        instance2 = machine.get_instance_two_id()
        region = machine.get_region()
        pem_file = machine.get_pem_file()
        sip, s_priv_ip = "15.223.3.41", "172.31.27.249"
        # sip, s_priv_ip = self.reboot_instance(instance1, access_key, secret_key, region)
        print("Server Agent {} instance -> Public IP:{}, Private IP: {}".format(instance1, sip, s_priv_ip))
        cip, c_priv_ip = "35.183.131.91", "172.31.27.146"
        # cip, c_priv_ip = self.reboot_instance(instance2, access_key, secret_key, region)
        print("Client Agent {} instance -> Public IP:{}, Private IP: {}".format(instance2, cip, c_priv_ip))

        self.ip_type = {sip: "Server", cip: "Client"}
        # Get the password
        # spwd = PerformanceScenario.get_pwd(region, access_key, secret_key, instance1, pem_file)
        # cpwd = PerformanceScenario.get_pwd(region, access_key, secret_key, instance2, pem_file)
        spwd = "&oYOI%N?HQyQhZVbD7v?yzqlrP(?KP!L"
        cpwd = "!(i@S=suaqdmjzbQ*fH5T-vM65!(4?UR"
        # Get the Server Rule and dependency with portlist
        self.grule_list, self.server_rule, self.client_rules = self.get_dependency_portlist(path_json, grule)
        self.dsm.upload_basic_policy(change_policy=True)
        self.title = ["iter-1 (MB/s)", "iter-2 (MB/s)", "iter-3 (MB/s)", "iter-4 (MB/s)", "iter-5 (MB/s)",
                      "Average (MB/s)"]
        self.path = machine.get_pkg_path()
        suser = machine.get_instance_one_user()
        cuser = machine.get_instance_two_user()
        # Get adaptor name
        self.s_adap_name = self.get_adaptor_name(sip, suser, spwd)
        self.c_adap_name = self.get_adaptor_name(cip, cuser, cpwd)
        # Server Upload
        # self.test_scenario(sip, spwd, cip, cpwd, s_priv_ip, c_priv_ip, suser, cuser, "Server Upload")
        # Win 7 -> Client
        # Win 8 -> Server
        # --> Server side rule on server
        # pcattcp(sip, suser, spwd) -> Server machine
        # pcattcp(cip, cuser, cpwd, sip) -> Client machine -> Reading
        # 80,5001
        if scenario == "Server_Upload" or scenario == "All":
            self.ip_type = {cip: "Server", sip: "Client"}
            print("Server Machine Public IP:{}, Private IP: {}".format(cip, c_priv_ip))
            print("Client Machine Public IP:{}, Private IP: {}".format(sip, s_priv_ip))
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Server Upload")
        # Testing Server Upload Scenario based on discussion with Arun and Sunil on 7-Jan-2021
        if scenario == "Server_Download" or scenario == "All":
            if scenario == "All":
                # Clean Rules from DSM
                self.dsm.clean_rules_from_dsm()
                # Enable both agents and filter
                self.enable_agent_filter(sip, suser, spwd, cip, cuser, cpwd)
            # Server Download
            # Win 7 -> server
            # Win 8 -> client
            # --> Server side rule on server
            # self.run_nginx(sip, suser, spwd) -> Server machine
            # self.run_ab(cip, cuser, cpwd, sip) -> Client machine -> Reading
            # 80,5001
            self.ip_type = {sip: "Server", cip: "Client"}
            print("Server Machine Public IP:{}, Private IP: {}".format(sip, s_priv_ip))
            print("Client Machine Public IP:{}, Private IP: {}".format(cip, c_priv_ip))
            self.perf_scenario_test(cuser, cip, cpwd, c_priv_ip, suser, sip, spwd, s_priv_ip, "Server Download")
        if scenario == "Client_Download" or scenario == "All":
            if scenario == "All":
                # Clean Rules from DSM
                self.dsm.clean_rules_from_dsm()
                # Enable both agents and filter
                self.enable_agent_filter(sip, suser, spwd, cip, cuser, cpwd)
            # Server Download
            # Win 7 -> server
            # Win 8 -> client
            # --> Server side rule on server
            # self.run_nginx(sip, suser, spwd) -> Server machine
            # self.run_ab(cip, cuser, cpwd, sip) -> Client machine -> Reading
            # 80,5001
            self.ip_type = {sip: "Server", cip: "Client"}
            print("Server Machine Public IP:{}, Private IP: {}".format(sip, s_priv_ip))
            print("Client Machine Public IP:{}, Private IP: {}".format(cip, c_priv_ip))
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Client Download")
        """
        # Clean Rules from DSM
        self.dsm.clean_rules_from_dsm()
        # Enable both agents and filter
        self.enable_agent_filter(sip, suser, spwd, cip, cuser, cpwd)
        # Client Download
        self.test_scenario(sip, spwd, cip, cpwd, s_priv_ip, c_priv_ip, suser, cuser, "Client Download")
        """

    def perf_scenario_test(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name):
        print("{0}\n### {1} ###\n{0}".format("#" * 50, scenario_name))
        # Disable Server filter
        self.disable_filter(sip, suser, spwd, self.s_adap_name)
        ################## Without Filter Driver ###########################
        print("{0}\n# Without Filter Driver #\n{0}\n".format(self.header))
        # Disable Server Agent
        self.disable_dsa(sip, suser, spwd)
        # Disable Client Agent
        self.disable_dsa(cip, cuser, cpwd)
        # Disable Client filter
        self.disable_filter(cip, cuser, cpwd, self.c_adap_name)
        print("{0}\nWaiting 2 min\n{3}-{1} and {4}-{2} Machines: Agent Disabled from DSM\n{3}-{1} Machine: Filter "
              "Disabled from network driver\n{0}".format(self.header, cip, sip, self.ip_type[cip], self.ip_type[sip]))
        time.sleep(120)
        wo_filter_all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip,scenario_name)
        wo_filter_stats = wo_filter_all_stats[:self.best_iteration]
        wof_avg = round(sum(map(float, wo_filter_stats)) / len(wo_filter_stats), 2)
        print("{0}{0}\n- Without Filter Driver Bandwidth: {1}\n- Average Bandwidth: {2} MBps\n{0}{0}\n".format(
            self.header, wo_filter_stats, wof_avg))
        ################## With Filter Driver ###########################
        print("{0}\n# With Filter Driver #\n{0}\n".format(self.header))
        # Enable Client Filter
        self.enable_filter(cip, cuser, cpwd, self.c_adap_name)
        # Activate Cleint Agent
        self.activate_dsa(cip, cuser, cpwd)
        print("{0}\nWaiting 2 min\n{2}-{1} Machine: Agent Enabled from DSM\n{2}-{1} Machine: Filter Enabled "
              "from Network Driver\n{0}".format(self.header, cip, self.ip_type[cip]))
        time.sleep(120)
        w_filter_all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip,scenario_name)
        w_filter_stats = w_filter_all_stats[:self.best_iteration]
        wf_avg = round(sum(map(float, w_filter_stats)) / len(w_filter_stats), 2)
        print("{0}{0}\n- With Filter Driver Bandwidth: {1}\n- Average Bandwidth: {2} MBps\n{0}{0}\n".format(self.header,
                                                                                                            w_filter_stats,
                                                                                                            wf_avg))
        ################## With 1 Good Server Rule ###########################
        print("{0}\n# With {1} Good Server Rule with Dependency #\n{0}\n".format(self.header, self.grule_list))
        # 1006436
        identifier = self.dsm.apply_rule(scenario_name, rule_list=self.grule_list)
        print("{0}{0}\nWaiting 2 min After {1} Good Rule Applied \n{0}{0}".format(self.header, identifier))
        time.sleep(120)
        good_rule_all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip,scenario_name)
        good_rule = good_rule_all_stats[:self.best_iteration]
        gr_avg = round(sum(map(float, good_rule)) / len(good_rule), 2)
        print("{0}{0}\n- With 1 Good Server Rule: {1}\n- Average Bandwidth: {2} MBps\n{0}{0}\n".format(self.header,
                                                                                                       good_rule,
                                                                                                       gr_avg))
        ################## With All Server side rule ###########################
        identifier = self.dsm.apply_rule(scenario_name)
        print("{0}{0}\nWaiting 2 min, After {1} Rule Applied\n{0}{0}".format(self.header, identifier))
        time.sleep(120)
        with_all_server_rule_all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip,scenario_name)
        with_all_server_rule = with_all_server_rule_all_stats[:self.best_iteration]
        all_rule_avg = round(sum(map(float, with_all_server_rule)) / len(with_all_server_rule), 2)
        print("{0}{0}\n- With All Server side rule: {1}\n- Average Bandwidth: {2} MBps\n{0}{0}\n".format(self.header,
                                                                                                         with_all_server_rule,
                                                                                                         all_rule_avg))
        wo_filter_stats.append(wof_avg)
        w_filter_stats.append(wf_avg)
        good_rule.append(gr_avg)
        with_all_server_rule.append(all_rule_avg)
        ############################### Scenrario complete ###################################
        print("- Without filter: {}\n- With filter: {}\n- One-Good Rule: {}\n- All Server Rule: {}".format(
              wo_filter_stats, w_filter_stats, good_rule, with_all_server_rule))
        self.col = ['Without Filter Driver', 'With Filter Driver + No Rule', 'One Good Rule']
        if scenario_name == "Server Upload" or scenario_name == "Server Download":
            self.col.append('Server Rule (No. of Rules: {})'.format(len(self.server_rule)))
        elif scenario_name == "Client Download":
            self.col.append('Client Rule (No. of Rules: {})'.format(len(self.client_rules)))
        df = pd.DataFrame([wo_filter_stats, w_filter_stats, good_rule, with_all_server_rule], index=self.col,
                          columns=self.title)
        # Create Html
        self.create_html_table(df, scenario_name)
        # Create Bar Diagram
        self.create_bar_chart([wof_avg, wf_avg, gr_avg, all_rule_avg], scenario_name)

    def enable_agent_filter(self, sip, suser, spwd, cip, cuser, cpwd):
        self.enable_filter(sip, suser, spwd, self.s_adap_name)
        self.enable_filter(cip, cuser, cpwd, self.c_adap_name)
        self.activate_dsa(sip, suser, spwd)
        self.activate_dsa(cip, cuser, cpwd)
        print("Waiting 30 sec, Both machine Agent: Enabled, Filter Driver: Enable")
        time.sleep(30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--access_key', type=str, help="Need access key to get the password of instance")
    parser.add_argument('--secret_key', type=str, help="Need secret key to get the password of instance")
    parser.add_argument('--machine_info', type=str, help="Need infra credential of dsm and dsa")
    parser.add_argument('--dsm_version', type=str, help="Need dsm version to decide the policy template")
    parser.add_argument('--stats', type=str, help="Html file name")
    parser.add_argument('--graph', type=str, help="Graph file name")
    parser.add_argument('--path', type=str, help="Graph file name")
    parser.add_argument('--uname', type=str, help="Nexus username")
    parser.add_argument('--pwd', type=str, help="Nexus password")
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    args = parser.parse_args()

    url = "https://dsnexus.trendmicro.com:8443/nexus/repository/dslabs/performance-test/performance-test/21-002.dsru/17/manifest.json"
    machine_info = requests.get(url, auth=(args.uname, args.pwd)).json()

    scenario = PerformanceScenario(machine_info,
                                   args.dsm_version,
                                   # args.package_url,
                                   args.access_key, args.secret_key,
                                   args.stats, args.graph, args.path,
                                   args.uname, args.pwd,
                                   args.scenario
                                   )
