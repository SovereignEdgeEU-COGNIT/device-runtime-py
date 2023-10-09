import yaml

from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

DEFAULT_CONFIG_PATH = "./cognit.conf"


class CognitConfig:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self._prov_engine_endpoint = None
        self._prov_engine_port = None
        self._prov_engine_pe_usr = None
        self._prov_engine_pe_pwd = None
        # TODO : Return default values if json does not exist
        # with open("../../config/cognit.conf", "r") as file:
        with open(config_path, "r") as file:
            try:
                self.cf = yaml.safe_load(file)
                # TODO : Properly set as properties.
                self._prov_engine_pe_usr = self.cf["pe_usr"]
                self._prov_engine_pe_pwd = self.cf["pe_pwd"]

            except yaml.YAMLError as exc:
                cognit_logger.debug(exc)

    def get_prov_context(self):
        return (self.cf["default"]["host"], self.cf["default"]["port"], self.cf["default"]["pe_usr"])

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

    @property
    def prov_engine_pe_usr(self):
        # Lazy read value
        if self._prov_engine_pe_usr is None:
            self._prov_engine_pe_usr = self.cf["pe_usr"]
        return self._prov_engine_pe_usr

    @property
    def prov_engine_pe_pwd(self):
        # Lazy read value
        if self._prov_engine_pe_pwd is None:
            self._prov_engine_pe_pwd = self.cf["pe_pwd"]
        return self._prov_engine_pe_pwd
