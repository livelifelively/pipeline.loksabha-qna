import asyncio
from temporalio import activity

@activity.defn
async def pyActivity(input_string: str) -> str:
    print(f"Running Python activity with input: {input_string}")
    await asyncio.sleep(0.5) # Simulate processing
    return f"Python: {input_string}"