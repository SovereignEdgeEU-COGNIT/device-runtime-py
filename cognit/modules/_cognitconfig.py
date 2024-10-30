import yaml

from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

DEFAULT_CONFIG_PATH = "./examples/cognit.yml"

class CognitConfig: 
    ## dann1 code uses JSON, but going to keep YAML and modify conf.yml file
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self._cognit_frontend_engine_endpoint = None
        self._cognit_frontend_engine_port = None
        self._cognit_frontend_engine_usr = None
        self._cognit_frontend_engine_pwd = None
        self._servl_runt_port = None
        with open(config_path, "r") as file:
            try:
                self.cf = yaml.safe_load(file)
                # TODO : Properly set as properties.
                
                credentials = self.cf['credentials'].split(':')
                self._cognit_frontend_engine_usr = credentials[0]
                self._cognit_frontend_engine_pwd = credentials[1]

            except yaml.YAMLError as exc:
                cognit_logger.debug(exc)

    def get_prov_context(self):
        return (
            self.cf["default"]["host"],
            self.cf["default"]["port"],
            self.cf["default"]["pe_usr"],
        )

    @property
    def cognit_frontend_engine_endpoint(self):
        # Lazy read value
        if self._cognit_frontend_engine_endpoint is None:
            # self._cognit_frontend_engine_endpoint = self.cf["api_endpoint"].split("://")[1].split(':')[0]
            self._cognit_frontend_engine_endpoint = self.cf["api_endpoint"]
        return self._cognit_frontend_engine_endpoint

    @property
    def cognit_frontend_engine_port(self):
        # Lazy read value
        if self._cognit_frontend_engine_port is None:
            self._cognit_frontend_engine_port = int(self.cf["api_endpoint"].split(':')[-1])
        return self._cognit_frontend_engine_port

    @property
    def cognit_frontend_engine_cfe_usr(self): # cfe stands for cognit frontend engine
        # Lazy read value
        if self._cognit_frontend_engine_usr is None:
            self._cognit_frontend_engine_usr = self.cf['credentials'].split(':')[0]
        return self._cognit_frontend_engine_usr

    @property
    def cognit_frontend_engine_cfe_pwd(self): 
        # Lazy read value
        if self._cognit_frontend_engine_pwd is None:
            self._cognit_frontend_engine_pwd = self.cf['credentials'].split(':')[1]
        return self._cognit_frontend_engine_pwd
    
    @property
    def servl_runt_port(self): # TODO: Remove
        # Lazy read value
        if self._servl_runt_port is None:
            self._servl_runt_port = self.cf["sr_port"]
        return self._servl_runt_port




