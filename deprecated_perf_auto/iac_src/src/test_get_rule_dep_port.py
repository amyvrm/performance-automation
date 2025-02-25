import json
import os


class GetDepPort(object):
    def get_dependency_portlist(self, path, grule):
        server_rules = []
        non_dpi_rules = []
        all_dep_rules = set()
        portlist_set = set()
        grule_list = [grule]
        rule_file = os.path.join("update-info", "rule-identifiers.txt")
        portlist_file = os.path.join("update-info", "port_list.txt")

        # with open(os.path.join("update-info", "rule-identifiers.txt"), "r") as f:
        #     all_identifier = f.read().split(",")
        all_identifier = ['1010594', '1010433', '1009766', '1010579', '1010604', '1010605', '1010575', '1006546', '1010606', '1010364',
         '1010365', '1010334', '1010592', '1010593', '1010564', '1010599', '1010600', '1010603', '1010601', '1010602',
         '1010099', '1010562', '1010580', '1010598', '1010590', '1003987', '1008852', '1010465', '1010489', '1010528',
         '1010536', '1010558', '1010582']
        print("Rules: {}".format(all_identifier))

        json_file = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        print("Json File: {}".format(json_file))
        with open(os.path.join(path, json_file[0]), "r") as fout:
            self.src_pkg_json = json.load(fout)

        # Get all server Rule with dependency and portlist
        for identifier in all_identifier:
            rule = self.check_dpi_server_rule(identifier)
            if rule:
                if self.check_server_rule(rule):
                    server_rules.append(identifier)
                    if rule["RequiresTBUIDs"]:
                        dep_rule = self.get_depend_rule(rule)
                        all_dep_rules.add(dep_rule["Identifier"])
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
        print("Good Rule with Dependency: {}\nNon DPI Rule: {}\n".format(grule_list, non_dpi_rules))
        print("\nPortList: {}\n\n{}".format(port_list, "*"*100))
        if len(all_dep_rules) > 0:
            server_rules.extend(list(all_dep_rules))
        server_rules.extend(non_dpi_rules)
        os.remove(rule_file)
        with open(rule_file, "w") as f:
            f.write(",".join(server_rules))
        with open(portlist_file, "w") as f:
            json.dump(port_list, f)

        return grule_list, identifiers

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
                    return True
                else:
                    return False

if __name__ == '__main__':
    dep_port = GetDepPort()
    dep_port.get_dependency_portlist('update-packages', "1006436")