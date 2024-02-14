import pydantic
import requests as req

from cognit.models._prov_engine_client import ServerlessRuntime
from cognit.models._serverless_runtime_client import *
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

SR_RESOURCE_ENDPOINT = "serverless-runtimes"

REQ_TIMEOUT = 60

def filter_empty_values(data):
    if isinstance(data, dict):
        return {key: filter_empty_values(value) for key, value in data.items() if value is not None}
    else:
        return data

class ProvEngineClient:
    def __init__(
        self,
        config: CognitConfig,
    ):
        """
        Cognit context request to Prov Eng.

        Args:
            config (CognitConfig): Cognit configuration object.

        """
        self.config = config
        self.endpoint = "http://{0}:{1}".format(
            self.config.prov_engine_endpoint, self.config.prov_engine_port
        )
        self.latency_to_pe = 0.0
        r = req.get(
            self.endpoint,
            auth=(self.config._prov_engine_pe_usr, self.config._prov_engine_pe_pwd),
            timeout=REQ_TIMEOUT,
        )
        if r != None:
            self.latency_to_pe = r.elapsed.total_seconds()
            cognit_logger.warning("Latency to Provisioning Engine is: {0}".format(self.latency_to_pe))

    def create(
        self, serverless_runtime: ServerlessRuntime
    ) -> Optional[ServerlessRuntime]:
        """
        Create Serverless runtime.

        Args:
            serverless_runtime (ServerlessRuntime): Cognit configuration object.
        Returns:
            ServerlessRuntime: Serverless runtime object.
        """
        response = None

        url = "{}/{}".format(self.endpoint, SR_RESOURCE_ENDPOINT)

        aux_dict = filter_empty_values(serverless_runtime.dict())
        cognit_logger.warning(str(aux_dict))

        cognit_logger.warning("Create [POST] URL: {}".format(url))
        r = req.post(
            url,
            auth=(self.config._prov_engine_pe_usr, self.config._prov_engine_pe_pwd),
            json=aux_dict,
            timeout=REQ_TIMEOUT,
        )

        if r.status_code != 201:
            cognit_logger.error(
                "Provisioning engine returned {} on create".format(r.status_code)
            )
            return response

        try:
            response = pydantic.parse_obj_as(ServerlessRuntime, r.json())

        except pydantic.ValidationError as e:
            cognit_logger.error(e)

        return response

    def retrieve(self, sr_id: int) -> Optional[ServerlessRuntime]:
        """
        Retrieves Serverless runtime status.

        Args:
            sr_id: Serverless runtime Id.
        Returns:
            ServerlessRuntime: Serverless runtime object.
        """
        response = None

        url = "{}/{}/{}".format(self.endpoint, SR_RESOURCE_ENDPOINT, sr_id)
        r = req.get(
            url,
            auth=(self.config._prov_engine_pe_usr, self.config._prov_engine_pe_pwd),
            timeout=REQ_TIMEOUT,
        )
        cognit_logger.warning("Retrieve [GET] URL: {}".format(url))

        if r.status_code != 200:
            cognit_logger.error(
                "Provisioning engine returned {} on retrieve".format(r.status_code)
            )
            return response

        try:
            response = pydantic.parse_obj_as(ServerlessRuntime, r.json())

        except pydantic.ValidationError as e:
            cognit_logger.error(e)

        return response

    def delete(self, sr_id: int) -> bool:
        """
        Delete the current Cognit context from Prov Eng.
        Returns:
            bool: Action succeded or not.
        """
        response = None

        url = "{}/{}/{}".format(self.endpoint, SR_RESOURCE_ENDPOINT, sr_id)
        r = req.delete(
            url,
            auth=(self.config._prov_engine_pe_usr, self.config._prov_engine_pe_pwd),
            timeout=REQ_TIMEOUT,
        )
        cognit_logger.warning("Delete [DELETE] URL: {}".format(url))

        if r.status_code != 204:
            cognit_logger.error(
                "Provisioning engine returned {} on delete".format(r.status_code)
            )
            return False

        return True
