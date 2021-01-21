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

        grule = "1006436"
        port = "80,5001"
        self.policy_name = "perf_policy"
        self.best_iteration = 5

        self.dsm = DsmPolicy(ver, nexus_uname, nexus_pwd, machine, path_json, self.policy_name, port,
                             self.server_rule_file, self.client_rule_file)
        self.dsm.upload_basic_policy()
        self.dsm.apply_pkg_create_applied_rule_list(self.rule_file)

        instance1 = machine.get_instance_one_id()
        instance2 = machine.get_instance_two_id()
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
            self.perf_scenario_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, "Server Download")
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

    def perf_scenario_test(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name):
        print("{0}\n### {1} ###\n{0}".format("#" * 50, scenario_name))
        # Without Filter Driver
        print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
        wo_filter_all_stats, wo_filter_stats, wof_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser,
                                                        cip, cpwd, c_priv_ip, False, scenario_name, action="wo_filter")
        print("- Without Filter Driver Average Stats: {}\n".format(wof_avg))

        # With Filter Driver
        print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
        w_filter_all_stats, w_filter_stats, wf_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser,
                                                        cip, cpwd, c_priv_ip, False, scenario_name, action="filter")
        print("- With Filter Driver Average Stats: {}\n".format(wf_avg))

        # count = 0
        # for retry in range(2):
        #     if wf_avg > wof_avg:
        #         count += 1
        #         print("- Take Reading-{} Without Filter Rule-{}MBps and with Filter-{}MBps".format(count, wof_avg, wf_avg))
        #         # With Filter Driver
        #         print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
        #         wo_filter_all_stats, wo_filter_stats, wof_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip,
        #                                                                                   cuser,
        #                                                                                   cip, cpwd, c_priv_ip, False,
        #                                                                                   scenario_name,
        #                                                                                   action="wo_filter")
        #         print("- Without Filter Driver Average Stats: {}\n".format(wf_avg))
        #         # Without Filter Driver
        #         print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
        #         w_filter_all_stats, w_filter_stats, wf_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip,
        #                                                                                cuser,
        #                                                                                cip, cpwd, c_priv_ip, False,
        #                                                                                scenario_name, action="filter")
        #         print("- With Filter Driver Average Stats: {}\n".format(wf_avg))

        # With 1 Good Server Rule
        print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        rulelist_stats, iter_rulelist, rulelist_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser, cip,
                                                                                cpwd, c_priv_ip, self.grule_list,
                                                                                scenario_name)
        print("- Threshold Rule with Dependency: {}\n".format(rulelist_avg))
        # count = 0
        # for retry in range(2):
        #     if rulelist_avg > wf_avg:
        #         count += 1
        #         self.dsm.connect()
        #         print("- Take Reading-{} Threshold Rule-{}MBps and with Filter-{}MBps".format(count, rulelist_avg, wf_avg))
        #         # With Filter Driver
        #         print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
        #         # Clean Rules from DSM
        #         self.dsm.clean_rules_from_dsm()
        #         w_filter_all_stats, w_filter_stats, wf_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip,
        #                                                                                cuser,
        #                                                                                cip, cpwd, c_priv_ip, False,
        #                                                                                scenario_name, action="filter")
        #         print("- With Filter Driver Average Stats: {}\n".format(wf_avg))
        #
        #         # With 1 Good Server Rule
        #         print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        #         rulelist_stats, iter_rulelist, rulelist_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip,
        #                                                                                 cuser, cip,
        #                                                                                 cpwd, c_priv_ip,
        #                                                                                 self.grule_list,
        #                                                                                 scenario_name)
        #         print("- Threshold Rule with Dependency Average stats: {}\n".format(rulelist_avg))

        # With All Server/Client side rule
        rule_stats, iter_rule, rule_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd,
                                                                    c_priv_ip, False, scenario_name)
        print("- Rule with Dependency Average stats: {}\n".format(rule_avg))
        # count = 0
        # for retry in range(2):
        #     if rule_avg > rulelist_avg:
        #         count += 1
        #         self.dsm.connect()
        #         print("- Take Reading-{} Rule-{}MBps and Threshold Rule-{}MBps".format(count, rulelist_avg, wf_avg))
        #         # With 1 Good Server Rule
        #         print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        #         rulelist_stats, iter_rulelist, rulelist_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip,
        #                                                                                 cuser, cip,
        #                                                                                 cpwd, c_priv_ip,
        #                                                                                 self.grule_list,
        #                                                                                 scenario_name)
        #         print("- Threshold Rule with Dependency Average stats: {}\n".format(rulelist_avg))
        #         # With All Server side rule
        #         rule_stats, iter_rule, rule_avg = self.apply_rule_get_stats(suser, sip, spwd, s_priv_ip, cuser, cip,
        #                                                                     cpwd,
        #                                                                     c_priv_ip, False, scenario_name)
        #         print("- Rule with Dependency Average stats: {}\n".format(rule_avg))

        wo_filter_stats.append(wof_avg)
        w_filter_stats.append(wf_avg)
        iter_rulelist.append(rulelist_avg)
        iter_rule.append(rule_avg)

        # Scenrario complete
        print("- Without filter: {}\n- With filter: {}\n- One-Good Rule: {}\n- All Server Rule: {}".format(
              wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule))
        self.col = ['Without Filter Driver', 'With Filter Driver + No Rule', 'One Good Rule']
        if scenario_name == "Server Upload" or scenario_name == "Server Download":
            self.col.append('Server Rule (No. of Rules: {})'.format(len(self.server_rule)))
        elif scenario_name == "Client Download":
            self.col.append('Client Rule (No. of Rules: {})'.format(len(self.client_rules)))
        df = pd.DataFrame([wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule], index=self.col,
                          columns=self.title)
        # Create Html
        self.create_html_table(df, scenario_name)
        # Create Bar Diagram
        self.create_bar_chart([wof_avg, wf_avg, rulelist_avg, rule_avg], scenario_name)

    def apply_rule_get_stats(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, grule_list, scenario_name,
                             action="reading"):
        if action == "wo_filter":
            # Disable Server Agent
            self.disable_dsa(sip, suser, spwd)
            # Disable Server filter
            self.disable_filter(sip, suser, spwd, self.s_adap_name)
            # Disable Client Agent
            # self.disable_dsa(cip, cuser, cpwd)
            # # Disable Client filter
            # self.disable_filter(cip, cuser, cpwd, self.c_adap_name)
            print("{0}\n{3}-{1} and {4}-{2} Agent: Disabled from DSM\n{3}-{1} Filter: Disabled from network driver\n"
                  "{0}".format(self.header, cip, sip, self.ip_type[cip], self.ip_type[sip]))
        elif action == "filter":
            # Activate Server Agent
            self.activate_dsa(sip, suser, spwd)
            # Enable Server Filter
            self.enable_filter(sip, suser, spwd, self.s_adap_name)
            print("{0}\n{2}-{1} Agent: Enabled from DSM\n{2}-{1} Filter: Enabled from Network Driver\n{0}".format(
                                                                                self.header, cip, self.ip_type[cip]))
        elif action == "rule":
            identifier = self.dsm.apply_rule(scenario_name, rule_list=grule_list)
            print("{0}{0}\n# {1} Rule Applied \n{0}{0}".format(self.header, identifier))

        print("Waiting 2 min")
        time.sleep(120)
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
    parser.add_argument('--uname', type=str, help="Nexus username")
    parser.add_argument('--pwd', type=str, help="Nexus password")
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    args = parser.parse_args()

    with open(args.machine_info) as fout:
        machine_info = json.load(fout)
    scenario = PerformanceScenario(machine_info,
                                   args.dsm_version,
                                   args.access_key, args.secret_key,
                                   args.stats, args.graph, args.path,
                                   args.uname, args.pwd,
                                   args.scenario
                                   )
