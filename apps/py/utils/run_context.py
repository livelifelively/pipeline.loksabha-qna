import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from .timestamps import get_current_timestamp


class RunContext(BaseModel):
    run_id: str = Field(..., description="Unique identifier for the run")
    start_time: datetime = Field(..., description="Start time of the run")
    sansad: str = Field(..., description="Sansad identifier")
    session: str = Field(..., description="Session identifier")

    @classmethod
    def create(cls, sansad: str, session: str) -> "RunContext":
        return cls(run_id=str(uuid.uuid4()), start_time=get_current_timestamp(), sansad=sansad, session=session)
