import yaml

from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

DEFAULT_CONFIG_PATH = "./cognit.conf"


class CognitConfig:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self._prov_engine_endpoint = None
        self._prov_engine_port = None
        # TODO : REturbn default values if json does not exist
        # with open("../../config/cognit.conf", "r") as file:
        with open(config_path, "r") as file:
            try:
                self.cf = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                cognit_logger.debug(exc)

    def get_prov_context(self):
        return (self.cf["default"]["host"], self.cf["default"]["port"])

    @property
    def prov_engine_endpoint(self):
        # Lazy read value
        if self._prov_engine_endpoint is None:
            self._prov_engine_endpoint = self.cf["endpoint"]
        return self._prov_engine_endpoint

    @property
    def prov_engine_port(self):
        # Lazy read value
        if self._prov_engine_port is None:
            self._prov_engine_port = self.cf["port"]
        return self._prov_engine_port
