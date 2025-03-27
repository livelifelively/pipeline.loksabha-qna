
from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the task output
class MetricMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the metric mention phrase extraction task.

    The output is a list of strings, where each string is a potential metric mention phrase
    extracted from the input text.
    """
    metric_mention_phrases: List[str]
    """
    List of potential metric mention phrases extracted from the input text.
    Each string is a contiguous text segment from the input.
    """

def create_metric_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting meaningful metric mention phrases in an input statement.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for metric phrase highlighting.
    """

    metric_highlighting_task = Task(
        name="metric_phrase_highlighting",

        description="""
        Identify and highlight meaningful phrases from the input statement that represent mentions of metrics, measurements, and quantitative data. 
        The focus is on highlighting contextually rich phrases that clearly indicate what is being measured, the associated numerical values and unit of measurement.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted (highlighted) directly from the input statement. Each phrase in the list represents a potential mention of a metric, measurement, or quantitative data. These phrases are expected to be:

        - Contextually Meaningful: Each phrase should capture a meaningful unit of text from the input, not just isolated numbers or keywords. They should provide enough context to understand what is being measured or quantified.
        - Quantitatively Focused: The phrases should relate to numerical values, measurements, or quantities. They should contain elements like numerical values, units of measurement, magnitude words, or metric keywords.
        - Directly from Input: The phrases are extracted directly from the input text, preserving the original wording and phrasing. No modifications or re-engineering of the phrases are expected at this stage.
        - Representing Metric Mentions:  Each phrase is identified as a *potential* metric mention, meaning it's a candidate for further analysis as a metric or measurement.  The task focuses on identifying these potential mentions, not on validating or classifying them as definitive metrics.

        Example:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) is a flagship scheme of the Government which provides health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization to approximately 55 crore beneficiaries corresponding to 12.37 crore families constituting economically vulnerable bottom 40% of India’s population. Recently, the scheme has been expanded to cover 6 crore senior citizens of age 70 years and above belonging to 4.5 crore families irrespective of their socio-economic status under AB-PMJAY with Vay Vandana Card. As on 01.01.2025, a total of 8.59 crore hospital admissions worth Rs.1.19 lakh crore have been authorized under the scheme"

        Expected Output List:
        ```
        [
        "health cover of Rs. 5 lakhs per family per year",
        "55 crore beneficiaries",
        "12.37 crore families",
        "40% of India’s population",
        "6 crore senior citizens of age 70 years and above",
        "4.5 crore families",
        "8.59 crore hospital admissions",
        "hospital admissions worth Rs.1.19 lakh crore"
        ]
        ```

        Key Considerations Illustrated by the Example:

        - For example, in "health cover of Rs. 5 lakhs per family per year", "health cover" corresponds to what is being measured, "5 lakhs" what is the quantity in terms of value and magnitude, and "Rs. per family per year" is the unit of measurement. all three parts, that are, what is being measured, how much is measurement (value and magnitude) and unit, are all mandatory.
        - Context is Prioritized: Notice that shorter phrases like just "5 lakhs", "55 crore", or "40%" are **not** included as standalone outputs in the expected list. This is because the task prioritizes extracting *contextually rich phrases* that provide more information about *what* is being measured.
        - Meaningful Phrases: The extracted phrases are meaningful units of text that represent complete metric mentions within the context of the input statement.
        - Direct Extraction: The phrases are directly copied from the input text, maintaining the original wording and order.
        - Dates Excluded (in this context): Dates are generally excluded as metric *measurements* in this task, focusing on quantities, rates, and values.
        """,

        agent=agent,
        
        async_execution=False,
        
        output_pydantic=MetricMentionPhrasesOutput
    )

    return metric_highlighting_task
