from temporalio import activity
from typing import List
from ..models.parliament import ParliamentQuestion

@activity.defn
# async def process_questions(questions: List[ParliamentQuestion]) -> List[ParliamentQuestion]:
async def process_questions(questions: str) -> str:
    """Process parliament questions activity."""
    print(f"Processing {len(questions)} parliament questions")
    return questions
