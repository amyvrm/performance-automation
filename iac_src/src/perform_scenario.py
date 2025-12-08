import argparse
from perf_common import PerfCommon
import time
import shutil
import pandas as pd
from dsm_operation import DsmPolicy
from get_machine_info import MachineInfo
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class PerformanceScenario(PerfCommon):
    def __init__(self, machine_info, ver, access_key, secret_key, stats, graph, path_json, jfrog_token,
                 scenario,rule_id, individual_rule_test):
        try:
            machine = MachineInfo(machine_info)
            PerfCommon.__init__(self, stats, graph)

            print(f"individual_rule_test: {individual_rule_test}")

            port = "80,5001"
            self.policy_name = "perf_policy"
            self.best_iteration = 5

            print(f"Rule Id's Perform_scenario: {rule_id}")
            rule_file = ""

            if rule_id != "0":
                rule_file = rule_id.split(',')
            else:
                rule_file = self.rule_file

            print(f"Rule File: {rule_file}")

            dsm_private_ips = machine.get_dsm_private_ips()
            print(f"Debug: DSM Private IPs response: {dsm_private_ips}")

            all_dsm_server = list(dsm_private_ips.get('dsm-private-ips', {}).values())

            dsm = {}  # Initialize dsm as a dictionary
            for x in range(0, len(all_dsm_server)):
                dsm_server = all_dsm_server[x]
                dsm[x] = DsmPolicy(ver, jfrog_token, machine, path_json, self.policy_name, port,
                                        self.server_rule_file, self.client_rule_file, self.portlist_file, dsm_server)

            grule = "1005366" if scenario == "Client_Download" else "1006436"

            all_instance_server = list(machine.get_all_windows_instance_ids().get('dsa-windows-ids', {}).values())
            all_instance_agent = list(machine.get_all_windows_agent_ids().get('dsa-windows_agent-ids', {}).values())

            all_instance = all_instance_server + all_instance_agent

            suser = machine.get_instance_one_user()
            cuser = machine.get_instance_two_user()

            region = machine.get_region()
            pem_file = machine.get_pem_file()

            def sequential_dsm_tasks(dsm, rule_file):
                try:
                    print(f"→ Starting sequential_dsm_tasks for rule_file: {rule_file}", flush=True)
                    print("→ Calling dsm.upload_basic_policy()...", flush=True)
                    dsm.upload_basic_policy()
                    print("✓ upload_basic_policy completed", flush=True)
                    
                    print("→ Calling dsm.apply_pkg_create_applied_rule_list()...", flush=True)
                    summary, identifiers = dsm.apply_pkg_create_applied_rule_list(rule_file)
                    print("✓ apply_pkg_create_applied_rule_list completed", flush=True)
                    print(f"✓ sequential_dsm_tasks completed successfully", flush=True)
                    return summary, identifiers
                except Exception as e:
                    print(f"✗ Error in sequential_dsm_tasks: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    return None, None

            def reboot_instance(instance):
                try:
                    return self.reboot_instance(instance, access_key, secret_key, region)
                except Exception as e:
                    print(f"Error in reboot_instance: {e}")
                    return None

            with ThreadPoolExecutor(max_workers=len(all_instance)) as executor:
                try:
                    # Submit DSM tasks
                    future_dsm_tasks = [executor.submit(
                            sequential_dsm_tasks, dsm[x], rule_file) for x in range(len(dsm))]

                    # Submit reboot tasks
                    future_to_instance = {
                    executor.submit(reboot_instance, instance): instance for instance in all_instance
                    }
                    
                    # Collect reboot results
                    results = {future_to_instance[future]: future.result() for future in future_to_instance}
                    print(f"✓ Reboot tasks completed for {len(results)} instances")

                    # Collect DSM task results (only call result() once per future)
                    print("Waiting for DSM tasks to complete...", flush=True)
                    summaries_and_identifiers = [future.result() for future in future_dsm_tasks]
                    print(f"✓ DSM tasks completed: {summaries_and_identifiers}", flush=True)
                    
                    # Unzip results
                    summary, identifiers = zip(*summaries_and_identifiers)
                except Exception as e:
                    print(f"Error in ThreadPoolExecutor block: {e}")
                    import traceback
                    traceback.print_exc()
                    summary, identifiers, results = [], [], []

            _sip = [] 
            _cip = [] 
            _s_priv_ip = [] 
            _c_priv_ip = []
            for x in range(0, len(all_instance_server)):
                try:
                    print("Server Instance Public IP: {}".format(results[all_instance_server[x]][0]))
                    print("Server Instance Private IP: {}".format(results[all_instance_server[x]][1]))
                    _sip.append(results[all_instance_server[x]][0])
                    _s_priv_ip.append(results[all_instance_server[x]][1])
                except Exception as e:
                    print(f"Error processing server instance {x}: {e}")
            for x in range(0, len(all_instance_agent)):
                try:
                    print("Client Instance Public IP: {}".format(results[all_instance_agent[x]][0]))
                    print("Client Instance Private IP: {}".format(results[all_instance_agent[x]][1]))
                    _cip.append(results[all_instance_agent[x]][0])
                    _c_priv_ip.append(results[all_instance_agent[x]][1])
                except Exception as e:
                    print(f"Error processing agent instance {x}: {e}")

            try:
                sip, s_priv_ip = results[all_instance_server[0]]
                print("Server Agent {} instance -> Public IP:{}, Private IP: {}".format(all_instance_server[0], sip, s_priv_ip))

                cip, c_priv_ip = results[all_instance_agent[0]]
                print("Client Agent {} instance -> Public IP:{}, Private IP: {}".format(all_instance_agent[0], cip, c_priv_ip))
            except Exception as e:
                print(f"Error extracting main server/client IPs: {e}")

            self.ip_type = {}
            for x in range(0, len(all_instance_server)):
                try:
                    self.ip_type[x] = {_s_priv_ip[x]: "Server", _c_priv_ip[x]: "Client"}
                    print("ip_type_forloop: {}".format(self.ip_type[x]))
                except Exception as e:
                    print(f"Error setting ip_type for {x}: {e}")
            try:
                print(f"ip_type 0: {self.ip_type[0]}")
                print(f"ip_type 1: {self.ip_type[1]}")
            except Exception as e:
                print(f"Error printing ip_type: {e}")

            self.title = ["iter-1 (MB/s)", "iter-2 (MB/s)", "iter-3 (MB/s)", "iter-4 (MB/s)", "iter-5 (MB/s)",
                      "Average (MB/s)"]
            self.path = machine.get_pkg_path()

            _spwd = []
            _cpwd = []
            for x in range(0, len(all_instance_server)):
                try:
                    _spwd.append(PerformanceScenario.get_pwd(region, access_key, secret_key, all_instance_server[x], pem_file, "Server"))
                except Exception as e:
                    print(f"Error getting server password for {x}: {e}")
            for x in range(0, len(all_instance_agent)):
                try:
                    _cpwd.append(PerformanceScenario.get_pwd(region, access_key, secret_key, all_instance_agent[x], pem_file, "Client"))
                except Exception as e:
                    print(f"Error getting client password for {x}: {e}")

            print(f"_sip: {_sip} \n | _cip: {_cip} \n | _s_priv_ip: {_s_priv_ip} \n | _c_priv_ip: {_c_priv_ip}\n")


            self._s_adap_name = []
            self._c_adap_name = []

            _sip, _cip = _s_priv_ip, _c_priv_ip

            # Prepare machine dicts for parallel preload
            server_machines = [
                {'ip': _sip[x], 'user': suser, 'pwd': _spwd[x]}
                for x in range(len(all_instance_server))
            ]
            client_machines = [
                {'ip': _cip[x], 'user': cuser, 'pwd': _cpwd[x]}
                for x in range(len(all_instance_agent))
            ]
            all_machines = server_machines + client_machines
            # Preload all adapters in parallel
            adapter_map = self.preload_adapter_names(all_machines)
            # Extract results
            self._s_adap_name = [adapter_map.get(_sip[x]) for x in range(len(all_instance_server))]
            self._c_adap_name = [adapter_map.get(_cip[x]) for x in range(len(all_instance_agent))]

            print(f"Lengths: _sip: {len(_sip)} | _cip: {len(_cip)} | self._s_adap_name: {len(self._s_adap_name)} | self._c_adap_name: {len(self._c_adap_name)} | self.ip_type: {len(self.ip_type)} | _spwd: {len(_spwd)} | _cpwd: {len(_cpwd)}")

            from perf_individual_rule import PerfIndividualRule
            from perf_package_rule import PerfPackageRule
            def run_parallel_tasks(rule_file):
                try:
                    print(f"Rule File: {rule_file}")
                    if isinstance(rule_file, str):
                        with open(rule_file, "r") as f:
                            identifiers = f.read().strip().split(",")
                        print(f"Identifiers from file: {identifiers}")
                    elif isinstance(rule_file, list):
                        identifiers = rule_file
                    print(f"Dynamically extracted identifiers: {identifiers}")
                    # Submit perfRules as a separate task
                    with ThreadPoolExecutor(max_workers=len(all_instance_server)) as executor:
                        if individual_rule_test == "False":
                            print("Running PerfPackageRule task")
                            executor.submit(PerfPackageRule, dsm[0], scenario, path_json, grule, identifiers, suser, _sip[0], _spwd[0], _s_priv_ip[0],
                                    cuser, _cip[0], _cpwd[0], _c_priv_ip[0], summary, stats, graph,
                                    self._s_adap_name[0], self._c_adap_name[0], self.title, self.ip_type[0],
                                    self.path, self.best_iteration)
                        else:
                            # Run PerfPackageRule and PerfIndividualRule tasks in parallel
                            futures = []
                            print(f"Running PerfPackageRule task on else block: {identifiers}")
                            futures.append(executor.submit(
                                PerfPackageRule, dsm[0], scenario, path_json, grule, identifiers, suser, _sip[0], _spwd[0], _s_priv_ip[0],
                                cuser, _cip[0], _cpwd[0], _c_priv_ip[0], summary, stats, graph,
                                self._s_adap_name[0], self._c_adap_name[0], self.title, self.ip_type[0],
                                self.path, self.best_iteration
                            ))
                            for i in range(1, len(all_instance_server)):
                                print(f"Iterations: {i}")
                                if i <= len(identifiers):
                                    print(f"Running PerfIndividualRule task on else block: {identifiers[i-1]}")
                                    futures.append(executor.submit(
                                        PerfIndividualRule,
                                        dsm[i], scenario, path_json, grule, identifiers[i-1], suser, _sip[i], _spwd[i], _s_priv_ip[i],
                                        cuser, _cip[i], _cpwd[i], _c_priv_ip[i], summary, stats, graph,
                                        self._s_adap_name[i], self._c_adap_name[i], self.title, self.ip_type[i],
                                        self.path, self.best_iteration
                                    ))
                                else:
                                    print(f"Skipping iteration {i} as no identifier is available.")
                            # Wait for all futures to complete
                            results = []
                            for future in as_completed(futures):
                                try:
                                    result = future.result()
                                    results.append(result)
                                    print(f"Task completed with result: {result}")
                                except Exception as e:
                                    print(f"Task raised an exception: {e}")
                            print(f"All tasks completed. Results: {results}")
                except Exception as e:
                    print(f"Error in run_parallel_tasks: {e}")
            # Call the function to execute tasks
            run_parallel_tasks(rule_file)
        except Exception as e:
            print(f"Error in PerformanceScenario.__init__: {e}")
        finally:
            print("PerformanceScenario Completed Closing DSM connections")
            for x in range(0, len(dsm)):
                try:
                    dsm[x].disconnect()
                except Exception as e:
                    print(f"Error closing DSM connection for {x}: {e}")

    def apply_rule_get_stats(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, grule_list, scenario_name, c_adaptor=None, s_adaptor=None,
                             action="reading", dsm=None):
        try:
            # Choose target host and adapter strictly from provided args to avoid cross-class attribute access
            if scenario_name == "Client Download":
                ip, user, pwd, adaptor = cip, cuser, cpwd, c_adaptor
            else:
                ip, user, pwd, adaptor = sip, suser, spwd, s_adaptor
            if adaptor is None:
                raise Exception("Adapter name not provided for selected scenario")
            if action == "wo_filter":
                dsm.clean_rules_from_dsm()
                # Disable Server Agent
                self.disable_dsa(ip, user, pwd)
                # Disable Server filter (using parallel for consistency)
                machines_to_disable = [{
                    'ip': ip,
                    'user': user,
                    'pwd': pwd,
                    'adaptor_name': adaptor
                }]
                self.disable_filters_parallel(machines_to_disable)
                # Wait for filter driver state to settle
                import time
                time.sleep(10)
                print("{0}\n{2}-{1} Agent: Disabled from DSM\n{2}-{1} Filter: Disabled from network driver\n{0}".format(
                      self.header, ip, self.ip_type[ip]))
            elif action == "filter":
                dsm.clean_rules_from_dsm()
                # Activate Server Agent
                self.activate_dsa(ip, user, pwd)
                # Enable Server Filter (using parallel for consistency)
                machines_to_enable = [{
                    'ip': ip,
                    'user': user,
                    'pwd': pwd,
                    'adaptor_name': adaptor
                }]
                self.enable_filters_parallel(machines_to_enable)
                # Wait for filter driver state to settle
                import time
                time.sleep(10)
                print("{0}\n{2}-{1} Agent: Enabled from DSM\n{2}-{1} Filter: Enabled from Network Driver\n{0}".format(
                                                                                    self.header, ip, self.ip_type[ip]))
            elif action == "rule":
                dsm.connect()
                identifier = dsm.apply_rule(scenario_name, rule_list=grule_list)
                print("\n# {} Rule Applied \n".format(grule_list))
                print("{0}{0}\n# {1} Rule Applied \n{0}{0}".format(self.header, identifier))
            
            # Actual measurement
            all_stats = self.run_band_test(suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name)
            iter_stats = all_stats[:self.best_iteration]
            avg = round(sum(map(float, iter_stats)) / len(iter_stats), 2)
            print("{0}{0}\n- {1} iteration stats {2} MBps\n- Average Bandwidth: {3} MBps\n{0}{0}\n".format(self.header,
                                                                                len(iter_stats), iter_stats, avg))
            return all_stats, iter_stats, avg
        except Exception as e:
            print(f"Error in apply_rule_get_stats: {e}")
            return None, None, None

    def jfrog_upload(self, jfrog_base_url, auth):
        try:
            uploaded_files = []
            print("Current working directory:", os.getcwd())
            print("All files in directory:", os.listdir())
            for file in os.listdir("/tmp"):
                if file.endswith(".html") or file.endswith(".png") or file.endswith(".json"):
                    #filename = "{}_{}_{}".format(scenario.replace(" ", "_"), rule_ids, file)
                    jfrog_url = "{}/{}".format(jfrog_base_url, file)
                    print("Uploading file:", file)
                    print("Target JFrog URL:", jfrog_url)
                    for retry in range(2):
                        print("Attempt-{} to upload {} to {}".format(retry + 1, file, jfrog_url))
                        #file_path = os.path.join("/tmp", file)
                        with open(file, "rb") as fout:
                            res = requests.put(jfrog_url, data=fout.read(), auth=auth)
                            print("jfrog_upload status: {}".format(res.status_code))
                            if res.status_code == 201:
                                print("PASS: {} file has been uploaded to JFrog Repo {}".format(file, jfrog_url))
                                uploaded_files.append(jfrog_url)
                                break
                        time.sleep(10)
                    else:
                        raise Exception("ERROR: Failed to upload {} to JFrog Repo {}".format(file, jfrog_url))
            return uploaded_files
        except Exception as e:
            print(f"Error in jfrog_upload: {e}")
            return []

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Please give argument to perform operations')
        parser.add_argument('--access_key', type=str, help="Need access key to get the password of instance")
        parser.add_argument('--secret_key', type=str, help="Need secret key to get the password of instance")
        parser.add_argument('--manifest_file', type=str, help="Need infra credential of dsm and dsa")
        parser.add_argument('--dsm_version', type=str, help="Need dsm version to decide the policy template")
        parser.add_argument('--stats', type=str, help="Html file name")
        parser.add_argument('--graph', type=str, help="Graph file name")
        parser.add_argument('--path', type=str, help="Graph file name")
        parser.add_argument('--jfrog_url', type=str, help="JFrog URL")
        parser.add_argument('--jfrog_token', type=str, help="JFrog Token")
        parser.add_argument('--scenario', type=str, help="Scenario name to test")
        parser.add_argument('--rule_id', type=str, help="Rule Id's to be tested")
        parser.add_argument('--individual_rule_test', type=str, help="individual_rule_test")
        args = parser.parse_args()

        with open(args.manifest_file) as fout:
            machine_info = json.load(fout)
        if args.rule_id:
            rule_file = args.rule_id
        scenario = PerformanceScenario(machine_info,
                                       args.dsm_version,
                                       args.access_key, args.secret_key,
                                       args.stats, args.graph, args.path,
                                       args.jfrog_token,
                                       args.scenario,
                                       rule_file, args.individual_rule_test
                                       )
        auth = BearerAuth(args.jfrog_token)
        if args.rule_id != "":
            rule_ids = args.rule_id
        elif args.rule_id == "":
            rule_file = os.path.join("update-info", "rule-identifiers.txt")
            with open(rule_file, "r") as f:
                rule_ids = f.read().strip().split(",")

        print(f"Rule Id's Perform_scenario: {rule_ids}")

        stats_url = scenario.jfrog_upload(args.jfrog_url, auth)
        graph_url = scenario.jfrog_upload(args.jfrog_url, auth)
        destination = "{}_{}".format(args.scenario.replace(" ", "_"), args.manifest_file)
        shutil.copyfile(args.manifest_file, destination)
        manifest_url = scenario.jfrog_upload(args.jfrog_url, auth)
    except Exception as e:
        print(f"Error in main: {e}")