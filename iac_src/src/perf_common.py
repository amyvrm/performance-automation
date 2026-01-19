import rsa
import boto.ec2
import base64
from pypsexec.client import Client
from pypsexec.exceptions import SCMRException
import simplejson as json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import seaborn as sns
import numpy as np
import time
from backoff_utils import wait_for_nginx_ready
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
        # Adapter name cache
        self._adapter_cache = {}  # {ip: adapter_name}
        self._adapter_cache_ttl = 3600  # Cache for 1 hour
        self._adapter_cache_timestamp = {}  # {ip: timestamp}

    def create_html_table(self, df, scenario_name, filtered_rules):
        fname = "{}_{}".format(scenario_name.replace(" ", "_"), self.stats)
        print(f"fname: {fname}")
        
        # Check if file exists
        if not os.path.exists(fname):
            with open(fname, "w") as fin:
                fin.write(self.create_html_header())
                fin.write('\n<title>Performance Report</title>\n')
                fin.write('<h2 style="text-align: center; padding: 10px;">Scenario Name: {}</h2>'.format(scenario_name))
                fin.write('<div class="container">\n')
    
        # Read existing content (avoiding memory overload)
        with open(fname, "r") as fin:
            content = fin.read()
            print(f"Content: {content}")

        # Ensure the closing tags exist for proper replacement
        if "</body>" not in content or "</html>" not in content:
            content += "</div>\n</body>\n</html>\n"

        # Remove the closing tags to append new content correctly
        content = content.replace("</body>\n</html>\n", "")

        # Append the new content
        with open(fname, "w") as fout:
            fout.write(content)
            fout.write('<div class="row">\n')
            fout.write(df.to_html(classes="table table-striped", justify="center", border=1))
            fout.write("</div>\n")
            fout.write('<h4 style="padding: 10px;">Performance Tested Rules:</h4>\n')
            fout.write("<div><pre>{}</pre></div>\n".format(filtered_rules.strip()))
            fout.write("</div>\n</body>\n</html>\n")
        
         # Read existing content (avoiding memory overload)
        with open(fname, "r") as fin:
            content = fin.read()
            print(f"Content: {content}")

    def create_bar_chart(self, avg, scenario_name, identifier):
        rule_msg = "Client Rules" if scenario_name == "Client Download" else "Server Rules"
        scenario_sort = ["Without FD", "With FD", "Best Case Rule", rule_msg]

        ind = np.arange(0, len(avg))
        df = pd.DataFrame()
        df["ind"] = ind
        df["avg"] = avg
        df["sce_sort"] = scenario_sort

        # specify the colors
        colors = sns.color_palette('pastel', n_colors=len(df))
        plt.figure(figsize=(16, 10))
        sns.set_style('ticks')
        ax = sns.barplot(data=df, x="sce_sort", y="avg", hue="sce_sort", palette=colors, legend=False)
        for index, row in df.iterrows():
            ax.text(row.ind, row.avg, row.avg, color='black', ha="center", fontsize=16)

        ax.set_xlabel("Scenario", fontsize=16, alpha=0.8)
        ax.set_ylabel("Throughput (MBps)", fontsize=16, alpha=0.8)
        ax.set_title(scenario_name, fontsize=18)
        ax.set_xticklabels(scenario_sort, fontsize=14)

        # map names to colors
        cmap = dict(zip(self.col, colors))
        # create the rectangles for the legend
        patches = [Patch(color=v, label=k) for k, v in cmap.items()]
        # add the legend
        lgd = plt.legend(title='Scenario Stats', handles=patches, bbox_to_anchor=(0.5, -0.1))
        text = ax.text(-0.2, 1.05, "Scenario Name: {}".format(scenario_name), transform=ax.transAxes)
        ax.grid('on')
        sns.despine()
        # plt.show()
        fname = "{}_{}_{}".format(scenario_name.replace(" ", "_"), str(identifier), self.graph)
        print(f"fname_image: {fname}")
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
        print("c_priv_ip: {}".format(c_priv_ip))
        print("s_priv_ip: {}".format(s_priv_ip))
        if scenario_name == "Server Download" or scenario_name == "Client Download":
            # Run Nginx
            self.run_nginx(sip, suser, spwd)
            print("Probing nginx readiness with adaptive wait...")
            probe_result = wait_for_nginx_ready(s_priv_ip)
            print(f"Nginx readiness probe: attempts={probe_result['attempts']}, avg_latency_ms={probe_result['avg_latency_ms']:.2f}, avg_ttfb_ms={probe_result['avg_ttfb_ms']:.2f}")
            # Run Apache Bench
            #through_put = self.run_ab(cip, cuser, cpwd, s_priv_ip)
            through_put = self.run_hey(cip, cuser, cpwd, s_priv_ip)
            print("Through put: {}".format(through_put))
            self.clean_nginx(sip, suser, spwd)
            self.clean_ab(cip, cuser, cpwd)

            for retry in range(2):
                if len(through_put) == 20:
                    return through_put
                else:
                    print("Exception: Attempt-{} to get the stats...Found stats=[{}]".format(retry, through_put))
                    # Run Nginx
                    self.run_nginx(sip, suser, spwd)
                    print("Probing nginx readiness with adaptive wait...")
                    probe_result = wait_for_nginx_ready(s_priv_ip)
                    print(f"Nginx readiness probe: attempts={probe_result['attempts']}, avg_latency_ms={probe_result['avg_latency_ms']:.2f}, avg_ttfb_ms={probe_result['avg_ttfb_ms']:.2f}")
                    # Run Apache Bench
                    #through_put = self.run_ab(cip, cuser, cpwd, s_priv_ip)
                    through_put = self.run_hey(cip, cuser, cpwd, s_priv_ip)
                    print("Through put: {}".format(through_put))
                    self.clean_nginx(sip, suser, spwd)
                    #self.clean_ab(cip, cuser, cpwd)
        elif scenario_name == "Server Upload":
            # receiver
            pid = self.run_pcattcp_rec(sip, suser, spwd, c_priv_ip, asynchronous=True)
            print("Waiting 3 min, to flow the traffic (with health checks every 30s)...")
            
            # Wait with periodic health checks instead of blind sleep
            for check_interval in range(6):  # 6 x 30s = 180s
                time.sleep(30)
                # Quick connectivity check to both machines
                try:
                    print(f"  [{(check_interval + 1) * 30}s] Health check: verifying instances are still reachable...")
                    
                    # Check server (receiver)
                    test_srv = Client(sip, username=suser, password=spwd, encrypt=False)
                    test_srv.connect(timeout=10)
                    test_srv.disconnect()
                    
                    # Check client (transmitter)
                    test_cli = Client(cip, username=cuser, password=cpwd, encrypt=False)
                    test_cli.connect(timeout=10)
                    test_cli.disconnect()
                    
                    print(f"  ✓ Both instances responsive")
                except Exception as health_err:
                    print(f"  ⚠️  WARNING: Health check failed - {health_err}")
                    print(f"     Instance may have rebooted! This test iteration may fail.")
            
            # transmitter
            through_put = self.run_pcattcp_tran(cip, cuser, cpwd, s_priv_ip, bandwidth=True)
            print("Through put: {}".format(through_put))
            self.clean(cip, cuser, cpwd, pid=pid)
            self.clean(sip, suser, spwd)

            for retry in range(2):
                if len(through_put) == 10:
                    return through_put
                else:
                    print("Exception: Attempt-{} to get the stats...Found stats=[{}]".format(retry, through_put))
                    # receiver
                    pid = self.run_pcattcp_rec(sip, suser, spwd, c_priv_ip, asynchronous=True)
                    print("Waiting 3 min, to flow the traffic (with health checks every 30s)...")
                    
                    # Wait with periodic health checks instead of blind sleep
                    for check_interval in range(6):  # 6 x 30s = 180s
                        time.sleep(30)
                        try:
                            print(f"  [{(check_interval + 1) * 30}s] Health check: verifying instances...")
                            
                            test_srv = Client(sip, username=suser, password=spwd, encrypt=False)
                            test_srv.connect(timeout=10)
                            test_srv.disconnect()
                            
                            test_cli = Client(cip, username=cuser, password=cpwd, encrypt=False)
                            test_cli.connect(timeout=10)
                            test_cli.disconnect()
                            
                            print(f"  ✓ Both instances responsive")
                        except Exception as health_err:
                            print(f"  ⚠️  WARNING: Health check failed - {health_err}")
                    
                    # transmitter
                    through_put = self.run_pcattcp_tran(cip, cuser, cpwd, s_priv_ip, bandwidth=True)
                    print("Through put: {}".format(through_put))
                    self.clean(cip, cuser, cpwd, pid=pid)
                    self.clean(sip, suser, spwd)

        raise Exception("Exception!!! Nginx access might be blocked, please check and try again")

    def execute_cmd(self, cmd, ip, user, pwd, tool="Powershell.exe", iteration=10, bandwidth=False, asynchronous=False):
        # Configure connection timeout (30s instead of default ~90s)
        machine = Client(ip, username=user, password=pwd, encrypt=False)
        
        try:
            machine.connect(timeout=30)  # Add explicit timeout
        except Exception as conn_err:
            print(f"⚠️  Failed to connect to {ip}: {conn_err}")
            # If connection fails during cleanup phase, log and return gracefully
            if "timed out" in str(conn_err) or "refused" in str(conn_err):
                print(f"→ Host {ip} may be shutting down or unreachable")
                return None
            raise
        
        try:
            machine.create_service()
            print("# IP: {}, Tool: {}, Command: {} #".format(ip, tool, cmd))
            if tool == "Powershell.exe":
                if bandwidth:
                    print("- Taking Bandwidth Reading...")
                    all_through_put = []
                    for i in range(iteration):
                        try:
                            stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                            PerfCommon.get_bandwidth(cmd, stdout, stderr, all_through_put, i)
                            time.sleep(5)  # OPTIMIZATION: Reduced from 30s to 5s (sufficient for connection/system cool-down)
                        except SCMRException as exc:
                            if "STATUS_SHARING_VIOLATION" in str(exc):
                                print(f"Retrying due to sharing violation: {exc}")
                                time.sleep(10)  # Wait before retrying
                                continue
                            else:
                                raise
                    all_through_put.sort(reverse=True)
                    return all_through_put
                else:
                    stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                    print("Tool: {}, Output: [{}], Error: {}".format(tool, stdout, stderr))
                    if stdout:
                        value = stdout.decode("utf-8").split("\r")[0]
                        print("Value = {}".format(value))
                        return value
            else:
                stdout, stderr, rc = machine.run_executable(tool, arguments=cmd, asynchronous=asynchronous)
                print("{} Output: [{}], pid: {}, Error: {}".format(tool, stdout, rc, stderr))
                value = rc
                print("Value = {}".format(value))
                return value
        except Exception as e:
            print("Error!!! {} while accessing {}".format(e, ip))
        finally:
            try:
                machine.cleanup()
                machine.remove_service()
            except SCMRException as exc:
                if exc.return_code == 1072:  # ERROR_SERVICE_MARKED_FOR_DELETE
                    print(f"⚠️  Service marked for delete on {ip} (expected during cleanup)")
                elif exc.return_code == 1115:  # ERROR_SHUTDOWN_IN_PROGRESS
                    print(f"⚠️  System shutdown in progress on {ip} (cleanup will be handled by OS)")
                else:
                    print(f"⚠️  Failed to remove service on {ip}: {exc} (code: {exc.return_code})")
            except Exception as e:
                print(f"⚠️  Cleanup exception on {ip}: {e}")
            finally:
                try:
                    machine.disconnect()
                except Exception as disc_err:
                    print(f"⚠️  Disconnect failed for {ip}: {disc_err} (non-critical)")

    @staticmethod
    def get_bandwidth(cmd, stdout, stderr, all_through_put, index):
        try:
            if "PCATTCP" in cmd:
                if stderr:
                    out = stderr.decode("utf-8")
                    for line in out.split("\r\n"):
                        print(line)
                    through_put = out.split("=")[1].split(" ")[-8]
                    t_mbps = round(float(through_put) / 1024.0, 2)
                    print("{0}\n+ {1}: {2} KBps, {3} MBps +\n{0}".format("+" * 50, index + 1, through_put, t_mbps))
                    all_through_put.append(t_mbps)
                    return True
            elif "ab" in cmd:
                if stdout:
                    out = stdout.decode("utf-8")
                    for line in out.split("\r\n"):
                        print(line)
                    for line in out.split("\r\n"):
                        if "Transfer rate" in line:
                            through_put = re.findall("\d+\.\d+", line)[0]
                            t_mbps = round(float(through_put) / 1024.0, 2)
                            print("{0}\n+ {1}: {2} KBps, {3} MBps +\n{0}".format("+" * 50, index + 1, through_put, t_mbps))
                            all_through_put.append(t_mbps)
                            return True
            elif "hey" in cmd:
                if stdout:
                    out = stdout.decode("utf-8")
                    time = "time"
                    size = "size"
                    for line in out.split("\n"):
                        print(line)
                        if "Total:" in line:
                            time = re.findall("\d+\.\d+", line)[0]
                        elif "Total data:" in line:
                            size = re.findall("\d+", line)[0]
                    if time != "time" and size != "size":
                        through_put = round(float(size) / float(time) / 1024.0, 2)
                        t_mbps = round(float(size) / float(time) / 1024.0 / 1024.0, 2)
                        print("{0}\n+ {1}: {2} KBps, {3} MBps +\n{0}".format("+" * 50, index + 1, through_put, t_mbps))
                        all_through_put.append(t_mbps)
                        return True
        except Exception as ex:
            print("Exception: {}".format(ex))
            return False
        return False

    @staticmethod
    def get_pwd(region, access_key, secret_key, instance_id, pem_file_loc, mtype):

        print("- get_pwd")
    
        # Connect to EC2
        ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    
        # Fetch instance details
        instances = ec2_conn.get_only_instances(instance_ids=[instance_id])
        if not instances:
            raise Exception(f"Instance {instance_id} not found in region {region}")
        
        instance = instances[0]
        print(f"Found instance id: {instance_id}")
        print(f"Private IP: {instance.private_ip_address}")
    
        # Try to get public IP
        try:
            print(f"Public IP: {instance.ip_address}")
        except AttributeError:
            print("Failed to get public IP")
    
        # Get the encrypted password
        password_data = ec2_conn.get_password_data(instance.id).strip()
        if not password_data:
            print("Password is not available yet. Wait at least 4 minutes after instance creation.")
            return "Password not available yet"
    
        # Decrypt password
        try:
            with open(pem_file_loc, 'r') as priv_key_file:
                private_key = rsa.PrivateKey.load_pkcs1(priv_key_file.read())
            decrypted_pwd = rsa.decrypt(base64.b64decode(password_data), private_key).decode("utf-8")
            print(f"* {mtype}-{instance.ip_address} Machine Password: {decrypted_pwd}")
            return decrypted_pwd
        except Exception as e:
            raise Exception(f"Failed to decrypt password: {e}")

    def get_adaptor_name(self, ip, user, pwd, force_refresh=False):
        """
        Get network adapter name with caching.
        Args:
            ip: Target machine IP
            user: Username
            pwd: Password
            force_refresh: Bypass cache and fetch fresh value
        Returns:
            Adapter name string
        """
        # Check cache first
        if not force_refresh and ip in self._adapter_cache:
            cached_time = self._adapter_cache_timestamp.get(ip, 0)
            age = time.time() - cached_time
            if age < self._adapter_cache_ttl:
                print(f"✓ Using cached adapter name for {ip} (age: {age:.0f}s)")
                return self._adapter_cache[ip]
            else:
                print(f"⚠ Cache expired for {ip} (age: {age:.0f}s), refreshing...")
        # Fetch from remote
        print(f"→ Fetching adapter name for {ip} via remote call...")
        tool = "Powershell.exe"
        cmd = "Get-NetAdapter -Name *|select Name|%{$_.Name}"
        name = self.execute_cmd(cmd, ip, user, pwd, tool=tool)
        normalized_name = name.strip()
        self._adapter_cache[ip] = normalized_name
        self._adapter_cache_timestamp[ip] = time.time()
        print(f"✓ Cached adapter name '{normalized_name}' for {ip}")
        return normalized_name

    def clear_adapter_cache(self, ip=None):
        """Clear adapter cache for specific IP or all IPs."""
        if ip:
            self._adapter_cache.pop(ip, None)
            self._adapter_cache_timestamp.pop(ip, None)
            print(f"Cleared adapter cache for {ip}")
        else:
            self._adapter_cache.clear()
            self._adapter_cache_timestamp.clear()
            print("Cleared all adapter cache")

    def _check_dsa_service_present(self, ip, user, pwd):
        """Return tuple(status_bool, message) for DSA service presence."""
        tool = "Powershell.exe"
        ps = (
            "$svc = Get-Service | Where-Object { $_.Name -like '*Deep*Security*Agent*' -or $_.DisplayName -like '*Deep*Security*Agent*' };"
            "if ($null -ne $svc) { Write-Output ('Present:' + $svc.Name) } else { Write-Output 'Absent' }"
        )
        try:
            out = self.execute_cmd(ps, ip, user, pwd, tool=tool)
            if out and out.startswith("Present:"):
                return True, out.replace("Present:", "")
            return False, "DSA service not found"
        except Exception as e:
            return False, f"Error checking DSA: {e}"
    
    def _check_filter_binding_exists(self, ip, user, pwd, adapter_name):
        """Return tuple(status_bool, message) for TM Lightweight Filter binding."""
        if not adapter_name:
            return False, "Adapter name unavailable"
        tool = "Powershell.exe"
        ps = (
            f"$name=\"{adapter_name}\"; $disp=\"Trend Micro LightWeight Filter Driver\";"
            "$binding = Get-NetAdapterBinding -Name $name -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $disp };"
            "if ($binding) { 'Present' } else { 'Absent' }"
        )
        try:
            out = self.execute_cmd(ps, ip, user, pwd, tool=tool)
            return (out == 'Present'), ("Filter binding present" if out == 'Present' else "Filter binding absent")
        except Exception as e:
            return False, f"Error checking filter: {e}"
    
    def print_readiness_report(self, host_label, ip, user, pwd, adapter_name):
        """Print a concise readiness report for a host (DSA + filter only)."""
        dsa_ok, dsa_msg = self._check_dsa_service_present(ip, user, pwd)
        filt_ok, filt_msg = self._check_filter_binding_exists(ip, user, pwd, adapter_name)
        status = (
            f"{host_label} {self.ip_type.get(ip, '')}-{ip} | DSA: {'OK' if dsa_ok else 'Missing'}"
            f" | Filter: {'Present' if filt_ok else 'Absent'}"
        )
        print(status)
        print(f"  Details → Adapter: {adapter_name or 'N/A'} | {dsa_msg} | {filt_msg}")

    def preload_adapter_names(self, machines):
        """
        Preload adapter names for multiple machines in parallel.
        Args:
            machines: List of dicts with keys: ip, user, pwd
        Returns:
            dict mapping ip -> adapter_name
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        print(f"Preloading adapter names for {len(machines)} machines...")
        results = {}
        with ThreadPoolExecutor(max_workers=min(len(machines), 10)) as executor:
            future_to_ip = {
                executor.submit(self.get_adaptor_name, m['ip'], m['user'], m['pwd']): m['ip']
                for m in machines
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    adapter_name = future.result()
                    results[ip] = adapter_name
                    print(f"  ✓ {ip}: {adapter_name}")
                except Exception as e:
                    print(f"  ✗ {ip}: Failed - {e}")
                    results[ip] = None
        return results

    def enable_filter(self, ip, user, pwd, adaptor_name):
        print("{0}\n # {2}-{1} Enable Filter #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        tool = "Powershell.exe"
        # Guard: enable binding only if present
        ps = (
            f"$name=\"{adaptor_name}\"; $disp=\"Trend Micro LightWeight Filter Driver\";"
            "$binding = Get-NetAdapterBinding -Name $name -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $disp };"
            "if ($binding) { Enable-NetAdapterBinding -Name $name -DisplayName $disp -ErrorAction SilentlyContinue; Write-Output 'Filter enabled' }"
            " else { Write-Output 'Filter binding not found' }"
        )
        self.execute_cmd(ps, ip, user, pwd, tool=tool)

    def disable_filter(self, ip, user, pwd, adaptor_name):
        print("{0}\n # {2}-{1} Disable Filter #\n{0}".format("+" * 50, ip, self.ip_type[ip]))
        tool = "Powershell.exe"
        ps = (
            f"$name=\"{adaptor_name}\"; $disp=\"Trend Micro LightWeight Filter Driver\";"
            "$binding = Get-NetAdapterBinding -Name $name -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq $disp };"
            "if ($binding) { Disable-NetAdapterBinding -Name $name -DisplayName $disp -ErrorAction SilentlyContinue; Write-Output 'Filter disabled' }"
            " else { Write-Output 'Filter binding not found' }"
        )
        self.execute_cmd(ps, ip, user, pwd, tool=tool)

    def enable_filters_parallel(self, machines, max_workers=None):
        """
        Enable filter drivers in parallel across multiple machines.
        
        Args:
            machines: List of dicts with keys: ip, user, pwd, adaptor_name
            max_workers: Max parallel workers (default: min(len(machines), 10))
        
        Returns:
            dict mapping ip -> result (True=success, False=failed)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        if not machines:
            print("No machines provided for parallel filter enablement")
            return {}
        
        max_workers = max_workers or min(len(machines), 10)
        print(f"Enabling filters in parallel on {len(machines)} machines (max_workers={max_workers})...")
        
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {
                executor.submit(
                    self.enable_filter,
                    m['ip'], m['user'], m['pwd'], m['adaptor_name']
                ): m['ip']
                for m in machines
            }
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    future.result(timeout=60)
                    results[ip] = True
                    print(f"  ✓ {ip}: Filter enabled")
                except Exception as e:
                    results[ip] = False
                    print(f"  ✗ {ip}: Filter enable failed - {e}")
        
        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        print(f"Filter enablement complete: {success_count}/{len(machines)} successful in {elapsed:.1f}s")
        
        return results

    def disable_filters_parallel(self, machines, max_workers=None):
        """
        Disable filter drivers in parallel across multiple machines.
        
        Args:
            machines: List of dicts with keys: ip, user, pwd, adaptor_name
            max_workers: Max parallel workers (default: min(len(machines), 10))
        
        Returns:
            dict mapping ip -> result (True=success, False=failed)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        if not machines:
            print("No machines provided for parallel filter disablement")
            return {}
        
        max_workers = max_workers or min(len(machines), 10)
        print(f"Disabling filters in parallel on {len(machines)} machines (max_workers={max_workers})...")
        
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {
                executor.submit(
                    self.disable_filter,
                    m['ip'], m['user'], m['pwd'], m['adaptor_name']
                ): m['ip']
                for m in machines
            }
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    future.result(timeout=60)
                    results[ip] = True
                    print(f"  ✓ {ip}: Filter disabled")
                except Exception as e:
                    results[ip] = False
                    print(f"  ✗ {ip}: Filter disable failed - {e}")
        
        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        print(f"Filter disablement complete: {success_count}/{len(machines)} successful in {elapsed:.1f}s")
        
        return results

    def clean(self, ip, user, pwd, pid=False):
        print(f"- clean pid: {pid}")
        tool = 'taskkill.exe'
        cmd = f'/F /PID {pid}' if pid else '/IM PCATTCP.exe /F'
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool)

    def clean_ab(self, ip, user, pwd):
        print(f"- Clean Apache Bench in {self.ip_type[ip]}-{ip}")
        return self.clean(ip, user, pwd, pid=False)

    def clean_nginx(self, ip, user, pwd):
        print(f"- Clean Nginx in {self.ip_type[ip]}-{ip}")
        try:
            return self.clean(ip, user, pwd, pid=False)
        except Exception as e:
            print(f"⚠️  Failed to clean nginx on {ip}: {e}")
            # Check if it's a connection timeout/failure during shutdown
            if "timed out" in str(e) or "Failed to connect" in str(e) or "No route to host" in str(e):
                print(f"→ Host {ip} appears to be shutting down or unreachable (cleanup will be handled by system)")
                return None
            raise

    def run_pcattcp_rec(self, ip, user, pwd, target_ip, asynchronous=False):
        print(f"run_pcattcp_rec: {ip}, {user}, {pwd}, {target_ip}")
        print(f"{'+' * 50}\n+ Run PCATTCP on {self.ip_type[ip]}-{ip} +\n{'+' * 50}")
        self.clean(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = f'{self.path}PCATTCP\\PCATTCP.exe -r -l 490000 {target_ip} -c'
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, asynchronous=asynchronous)

    def run_pcattcp_tran(self, ip, user, pwd, target_ip, bandwidth=False, asynchronous=False):
        print(f"{'+' * 50}\n+ Run PCATTCP on {self.ip_type[ip]}-{ip} and take Reading +\n{'+' * 50}")
        self.clean(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = f'{self.path}PCATTCP\\PCATTCP.exe -t -l 490000 {target_ip}'
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=bandwidth, asynchronous=asynchronous)

    def run_nginx(self, ip, user, pwd):
        print(f"{'+' * 50}\n+ Run nginx on {self.ip_type[ip]}-{ip} +\n{'+' * 50}")
        self.clean_nginx(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = f"cd {self.path}nginx-1.19.2; start {self.path}nginx-1.19.2\\nginx.exe"
        self.execute_cmd(cmd, ip, user, pwd, tool=tool, asynchronous=True)

    def run_ab(self, ip, user, pwd, target_ip):
        print(f"{'+' * 50}\n+ Run Apache Bench {self.ip_type[ip]}-{ip} +\n{'+' * 50}")
        self.clean_ab(ip, user, pwd)
        tool = "Powershell.exe"
        cmd = f"{self.path}ab.exe -c 10 -n 100 http://{target_ip}/test.htm"
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=True)

    def run_hey(self, ip, user, pwd, target_ip, iteration=20):
        print(f"{'+' * 50}\n+ Run Hey.exe {self.ip_type[ip]}-{ip} +\n{'+' * 50}")
        tool = "Powershell.exe"
        # Clean up any existing Hey.exe processes
        self.clean(ip, user, pwd, pid=False)
        cmd = f"{self.path}hey.exe -c 10 -n 100 http://{target_ip}/test.htm"
        return self.execute_cmd(cmd, ip, user, pwd, tool=tool, bandwidth=True, iteration=iteration)
    
    def run_warmup_test(self, suser, sip, spwd, s_priv_ip, cuser, cip, cpwd, c_priv_ip, scenario_name):
        """Lightweight warm-up: 3 iterations to prime DNS/ARP/TCP caches (~1-2 min)"""
        if scenario_name == "Server Download" or scenario_name == "Client Download":
            self.run_nginx(sip, suser, spwd)
            probe_result = wait_for_nginx_ready(s_priv_ip)
            print(f"Nginx warm-up ready: {probe_result['attempts']} attempts")
            # Only 3 iterations for warm-up
            warmup_stats = self.run_hey(cip, cuser, cpwd, s_priv_ip, iteration=3)
            self.clean_nginx(sip, suser, spwd)
            self.clean_ab(cip, cuser, cpwd)
            return warmup_stats
        elif scenario_name == "Server Upload":
            # Quick warm-up for Server Upload: single 30s flow
            pid = self.run_pcattcp_rec(sip, suser, spwd, c_priv_ip, asynchronous=True)
            print("Waiting 30s for warm-up traffic flow...")
            time.sleep(30)  # Minimal warm-up
            self.run_pcattcp_tran(cip, cuser, cpwd, s_priv_ip, bandwidth=False)
            self.clean(cip, cuser, cpwd, pid=pid)
            self.clean(sip, suser, spwd)
            return [0]  # Placeholder
        return []

    def check_test_page(self, ip, user, pwd, target_ip):
        print(f"{'+' * 50}\n+ Check Test Page {self.ip_type[ip]}-{ip} +\n{'+' * 50}")
        tool = "Powershell.exe"
        cmd = f"wget http://{target_ip}/test.htm | % {{$_.StatusCode}}"
        status_code = self.execute_cmd(cmd, ip, user, pwd, tool=tool)
        if status_code != "200":
            raise Exception(f"Test page is not accessible. Status code: {status_code}")

    def disable_dsa(self, ip, user, pwd):
        print(f"{'+' * 50}\n # {self.ip_type[ip]}-{ip} Disable DSA #\n{'+' * 50}")
        tool = "Powershell.exe"
        
        # Check for pending reboots before disabling DSA
        ps_check = (
            "if (Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending') { "
            "Write-Output 'REBOOT_PENDING' } else { Write-Output 'NO_REBOOT' }"
        )
        reboot_status = self.execute_cmd(ps_check, ip, user, pwd, tool=tool)
        if reboot_status and "REBOOT_PENDING" in str(reboot_status):
            print(f"⚠️  WARNING: System {ip} has pending reboot flag set!")
            print(f"   This may cause unexpected reboots during testing")
        
        ps = (
            "$svc = Get-Service | Where-Object { $_.Name -like '*Deep*Security*Agent*' -or $_.DisplayName -like '*Deep*Security*Agent*' };"
            "if ($null -ne $svc) { Stop-Service -Name $svc.Name -ErrorAction SilentlyContinue; Write-Output ('Stopped ' + $svc.Name) }"
            " else { Write-Output 'DSA service not found' }"
        )
        self.execute_cmd(ps, ip, user, pwd, tool=tool)

    def activate_dsa(self, ip, user, pwd):
        print(f"{'+' * 50}\n # {self.ip_type[ip]}-{ip} Activate DSA #\n{'+' * 50}")
        tool = "Powershell.exe"
        ps = (
            "$svc = Get-Service | Where-Object { $_.Name -like '*Deep*Security*Agent*' -or $_.DisplayName -like '*Deep*Security*Agent*' };"
            "if ($null -ne $svc) { Start-Service -Name $svc.Name -ErrorAction SilentlyContinue; Write-Output ('Started ' + $svc.Name) }"
            " else { Write-Output 'DSA service not found' }"
        )
        self.execute_cmd(ps, ip, user, pwd, tool=tool)

    def reboot_instance(self, instance_id, access_key, secret_key, region):
        print(f"{self.header}\n # Reboot {instance_id} Instance #\n{self.header}")

        # Connect to EC2
        ec2_conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

        # Fetch instance details
        instances = ec2_conn.get_only_instances(instance_ids=[instance_id])
        if not instances:
            raise Exception(f"Instance {instance_id} not found in region {region}")

        instance = instances[0]
        print(f"Found instance id: {instance_id}")

        # Stop the instance
        instance.stop()
        print(f"Stopping {instance_id} ...")

        # Wait for the instance to stop
        while instance.update() != 'stopped':
            print("Waiting for instance to stop...")
            time.sleep(10)

        # Start the instance
        instance.start()
        print(f"Starting {instance_id} ...")

        # Wait for the instance to start
        while instance.update() != 'running':
            print("Waiting for instance to start...")
            time.sleep(10)

        # Refresh instance info and return IPs
        instance.update()
        print(f"{instance_id} is running with Public IP: {instance.ip_address}, Private IP: {instance.private_ip_address}")
        
        # Wait for WinRM to be ready (Windows fully booted)
        print(f"Waiting for WinRM service to be ready on {instance.ip_address}...")
        max_attempts = 6  # 1 minute max (we have 90s stabilization period after reboot anyway)
        for attempt in range(max_attempts):
            try:
                test_client = Client(instance.ip_address, username="Administrator", password="TempPassword", encrypt=False)
                test_client.connect(timeout=10)
                test_client.disconnect()
                print(f"✓ WinRM ready on {instance.ip_address}")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"  Attempt {attempt + 1}/{max_attempts}: WinRM not ready yet, waiting 10s...")
                    time.sleep(10)
                else:
                    print(f"⚠️  WinRM readiness check timed out, proceeding anyway (90s stabilization period will follow)")

        return instance.ip_address, instance.private_ip_address

    def get_dependency_portlist(self, path, grule, identifiers):
        server_rules, client_rules, non_dpi_rules = [], [], []
        all_dep_rules, client_dep_rules, portlist_set = set(), set(), set()
        grule_list = [grule]

        all_identifier = []
        print(f"Identifiers get_dependency_portlist: {identifiers}")
        print(f"Length Identifiers get_dependency_portlist: {len(identifiers)}")

        if len(identifiers) == 1:
            all_identifier = identifiers
        elif os.path.exists(self.rule_file):
            with open(self.rule_file, "r") as f:
                all_identifier = f.read().split(",")
        elif not os.path.exists(self.server_rule_file):
            all_identifier = identifiers
        
        print(f"Rules get dependency portlist: {all_identifier}")

        json_file = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        print(f"Json File: {json_file}")
        with open(os.path.join(path, json_file[0]), "r") as fout:
            self.src_pkg_json = json.load(fout)

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
        print(f"{'*' * 100}\nAll Rules: {all_identifier}\nServer Rules: {server_rules}\nDependency of Server Rules: {all_dep_rules}")
        client_rules_iden = client_rules[:]
        print(f"{'*' * 100}\nClient Rules: {client_rules}\nDependency of Client Rules: {client_dep_rules}")
        print(f"Good Rule with Dependency: {grule_list}\nNon DPI Rule: {non_dpi_rules}\n")
        print(f"PortList: {port_list}\n{'*' * 100}")

        if all_dep_rules:
            server_rules.extend(list(all_dep_rules))

        if client_dep_rules:
            client_rules.extend(list(client_dep_rules))

        server_rules.extend(non_dpi_rules)
        # Ensure the directory exists
        directory = os.path.dirname(self.server_rule_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Safely handle file creation and removal
        if os.path.exists(self.server_rule_file):
            os.remove(self.server_rule_file)
        with open(self.server_rule_file, "w") as f:
            f.write(",".join(server_rules))
        with open(self.server_rule_file, "r") as f:
            print(f"Server Rule get_dependency_portlist: {f.read()}")
        with open(self.portlist_file, "w") as f:
            json.dump(port_list, f)
        client_rules.extend(non_dpi_rules)
        
        directory = os.path.dirname(self.client_rule_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        if os.path.exists(self.client_rule_file):
            os.remove(self.client_rule_file)
        with open(self.client_rule_file, "w") as f:
            f.write(",".join(client_rules))
        with open(self.client_rule_file, "r") as f:
            print(f"Client Rule get_dependency_portlist: {f.read()}")
        print(f"grule_list get_dependency_portlist: {grule_list} | identifers get_dependency_portlist: {identifiers} | client_rules_iden get_dependency_portlist: {client_rules_iden}")
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
                print(f"{dep_rule['Identifier']} Dependency Found of {rule['Identifier']} Rule")
                return dep_rule

    def get_port_info(self, rule, portlist_set):
        port1, port2 = "PortLists", "PortList"
        con1, con2 = "ConnectionTypes", "ConnectionType"
        port_id, con_tbuid = "PortListTBUID", "ConnectionTypeTBUID"

        for con in self.src_pkg_json[con1][con2]:
            if rule[con_tbuid] in con["TBUID"].split(","):
                if con[port_id]:
                    for port in self.src_pkg_json[port1][port2]:
                        if con[port_id] in port["TBUID"].split(","):
                            print(f"- {rule['Identifier']} Rule PortList, {port}")
                            try:
                                sani_port = {k: (v if v is not None else "") for k, v in port.items() if k != "Issued"}
                                return portlist_set.add(tuple(sani_port.items()))
                            except Exception as exc:
                                print(f"Exception: {exc} at Port List: {port}")
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

    def enable_agent_filter(self, sip, suser, spwd, cip, cuser, cpwd, scenario):
        """Enable agents and filters with parallel filter activation."""
        print("+" * 50)
        print("Enabling agents and filters...")
        start_time = time.time()
        
        # Activate agents sequentially (DSM operations must be sequential)
        if scenario in ["Server_Download", "Server_Upload"]:
            self.activate_dsa(sip, suser, spwd)
        if scenario == "Client_Download":
            self.activate_dsa(cip, cuser, cpwd)
        
        # Enable filters in parallel
        machines_to_enable = []
        if scenario in ["Server_Download", "Server_Upload"]:
            machines_to_enable.append({
                'ip': sip,
                'user': suser,
                'pwd': spwd,
                'adaptor_name': self.s_adap_name
            })
        if scenario == "Client_Download":
            machines_to_enable.append({
                'ip': cip,
                'user': cuser,
                'pwd': cpwd,
                'adaptor_name': self.c_adap_name
            })
        
        # Parallel filter enablement
        if machines_to_enable:
            self.enable_filters_parallel(machines_to_enable, max_workers=len(machines_to_enable))
        
        elapsed = time.time() - start_time
        print(f"Agent and filter enablement complete in {elapsed:.1f}s")
        print(f"Waiting for stabilization... (additional 5s)")
        time.sleep(5)  # Reduced from 30s to 5s for stabilization