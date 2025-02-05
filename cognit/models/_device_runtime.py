from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class FunctionLanguage(str, Enum):
    PY = "PY"
    C = "C"

class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"

class Call(BaseModel):
    function: callable = Field(
        description="The function to be offloaded")
    fc_lang: FunctionLanguage = Field(
        description="The language of the offloaded function 'PY' or 'C'")
    callback: callable = Field(
        description="The callback function to be executed after the offloaded function finishes")
    mode: ExecutionMode = Field(
        description="The mode of execution of the offloaded function (SYNC or ASYNC)")
    params: List[str] = Field(
        description="A list containing the function parameters encoded in base64")