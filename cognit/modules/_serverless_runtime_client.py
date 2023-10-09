import pydantic
import requests as req

from cognit.models._serverless_runtime_client import *
from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

VERSION = "v1"
FAAS_EXECUTE_SYNC_ENDPOINT = "faas/execute-sync"
FAAS_EXECUTE_ASYNC_ENDPOINT = "faas/execute-async"
FAAS_WAIT_ENDPOINT = "faas/xx-xxx-xx/status"

REQ_TIMEOUT = 5


class ServerlessRuntimeClient:
    def __init__(self, endpoint: str):
        """
        Constructor for ServerlessRuntimeClient

        Args:
            endpoint (str): String containing the HTTP URL of the Runtime
        """
        self.endpoint = endpoint

    def faas_execute_sync(self, payload: ExecSyncParams) -> ExecResponse:
        """
        Perform the offload of a function to the cognit platform and wait for\
        the result.

        Args:
            payload: The content of the request to send.
        Returns:
            ExecResponse: Return execution response
        """

        # Define POST request URL, payload or body and headers.
        url = "{}/{}/{}".format(self.endpoint, VERSION, FAAS_EXECUTE_SYNC_ENDPOINT)

        try:
            r = req.post(url, json=payload.dict(), timeout=REQ_TIMEOUT)
            # Check if status code is 200
            response = None
            if r.status_code == 200:
                response = pydantic.parse_obj_as(ExecResponse, r.json())

            cognit_logger.warning("Faas execute sync [POST] URL: {}".format(url))
            cognit_logger.warning("Faas execute sync payload: {}".format(payload))
            # Return the status code of the response
            if response == None:
                return ExecResponse(ret_code=ExecReturnCode.ERROR, err=r.status_code)
            else:
                return response
        except Exception as e:
            cognit_logger.error("Couldn't run sync request; {0}".format(e))
            cognit_logger.error("Faas execute sync [POST] URL: {}".format(url))
            cognit_logger.error("Faas execute sync payload: {}".format(payload))
            return ExecResponse(ret_code=ExecReturnCode.ERROR)

    def faas_execute_async(self, payload: ExecSyncParams) -> AsyncExecResponse:
        """
        Perform the offload of a function to the cognit platform asynchronously.

        Args:
            payload: The content of the request to send.
        Returns:
            AsyncExecResponse: Return asynchronous execution response
        """

        # Define POST request URL, payload or body and headers.
        url = "{}/{}/{}".format(self.endpoint, VERSION, FAAS_EXECUTE_ASYNC_ENDPOINT)

        try:
            r = req.post(url, json=payload.dict(), timeout=REQ_TIMEOUT)
            cognit_logger.warning("Faas execute async [POST] URL: {}".format(url))
            cognit_logger.warning("Faas execute sync payload: {}".format(payload))
            # Check if status code is 200
            response = None
            if r.status_code == 200:
                response = pydantic.parse_obj_as(AsyncExecResponse, r.json())
                # Return the status code of the response
                return response
            elif r.status_code == 400:
                return AsyncExecResponse(
                    status=AsyncExecStatus.FAILED,
                    exec_id=AsyncExecId(faas_task_uuid="000-000-000"),
                    res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                )
            else:
                return AsyncExecResponse(
                    status=AsyncExecStatus.READY,
                    exec_id=AsyncExecId(faas_task_uuid="000-000-000"),
                    res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                )

        except Exception as e:
            cognit_logger.error("Couldn't run async request; {0}".format(e))
            cognit_logger.error(f"URL: {url}")
            return AsyncExecResponse(
                status=AsyncExecStatus.READY,
                res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                exec_id=AsyncExecId(faas_task_uuid="000-000-000"),
            )

    def wait(self, Id: str) -> AsyncExecResponse:
        """
        Get asynchronously executed function response.

        Args:
            Id: The function identifier.
        Returns:
            AsyncExecResponse: Get asynchronous execution response
        """
        # Define GET request URL, payload or body and headers.
        faas_wait_ep = FAAS_WAIT_ENDPOINT.replace("xx-xxx-xx", str(Id))
        url = "{}/{}/{}".format(self.endpoint, VERSION, faas_wait_ep)
        cognit_logger.info("Wait [GET] URL: {}".format(url))

        try:
            r = req.get(url, timeout=REQ_TIMEOUT)
            # Check if status code means successful
            response = None
            if r.status_code == 200:
                response = pydantic.parse_obj_as(AsyncExecResponse, r.json())
            
            if r.status_code == 400:
                response = pydantic.parse_obj_as(AsyncExecResponse, r.json())
            
            # Return the status code of the response
            return response
        except Exception as e:
            cognit_logger.error(
                "Couldn't check the async AsyncExecResponse\
                    status; {0}".format(
                    e
                )
            )
            cognit_logger.error(f"URL: {url}")
            return AsyncExecResponse(
                status=AsyncExecStatus.READY,
                res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                exec_id=AsyncExecId(faas_task_uuid="000-000-000"),
            )
