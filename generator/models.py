from pydantic import BaseModel

class PackagePayload(BaseModel):
    executor: str
    type: str = 'k8s'
    protocol: str = 'http'
