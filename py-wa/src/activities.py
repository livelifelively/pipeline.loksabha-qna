import asyncio
from temporalio import activity
from typing import Any, TypedDict, List, Optional

class ParliamentQuestion(TypedDict):
    quesNo: int
    subjects: str
    lokNo: str
    member: List[str]
    ministry: str
    type: str
    date: str
    questionsFilePathLocal: str
    questionsFilePathWeb: str
    questionsFilePathHindiLocal: Optional[str]
    questionsFilePathHindiWeb: Optional[str]
    questionText: Optional[str]
    answerText: Optional[str]
    sessionNo: Optional[str]

@activity.defn
async def pyActivity(input_data: List[ParliamentQuestion]) -> Any:
    print(f"Running Python activity with input: {input_data}")
    await asyncio.sleep(0.5) # Simulate processing
    return input_data   