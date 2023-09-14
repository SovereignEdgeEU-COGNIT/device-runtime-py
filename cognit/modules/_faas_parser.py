import base64 as b64
from typing import Any

import cloudpickle as cp


class FaasParser:
    """
    This class is responsible for serializing the functions that will be offloaded
    and deserializing the results that will be returned from the serverless runtime.
    """

    def __init__(self):
        pass

    def serialize(self, fc) -> str:
        # For now clear the __global__ attribute to avoid sending global namespace info
        # TODO: Implement a dependency analyzer to send the required imports
        if hasattr(fc, "__globals__"):
            g = fc.__globals__.copy()
            fc.__globals__.clear()
            # Cloudpickle it
            blob_cp = cp.dumps(fc)
            fc.__globals__.update(g)
        else:
            # Cloudpickle it
            blob_cp = cp.dumps(fc)

        ## Encode it in base64
        blob_b64 = b64.b64encode(blob_cp)
        return blob_b64.decode("utf-8")

    def deserialize(self, input: bytes) -> Any:
        # TODO encapsulate logic to parse from bytes to object
        raise NotImplementedError
