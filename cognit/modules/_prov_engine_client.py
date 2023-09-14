import pydantic
import requests as req

from cognit.models._prov_engine_client import ServerlessRuntime
from cognit.models._serverless_runtime_client import *
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

SR_RESOURCE_ENDPOINT = "serverless-runtimes"

REQ_TIMEOUT = 5


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
        self.endpoint = "https://{0}:{1}".format(
            self.config.prov_engine_endpoint, self.config.prov_engine_port
        )

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

        r = req.post(url, json=serverless_runtime.dict(), timeout=REQ_TIMEOUT)
        cognit_logger.warning("Create [POST] URL: {}".format(url))

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
        r = req.get(url, timeout=REQ_TIMEOUT)
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
        r = req.delete(url, timeout=REQ_TIMEOUT)
        cognit_logger.warning("Delete [DELETE] URL: {}".format(url))

        if r.status_code != 204:
            cognit_logger.error(
                "Provisioning engine returned {} on delete".format(r.status_code)
            )
            return False

        return True
