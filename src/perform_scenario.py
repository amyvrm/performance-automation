import argparse
from perf_common import PerfCommon
import time
import simplejson as json
import pandas as pd
from dsm_operation import DsmPolicy
from get_machine_info import MachineInfo


class PerformanceScenario(PerfCommon):
    def __init__(self, machine_info, ver, access_key, secret_key, stats, graph, path_json, nexus_uname, nexus_pwd, scenario):
        machine = MachineInfo(machine_info)
        PerfCommon.__init__(self, stats, graph)

        port = "80,5001"
        self.policy_name = "perf_policy"
        self.best_iteration = 5

        self.dsm = DsmPolicy(ver, nexus_uname, nexus_pwd, machine, path_json, self.policy_name, port,
                             self.server_rule_file, self.client_rule_file)
        self.dsm.upload_basic_policy()
        self.dsm.apply_pkg_create_applied_rule_list(self.rule_file)

        if scenario == "Client_Download":
            grule = "1005366"
            instance1 = machine.get_instance_two_id()
            instance2 = machine.get_instance_one_id()
            suser = machine.get_instance_two_user()
            cuser = machine.get_instance_one_user()
        else:
            grule = "1006436"
            instance1 = machine.get_instance_one_id()
            instance2 = machine.get_instance_two_id()
            suser = machine.get_instance_one_user()
            cuser = machine.get_instance_two_user()

        region = machine.get_region()
        pem_file = machine.get_pem_file()
        sip, s_priv_ip = self.reboot_instance(instance1, access_key, secret_key, region)
        print("Server Agent {} instance -> Public IP:{}, Private IP: {}".format(instance1, sip, s_priv_ip))
        cip, c_priv_ip = self.reboot_instance(instance2, access_key, secret_key, region)
        print("Client Agent {} instance -> Public IP:{}, Private IP: {}".format(instance2, cip, c_priv_ip))

        self.ip_type = {sip: "Server", cip: "Client"}
        # Get the password
        spwd = PerformanceScenario.get_pwd(region, access_key, secret_key, instance1, pem_file, "Server")
        cpwd = PerformanceScenario.get_pwd(region, access_key, secret_key, instance2, pem_file, "Client")

        # Get the Server Rule and dependency with portlist
        self.grule_list, self.server_rule, self.client_rules = self.get_dependency_portlist(path_json, grule)
        self.dsm.upload_basic_policy(change_policy=True)
        self.title = ["iter-1 (MB/s)", "iter-2 (MB/s)", "iter-3 (MB/s)", "iter-4 (MB/s)", "iter-5 (MB/s)",
                      "Average (MB/s)"]
        self.path = machine.get_pkg_path()

        # Get adaptor name
        self.s_adap_name = self.get_adaptor_name(sip, suser, spwd)
        self.c_adap_name = self.get_adaptor_name(cip, cuser, cpwd)

        self.ip_type = {sip: "Server", cip: "Client"}
        print("Server Machine Public IP:{}, Private IP: {}".format(sip, s_priv_ip))
        print("Client Machine Public IP:{}, Private IP: {}".format(cip, c_priv_ip))

        if scenario == "Server_Upload" or scenario == "All":
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Server Upload")
        # Testing Server Upload Scenario based on discussion with Arun and Sunil on 7-Jan-2021
        if scenario == "Server_Download" or scenario == "All":
            if scenario == "All":
                # Clean Rules from DSM
                self.dsm.clean_rules_from_dsm()
                # Enable both agents and filter
                self.enable_agent_filter(sip, suser, spwd, cip, cuser, cpwd)
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Server Download")
        if scenario == "Client_Download" or scenario == "All":
            if scenario == "All":
                # Clean Rules from DSM
                self.dsm.clean_rules_from_dsm()
                # Enable both agents and filter
                self.enable_agent_filter(sip, suser, spwd, cip, cuser, cpwd)
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Client Download")

    def perf_scenario_test(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name):
        print("{0}\n### {1} ###\n{0}".format("#" * 50, scenario_name))
        # Without Filter Driver
        print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
        wo_filter_all_stats, wo_filter_stats, wof_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser,
                                                                                  cip, cpwd, c_priv_ip, False,
                                                                                  scenario_name, action="wo_filter")
        print("- Without Filter Driver Average Stats: {} MBps\n".format(wof_avg))

        # With Filter Driver
        print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
        w_filter_all_stats, w_filter_stats, wf_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser,
                                                                               cip, cpwd, c_priv_ip, False,
                                                                               scenario_name, action="filter")
        print("- With Filter Driver Average Stats: {} MBps\n".format(wf_avg))

        # With 1 Good Server Rule
        print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        rulelist_stats, iter_rulelist, rulelist_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser, cip,
                                                                                cpwd, c_priv_ip, self.grule_list,
                                                                                scenario_name, action="rule")
        print("- Threshold Rule with Dependency: {} MBps\n".format(rulelist_avg))

        # With All Server/Client side rule
        rule_stats, iter_rule, rule_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd,
                                                                    c_priv_ip, False, scenario_name, action="rule")
        print("- Rule with Dependency Average stats: {} MBps\n".format(rule_avg))

        wo_filter_stats.append(wof_avg)
        w_filter_stats.append(wf_avg)
        iter_rulelist.append(rulelist_avg)
        iter_rule.append(rule_avg)

        # Scenrario complete
        print("- Without filter: {}\n- With filter: {}\n- Best Case Rule: {}\n- All Server Rule: {}".format(
              wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule))
        self.col = ['Without Filter Driver', 'With Filter Driver + No Rule', 'Best Case Rule']
        if scenario_name == "Server Upload" or scenario_name == "Server Download":
            self.col.append('Server Rules (No. of Rules: {})'.format(len(self.server_rule)))
        elif scenario_name == "Client Download":
            self.col.append('Client Rules (No. of Rules: {})'.format(len(self.client_rules)))
        df = pd.DataFrame([wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule], index=self.col,
                          columns=self.title)
        # Create Html
        self.create_html_table(df, scenario_name)
        # Create Bar Diagram
        self.create_bar_chart([wof_avg, wf_avg, rulelist_avg, rule_avg], scenario_name)

    def apply_rule_get_stats(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, grule_list, scenario_name,
                             action="reading"):
        if scenario_name == "Client Download":
            ip, user, pwd, adaptor = cip, cuser, cpwd, self.c_adap_name
        else:
            ip, user, pwd, adaptor = sip, suser, spwd, self.s_adap_name
        if action == "wo_filter":
            # Disable Server Agent
            self.disable_dsa(ip, user, pwd)
            # Disable Server filter
            self.disable_filter(ip, user, pwd, adaptor)
            print("{0}\n{2}-{1} Agent: Disabled from DSM\n{2}-{1} Filter: Disabled from network driver\n{0}".format(
                  self.header, ip, self.ip_type[ip]))
        elif action == "filter":
            # Activate Server Agent
            self.activate_dsa(ip, user, pwd)
            # Enable Server Filter
            self.enable_filter(ip, user, pwd, adaptor)
            print("{0}\n{2}-{1} Agent: Enabled from DSM\n{2}-{1} Filter: Enabled from Network Driver\n{0}".format(
                                                                                self.header, ip, self.ip_type[ip]))
        elif action == "rule":
            self.dsm.connect()
            identifier = self.dsm.apply_rule(scenario_name, rule_list=grule_list)
            print("{0}{0}\n# {1} Rule Applied \n{0}{0}".format(self.header, identifier))

        print("Waiting 3 min")
        time.sleep(180)
        all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name)
        iter_stats = all_stats[:self.best_iteration]
        avg = round(sum(map(float, iter_stats)) / len(iter_stats), 2)
        print("{0}{0}\n- {1} iteration stats {2} MBps\n- Average Bandwidth: {3} MBps\n{0}{0}\n".format(self.header,
                                                                            len(iter_stats), iter_stats, avg))
        return all_stats, iter_stats, avg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--access_key', type=str, help="Need access key to get the password of instance")
    parser.add_argument('--secret_key', type=str, help="Need secret key to get the password of instance")
    parser.add_argument('--machine_info', type=str, help="Need infra credential of dsm and dsa")
    parser.add_argument('--dsm_version', type=str, help="Need dsm version to decide the policy template")
    parser.add_argument('--stats', type=str, help="Html file name")
    parser.add_argument('--graph', type=str, help="Graph file name")
    parser.add_argument('--path', type=str, help="Graph file name")
    parser.add_argument('--nexus_uname', type=str, help="Nexus username")
    parser.add_argument('--nexus_pwd', type=str, help="Nexus password")
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    args = parser.parse_args()

    with open(args.machine_info) as fout:
        machine_info = json.load(fout)
    scenario = PerformanceScenario(machine_info,
                                   args.dsm_version,
                                   args.access_key, args.secret_key,
                                   args.stats, args.graph, args.path,
                                   args.nexus_uname, args.nexus_pwd,
                                   args.scenario
                                   )
