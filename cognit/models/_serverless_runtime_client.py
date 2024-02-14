from enum import Enum
from typing import Optional

from pydantic import BaseModel


class status_exec(Enum):
    OK = 0
    WORKING = 1
    NOT_OK = -1


class Param(BaseModel):
    type: str
    var_name: str
    value: str  # Coded b64
    mode: str


class ExecSyncParams(BaseModel):
    lang: str
    fc: str
    fc_hash: str
    params: list[str]


class ExecAsyncParams(BaseModel):
    lang: str
    fc: str
    fc_hash: str
    params: list[str]


class FaasUuidStatus(BaseModel):
    state: str
    result: str | None = None


class ExecReturnCode(Enum):
    SUCCESS = 0
    ERROR = -1


class ExecResponse(BaseModel):
    ret_code: ExecReturnCode = ExecReturnCode.SUCCESS
    res: str | None = None
    err: str | None = None


class AsyncExecId(BaseModel):
    faas_task_uuid: str


class AsyncExecStatus(Enum):
    WORKING = "WORKING"
    READY = "READY"
    FAILED = "FAILED"


class AsyncExecResponse(BaseModel):
    status: AsyncExecStatus = AsyncExecStatus.WORKING
    res: Optional[ExecResponse]
    exec_id: AsyncExecId = AsyncExecId(faas_task_uuid="000-000-000")
