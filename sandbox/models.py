from typing import Optional, List

from pydantic import BaseModel

class ExecutorModel(BaseModel):
    url: str

class PackagePayload(BaseModel):
    executor: str
    replicas: Optional[int] = 1
    endpoints: Optional[List[str]] = []


class DeployResult(BaseModel):
    success: bool
    code: int
    data: Optional[ExecutorModel]
    message: str
