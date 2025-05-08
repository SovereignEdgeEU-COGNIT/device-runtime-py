
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._logger import CognitLogger
from subprocess import Popen, PIPE, STDOUT
import shlex  
import time

import sys

sys.path.append(".")

class LatencyCalculator:

    def __init__(self, ecf: EdgeClusterFrontendClient, interval: int = 2):

        self.logger = CognitLogger()
        self.running = True
        self.interval = interval
        self.host = ecf.address.split("//")[1]
        self.ecf = ecf

    def get_simple_cmd_output(self, cmd, stderr=STDOUT) -> str:
        """
        Execute a simple external command and get its output.
        """
        args = shlex.split(cmd)
        return Popen(args, stdout=PIPE, stderr=stderr).communicate()[0].decode()

    def calculate(self) -> float:
        """
        Calculate the latency of the host.
        """
        # Extracting time=XXXms from the last line
        latency_line = None
        try:
            cmd = f"ping -c 1 {self.host}"
            output = self.get_simple_cmd_output(cmd)
            latency_line = output.strip().split("\n")[1]
            latency = float(latency_line.split("time=")[-1].split()[0])
        except (IndexError, ValueError):
            if latency_line:
                self.logger.error("Failed to parse latency from:", latency_line)
            else:
                pass
                # self.logger.error(f"Failed to parse latency from host: {self.host}")
            return -1.0  # Return -1.0 if parsing fails

        return latency
    
    def run(self):
        """
        Run the latency calculator.

        :param interval: The interval in seconds to calculate the latency.
        """

        while self.running:

            # Calculate the latency
            latency = self.calculate()

            if (latency == -1.0):
                # self.logger.error("Failed to calculate latency")
                continue
            else:
                self.logger.info(f"Latency: {latency} ms")
                is_sent = self.ecf.send_metrics(latency)

            if (is_sent):
                self.logger.info("Latency sent")
            else:
                self.logger.error("Failed to send the latency")

            time.sleep(self.interval)

    def stop(self):
        """
        Stop the latency calculator.
        """
        self.running = False

    def set_interval(self, interval: int):
        """
        Set the interval in seconds to calculate the latency.
        """
        self.interval = interval