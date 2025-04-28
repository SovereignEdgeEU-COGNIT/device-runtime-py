from typing import Callable, List, Any
from pydantic import BaseModel, Field
from enum import Enum

class ExecReturnCode(Enum):
    SUCCESS = 0
    ERROR = -1

class FunctionLanguage(str, Enum):
    PY = "PY"
    C = "C"

class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"

class Call(BaseModel):
    function: Callable = Field(
        description="The function to be offloaded")
    fc_lang: FunctionLanguage = Field(
        description="The language of the offloaded function 'PY' or 'C'")
    callback: Callable | None = Field(
        description="The callback function to be executed after the offloaded function finishes")
    mode: ExecutionMode = Field(
        description="The mode of execution of the offloaded function (SYNC or ASYNC)")
    params: List[Any] = Field(
        description="A list containing the function parameters encoded in base64")
    
class ExecResponse(BaseModel):
    ret_code: ExecReturnCode = Field(
        default=ExecReturnCode.SUCCESS,
        description="Offloaded function execution result (0 if finished successfully, 1 if not)",
    )
    res: str | None = Field(
        default=None,
        description="Result of the offloaded function",
    )
    err: str | None = Field(
        default=None,
        description="Offloaded function execution error description",
    )