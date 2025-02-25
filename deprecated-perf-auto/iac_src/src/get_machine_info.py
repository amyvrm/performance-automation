


class MachineInfo(object):
    def __init__(self, machine_info):
        self.machine_info = machine_info

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

    def get_region(self):
        return self.machine_info["region"]["value"]

    def get_pem_file(self):
        return self.machine_info["pem-file"]["value"]