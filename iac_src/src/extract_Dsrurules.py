import argparse
import os
import shutil
from perf_common import PerfCommon

class extract_Dsrurules(PerfCommon): 
    def __init__(self, stats, graph, path_json, scenario, identifiers):
        PerfCommon.__init__(self, stats, graph)
        self.scenario = scenario
        self.path_json = path_json
        self.identifiers = identifiers
        self.grule = "1005366" if scenario == "Client_Download" else "1006436"

        if not os.path.exists("update-info"):
            os.makedirs("update-info")

    def get_rules_length(self):
        identifiers = self.identifiers.strip('[]').replace("'", "").split(',')
        identifiers = [identifier.strip() for identifier in identifiers]

        grule_list, server_rule, client_rules = PerfCommon.get_dependency_portlist(self, self.path_json, self.grule, identifiers)
        shutil.rmtree("update-info")
        
        # Print the server and client rules counts in a specific format
        print(f"server_rules={len(server_rule)}")
        print(f"client_rules={len(client_rules)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--stats', type=str, help="Html file name")
    parser.add_argument('--graph', type=str, help="Graph file name")
    parser.add_argument('--path', type=str, help="DSRU file path")
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    parser.add_argument('--identifiers', type=str, help="All Rules")
    args = parser.parse_args()

    extractor = extract_Dsrurules(args.stats, args.graph, args.path, args.scenario, args.identifiers)
    extractor.get_rules_length()