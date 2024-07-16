from pydantic import BaseModel, Field
from typing import Optional


class Rule(BaseModel):
    name: str
    description: str
    conversations: int = 1
    when: Optional[str] = "True"
    if_: str = Field(..., alias="if")
    then: str
