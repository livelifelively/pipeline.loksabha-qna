from typing import Any

from temporalio import activity

from apps.py.pipeline.sansad_session_pipeline import sansad_session_pipeline


@activity.defn
async def process_questions(input_string: str) -> Any:
    """
    Process parliament questions activity.

    Args:
        input_string: Input string (similar to TypeScript activity)

    Returns:
        Any: Output from sansad session pipeline
    """
    activity.logger.info(f"Running Python activity with input: {input_string}")

    # Match TypeScript activity parameters
    sansad_session_questions = await sansad_session_pipeline(sansad="17", session="i")

    return sansad_session_questions
