from cognit.modules._logger import CognitLogger
from subprocess import Popen, PIPE, STDOUT
import shlex  
import json
import sys

sys.path.append(".")

class LatencyCalculator:

    def __init__(self):

        self.logger = CognitLogger()

    def get_simple_cmd_output(self, cmd, stderr=STDOUT) -> str:
        """
        Execute a simple external command and get its output.

        :param cmd: Command to execute.
        :param stderr: Where to redirect stderr, default is STDOUT.
        :return: Output of the command as a string.
        :raises: OSError if the command fails to execute.
        """

        args = shlex.split(cmd)
        return Popen(args, stdout=PIPE, stderr=stderr).communicate()[0].decode()
    
    def get_latency_for_clusters(self, edge_clusters: list) -> str:
        """
        Gets the address who has the lowest latency to the given edge clusters.

        :param edge_clusters: List of edge clusters to check latency against.
        :return: JSON string with the latency of each edge cluster.
        """

        latency_by_cluster = {}

        for cluster_ip in edge_clusters:

                # Latency of cluster_ip
                latency = self.calculate(cluster_ip)

                if latency < 0:
                    self.logger.error(f"Failed to calculate latency for {cluster_ip}")
                    continue

                latency_by_cluster[cluster_ip] = latency

        # Return lowest latency cluster as JSON string
        if not latency_by_cluster:
            self.logger.error("No valid edge clusters found.")
            return json.dumps({"error": "No valid edge clusters found."})
        
        self.logger.info("Calculated latency for edge clusters:", latency_by_cluster)
        return json.dumps(latency_by_cluster)

    def calculate(self, ip: str) -> float:
        """
        Calculate the latency of the given ip.

        :param ip: IP address to calculate latency for.
        :return: Latency in milliseconds, or -1.0 if parsing fails.
        """

        latency_line = None

        try:

            cmd = f"ping -c 1 {ip}"
            output = self.get_simple_cmd_output(cmd)
            latency_line = output.strip().split("\n")[1]
            latency = float(latency_line.split("time=")[-1].split()[0])
            self.logger.info(f"Latency for {ip}: {latency} ms")

        except (IndexError, ValueError):

            if latency_line:
                self.logger.error("Failed to parse latency from:", latency_line)
            else:
                self.logger.error(f"Failed to parse latency from host: {self.host}")
            return -1.0  # Return -1.0 if parsing fails

        return latency
    
