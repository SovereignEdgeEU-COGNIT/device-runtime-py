from pydantic import BaseModel, Field
from typing import Optional
from typing import List
from enum import Enum

class FunctionLanguage(str, Enum):
    PY = "PY"
    C = "C"
class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
class ExecParams(BaseModel):
    lang: str
    fc: str
    fc_hash: str
    params: list[str]
class ExecReturnCode(Enum):
    SUCCESS = 0
    ERROR = -1
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
    
class Execution(BaseModel):
    app_reqs_id: int = Field(
        description="Application Requirement document ID")
    function_id: int = Field(
        description="Function document ID")
    lang: FunctionLanguage = Field(
        description="The language of the offloaded function 'PY' or 'C'")
    params: List[str] = Field(
        description="A list containing the function parameters encoded in base64")
    