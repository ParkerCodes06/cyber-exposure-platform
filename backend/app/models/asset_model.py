from pydantic import BaseModel, Field
from typing import List


class AssetIngest(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    os: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., min_length=1, max_length=45)
    open_ports: List[int] = Field(default_factory=list)
