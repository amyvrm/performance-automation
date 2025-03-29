class MachineInfo(object):
    def __init__(self, machine_info):
        self.machine_info = machine_info

        self.windows_ids = {
            key: value["value"] for key, value in machine_info.items() if key.startswith("dsa-windows-id")
        }

        # Dynamically extract all Windows Agent instance IDs
        self.windows_agent_ids = {
            key: value["value"] for key, value in machine_info.items() if key.startswith("dsa-windows_agent-id")
        }

        self.dsm_ids = {
            key: value["value"] for key, value in machine_info.items() if key.startswith("dsm-rhel_id")
        }
        
        self.dsm_private_ips = {
            key: value["value"] for key, value in machine_info.items() if key.startswith("dsm-private-ip")
        }

        self.dsm_public_ips = {
            key: value["value"] for key, value in machine_info.items() if key.startswith("dsm-public-ip")
        }

    def get_instance_one_user(self):
        return self.machine_info["dsa-user"]["value"]

    def get_instance_two_user(self):
        return self.machine_info["dsa-user-2"]["value"]

    def get_pkg_path(self):
        return self.machine_info["pkg-path"]["value"]

    def get_dsm_public_ip(self):
        return self.machine_info["dsm-public-ip"]["value"]

    def get_dsm_private_ip(self):
        return self.machine_info["dsm-private-ip"]["value"]

    def get_dsm_user(self):
        return self.machine_info["dsm-login-user"]["value"]

    def get_dsm_pwd(self):
        return self.machine_info["dsm-login-password"]["value"]

    def get_instance_one_id(self):
        return self.machine_info["dsa-windows-id"]["value"]

    def get_instance_two_id(self):
        return self.machine_info["dsa-windows-id-2"]["value"]
    
    def get_instance_one_id_one(self):
        return self.machine_info["dsa-windows-agent-id-2"]["value"]

    def get_instance_two_id_two(self):
        return self.machine_info["dsa-windows-id-2-2"]["value"]

    def get_region(self):
        return self.machine_info["region"]["value"]

    def get_pem_file(self):
        return self.machine_info["pem-file"]["value"]
    
    def get_all_windows_instance_ids(self):
        """ Returns all dynamically found Windows instance IDs """
        return self.windows_ids

    def get_all_windows_agent_ids(self):
        """ Returns all dynamically found Windows Agent instance IDs """
        return self.windows_agent_ids
    
    def get_all_dsm_instance_ids(self):
        """ Returns all dynamically found DSM instance IDs """
        return self.dsm_ids
    
    def get_dsm_private_ips(self):
        return self.dsm_private_ips
    
    def get_dsm_public_ips(self):
        return self.dsm_public_ips