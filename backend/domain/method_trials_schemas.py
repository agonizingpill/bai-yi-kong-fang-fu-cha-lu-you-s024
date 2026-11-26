from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

class TrialPair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    room_code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    target_day: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class OpenTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pairs: Annotated[list[TrialPair], Field(min_length=1, max_length=60)]


class LockTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class EnableTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
