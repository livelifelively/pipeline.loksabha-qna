from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class RunContext(BaseModel):
    run_id: str = Field(..., description="Unique identifier for the run")
    start_time: datetime = Field(..., description="Start time of the run")
    sansad: str = Field(..., description="Sansad identifier")
    session: str = Field(..., description="Session identifier")
    
    @classmethod
    def create(cls, sansad: str, session: str) -> 'RunContext':
        return cls(
            run_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            sansad=sansad,
            session=session
        ) 