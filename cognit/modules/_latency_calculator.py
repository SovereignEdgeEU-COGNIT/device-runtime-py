from cognit.modules._logger import CognitLogger
from subprocess import Popen, PIPE, STDOUT
import shlex  
import sys

sys.path.append(".")

class LatencyCalculator:

    def __init__(self):

        self.logger = CognitLogger()

    def get_simple_cmd_output(self, cmd, stderr=STDOUT) -> str:
        """
        Executes a simple command and returns its output as a string.
        
        Args:
            cmd (str): Command to be executed.
            stderr: Standard error handling (default: STDOUT).

        Returns:
            str: Output of the command as a string.
        """

        args = shlex.split(cmd)
        return Popen(args, stdout=PIPE, stderr=stderr).communicate()[0].decode()
    
    def get_latency_for_clusters(self, edge_clusters: list) -> dict:
        """
        Calculate the latency for a list of edge clusters.

        Args:
            edge_clusters (list): List of edge cluster IPs or domain names.

        Returns:
            dict: Dictionary with the edge cluster as key and its latency in milliseconds as value.
        """

        latency_by_cluster = {}

        for cluster_ip in edge_clusters:
                
                # Extract http:// or https:// from the cluster_ip if present and remove what is after ip or domain name
                if cluster_ip.startswith("http://"):

                    ip = cluster_ip[7:].split("/")[0]

                elif cluster_ip.startswith("https://"):

                    ip = cluster_ip[8:].split("/")[0]

                else:
                    
                    ip = cluster_ip.split("/")[0]

                # Remove port if present
                if ":" in ip:
                    ip = ip.split(":")[0]

                # Latency of cluster_ip
                latency = self.calculate(ip)

                if latency < 0:

                    self.logger.error(f"Failed to calculate latency for {ip}")
                    continue

                latency_by_cluster[cluster_ip] = latency

        # Return lowest latency cluster as JSON string
        if not latency_by_cluster:

            self.logger.error("No valid edge clusters found.")
            return {"error": "No valid edge clusters found."}
        
        return latency_by_cluster

    def calculate(self, ip: str) -> float:
        """
        Calculate the latency of the given ip.

        Args:
            ip (str): IP or domain name to calculate the latency.

        Returns:
            float: Latency in milliseconds. If the latency cannot be calculated, returns -1.
        """

        latency_line = None

        try:

            cmd = f"ping -c 1 {ip}"
            output = self.get_simple_cmd_output(cmd)
            latency_line = output.strip().split("\n")[1]
            latency = float(latency_line.split("time=")[-1].split()[0])
            self.logger.info(f"Latency for {ip}: {latency} ms")

        except Exception as e:

            self.logger.error(f"Failed to parse latency for {ip}: {e}")
            return -1.0

        return latency
    