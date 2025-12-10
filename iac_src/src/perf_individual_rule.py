from perform_scenario import PerformanceScenario
from perf_common import PerfCommon
from dsm_operation import DsmPolicy
import pandas as pd
import time

class PerfIndividualRule(PerfCommon, DsmPolicy):
    def __init__(self, dsm, scenario, path_json, grule, identifiers, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, summary, stats, graph, s_adap_name, c_adap_name, title, ip_type, path, best_iteration):
        PerfCommon.__init__(self, stats, graph)
        self.dsm = dsm
        self.path_json = path_json
        self.grule = grule
        self.identifiers = identifiers
        self.suser = suser
        self.sip = sip
        self.spwd = spwd
        self.s_priv_ip = s_priv_ip
        self.cuser = cuser
        self.cip = cip
        self.cpwd = cpwd
        self.c_priv_ip = c_priv_ip
        self.scenario = scenario
        self.summary = summary
        self.s_adap_name = s_adap_name
        self.c_adap_name = c_adap_name
        self.title = title
        self.ip_type = ip_type
        self.path = path
        self.best_iteration = best_iteration
        self.perf_rule()

    def perf_rule(self):
        print(f"### Perf Rule Individual perf_rule### {self.identifiers}")
        print("Identifiers: {}".format(self.identifiers))
        self.identifiers = [self.identifiers]
        grule_list, server_rules, client_rules = PerfCommon.get_dependency_portlist(self, self.path_json, self.grule, self.identifiers)
        print(f"grule_list Individual: {grule_list} | server_rules Individual: {server_rules} | client_rules Individual: {client_rules}")
        #self.dsm.upload_basic_policy(change_policy=True)
        print(f"grule_list Individual: {grule_list} | server_rules Individual: {server_rules}")
        print(f"Server rules Individual: {server_rules} | Client Rules Individual: {client_rules}")
        print(f"sip: {self.sip} | cip: {self.cip} | s_priv_ip: {self.s_priv_ip} | c_priv_ip: {self.c_priv_ip} | s_adap_name: {self.s_adap_name} | c_adap_name: {self.c_adap_name} | ip_type: {self.ip_type}")
        self.filtered_rules = self.get_filtered_rules(server_rules, client_rules)
        if self.scenario in ["Server_Upload", "All"]:
            self.perf_scenario_test_individual("Server Upload", server_rules, client_rules, grule_list)
        if self.scenario in ["Server_Download", "All"]:
            if self.scenario == "All":
                self.clean_and_enable_agents()
            self.perf_scenario_test_reverse_individual("Server Download", server_rules, client_rules, grule_list)
        if self.scenario in ["Client_Download", "All"]:
            if self.scenario == "All":
                self.clean_and_enable_agents()
            self.perf_scenario_test_individual("Client Download", server_rules, client_rules, grule_list)

    def get_filtered_rules(self, server_rules, client_rules):
        print(f"### Perf Rule Individual get_filtered_rules### {self.identifiers}")
        print(f"self.summary: {self.summary}")
        # Ensure self.summary is a string, handle None values
        if self.summary is None:
            print("⚠️  Warning: summary is None, returning default")
            return "Server Rules: None\nClient Rules: None"
        
        summary_text = self.summary[0] if isinstance(self.summary, tuple) else self.summary
        
        # Validate summary_text is not None and is a string
        if summary_text is None:
            print("⚠️  Warning: summary_text is None, returning default")
            return "Server Rules: None\nClient Rules: None"
        
        summary_text = str(summary_text)  # Ensure it's a string

        filtered_rules = "Server Rules:\n" + "\n".join(
            line for line in summary_text.split("\n") if any(rule_id.strip() in line for rule_id in server_rules)
        ) if server_rules else "Server Rules: None"
        filtered_rules += "\nClient Rules:\n" + "\n".join(
            line for line in summary_text.split("\n") if any(rule_id.strip() in line for rule_id in client_rules)
        ) if client_rules else "\nClient Rules: None"
        print(f"filtered rules: {filtered_rules}")
        return filtered_rules

    def clean_and_enable_agents(self):
        print("### Perf Rule Individual clean_and_enable_agents###")
        self.dsm.clean_rules_from_dsm()
        # Enable both server and client agents when running "All" scenario
        self.activate_dsa(self.sip, self.suser, self.spwd)
        self.activate_dsa(self.cip, self.cuser, self.cpwd)
        # Enable filters in parallel
        machines_to_enable = [
            {'ip': self.sip, 'user': self.suser, 'pwd': self.spwd, 'adaptor_name': self.s_adap_name},
            {'ip': self.cip, 'user': self.cuser, 'pwd': self.cpwd, 'adaptor_name': self.c_adap_name}
        ]
        self.enable_filters_parallel(machines_to_enable)
        print("→ Waiting 5s for agent/filter stabilization...")
        time.sleep(5)

    def perf_scenario_test_individual(self, scenario_name, server_rules, client_rules, grule_list):
        print(f"### Perf Rule Individual perf_scenario_test_individual### {self.identifiers}")

        print("{0}\n### {1} ###\n{0}".format("#" * 50, scenario_name))
        
        # System warm-up: eliminate cold-start bias (DNS, ARP, TCP window, routing cache)
        print(f"{self.header}\n→ Running lightweight warm-up (3 iterations) to eliminate cold-start effects...\n{self.header}")
        warmup_stats = PerformanceScenario.run_warmup_test(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, scenario_name)
        print(f"✓ Warm-up complete: System caches primed (DNS/ARP/TCP)")
        print(f"→ All subsequent measurements will use warm system state\n")
        
        if scenario_name == "Client Download":
            # Run With Filter first for Client Download to isolate cache bias from affecting baseline
            print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
            w_filter_all_stats, w_filter_stats, wf_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="filter", dsm=self.dsm)
            print("- With Filter Driver Average Stats: {} MBps\n".format(wf_avg))

            print("→ Cooldown: Waiting 20s to clear CPU/network caches before baseline...")
            time.sleep(20)

            print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
            wo_filter_all_stats, wo_filter_stats, wof_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="wo_filter", dsm=self.dsm)
            print("- Without Filter Driver Average Stats: {} MBps\n".format(wof_avg))
        else:
            # Default order for other scenarios
            print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
            wo_filter_all_stats, wo_filter_stats, wof_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="wo_filter", dsm=self.dsm)
            print("- Without Filter Driver Average Stats: {} MBps\n".format(wof_avg))

            print("→ Cooldown: Waiting 15s to clear CPU/network caches before next test...")
            time.sleep(15)

            print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
            w_filter_all_stats, w_filter_stats, wf_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="filter", dsm=self.dsm)
            print("- With Filter Driver Average Stats: {} MBps\n".format(wf_avg))


        print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        rulelist_stats, iter_rulelist, rulelist_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip,
            grule_list, scenario_name, self.s_adap_name, self.c_adap_name, action="rule", dsm=self.dsm
        )
        print(f"iter_rulelist: {iter_rulelist} | rulelist_avg: {rulelist_avg}")

        print("- Threshold Rule with Dependency: {} MBps\n".format(rulelist_avg))
        rule_stats, iter_rule, rule_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip,
            False, scenario_name, self.s_adap_name, self.c_adap_name, action="rule", dsm=self.dsm
        )
        print(f"iter_rule: {iter_rule} | rule_avg: {rule_avg}")
        print("- Rule with Dependency Average stats: {} MBps\n".format(rule_avg))

        wo_filter_stats.append(wof_avg)
        w_filter_stats.append(wf_avg)
        iter_rulelist.append(rulelist_avg)
        iter_rule.append(rule_avg)

        print("- Best Case Rule: {}\n- All Server Rule: {}".format(iter_rulelist, iter_rule))
        self.create_report(scenario_name, wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule, rulelist_avg, rule_avg, server_rules, client_rules, wof_avg, wf_avg)

    def perf_scenario_test_reverse_individual(self, scenario_name, server_rules, client_rules, grule_list):
        print(f"### Perf Rule Individual perf_scenario_test_reverse_individual### {self.identifiers}")
        print("{0}\n### {1} ###\n{0}".format("#" * 50, scenario_name))
        
        # System warm-up: eliminate cold-start bias (DNS, ARP, TCP window, routing cache)
        print(f"{self.header}\n→ Running lightweight warm-up (3 iterations) to eliminate cold-start effects...\n{self.header}")
        warmup_stats = PerformanceScenario.run_warmup_test(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, scenario_name)
        print(f"✓ Warm-up complete: System caches primed (DNS/ARP/TCP)")
        print(f"→ All subsequent measurements will use warm system state\n")
        
        # Without Filter Driver (run FIRST for Server Download to avoid warm-up bias)
        print("{0}{0}\n# Without Filter Driver #\n{0}{0}".format(self.header))
        wo_filter_all_stats, wo_filter_stats, wof_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="wo_filter", dsm=self.dsm)
        print("- Without Filter Driver Average Stats: {} MBps\n".format(wof_avg))

        # With Filter Driver
        print("{0}{0}\n# With Filter Driver #\n{0}{0}".format(self.header))
        w_filter_all_stats, w_filter_stats, wf_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, False, scenario_name, self.s_adap_name, self.c_adap_name, action="filter", dsm=self.dsm)
        print("- With Filter Driver Average Stats: {} MBps\n".format(wf_avg))
        
        # Best Case Rule (run after filter tests)
        print("{0}{0}\n# Threshold Rule with Dependency #\n{0}{0}".format(self.header))
        rulelist_stats, iter_rulelist, rulelist_avg = PerformanceScenario.apply_rule_get_stats(self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip, grule_list, scenario_name, self.s_adap_name, self.c_adap_name, action="rule", dsm=self.dsm
        )
        print(f"iter_rulelist: {iter_rulelist} | rulelist_avg: {rulelist_avg}")
        print("- Threshold Rule with Dependency: {} MBps\n".format(rulelist_avg))

        # All Rules
        print("{0}{0}\n# All Rules #\n{0}{0}".format(self.header))
        rule_stats, iter_rule, rule_avg = PerformanceScenario.apply_rule_get_stats(
            self, self.suser, self.sip, self.spwd, self.s_priv_ip, self.cuser, self.cip, self.cpwd, self.c_priv_ip,
            False, scenario_name, self.s_adap_name, self.c_adap_name, action="rule", dsm=self.dsm
        )
        print(f"iter_rule: {iter_rule} | rule_avg: {rule_avg}")
        print("- Rule with Dependency Average stats: {} MBps\n".format(rule_avg))

        wo_filter_stats.append(wof_avg)
        w_filter_stats.append(wf_avg)
        iter_rulelist.append(rulelist_avg)
        iter_rule.append(rule_avg)

        print("- Best Case Rule: {}\n- All Server Rule: {}".format(iter_rulelist, iter_rule))
        self.create_report(scenario_name, wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule, rulelist_avg, rule_avg, server_rules, client_rules, wof_avg, wf_avg)

    def create_report(self, scenario_name, wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule, rulelist_avg, rule_avg, server_rules, client_rules, wof_avg, wf_avg):
        print(f"### Perf Rule Individual create_report### {self.identifiers}")
        self.col = ['Without Filter Driver', 'With Filter Driver + No Rule', 'Best Case Rule']
        if scenario_name in ["Server Upload", "Server Download"]:
            self.col.append('Server Rules (No. of Rules: {} Ids: {})'.format(len(server_rules), server_rules))
            print(f"Server Rules (No. of Rules: {len(server_rules)} Ids: {server_rules}")
        elif scenario_name == "Client Download":
            self.col.append('Client Rules (No. of Rules: {} Ids: {})'.format(len(client_rules), client_rules))
            print(f"Client Rules (No. of Rules: {len(client_rules)} Ids: {client_rules}")
        print(f"columns: {self.title}")
        print(f"index: {self.col}")
        print(f"iter_rulelist, iter_rule: {[iter_rulelist, iter_rule]}")
        print(f"wo_filter_stats, w_filter_stats: {[wo_filter_stats, w_filter_stats]}")
        df = pd.DataFrame([wo_filter_stats, w_filter_stats, iter_rulelist, iter_rule], index=self.col, columns=self.title)
        print(f"DF: {df}")
        print(f"Scenario_name: {scenario_name}")
        print(f"filtered_rules: {self.filtered_rules}")
        PerfCommon.create_html_table(self, df, scenario_name, self.filtered_rules)
        PerfCommon.create_bar_chart(self, [wof_avg, wf_avg, rulelist_avg, rule_avg], scenario_name, str(self.identifiers))