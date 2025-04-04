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
        Identify and extract meaningful, contextually rich phrases from the input statement that represent mentions of metrics, measurements, and quantitative data.
        Each extracted phrase should ideally contain:
        1.  **What is being measured** (e.g., 'health cover', 'beneficiaries').
        2.  The associated **numerical value including magnitude words** (e.g., '5 lakhs', '55 crore', '40%').
        3.  The **unit of measurement**, which can be explicit (e.g., 'per family per year', 'Rs. lakh crore') or implied by context (e.g., the noun in '55 crore beneficiaries').

        The primary goal is to extract the **complete, verbatim phrase** from the input text that encompasses these elements, preserving all original wording including magnitude and implicit units.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted (highlighted) directly from the input statement. Each phrase in the list represents a potential mention of a metric, measurement, or quantitative data. These phrases are expected to be:

        - Contextually Meaningful: Each phrase should capture a meaningful unit of text from the input, not just isolated numbers or keywords. They should provide enough context to understand what is being measured or quantified.
        - Quantitatively Focused: The phrases should relate to numerical values, measurements, or quantities. They should contain elements like numerical values, units of measurement (explicit or implied), magnitude words, or metric keywords.
        - **Directly and Exactly from Input**: The phrases MUST be extracted directly and exactly from the input text, preserving the original wording, phrasing, and spelling. **No modifications, additions, rephrasing, or interpretations are allowed.** This is critical for preserving nuances.
        - Representing Metric Mentions: Each phrase is identified as a *potential* metric mention, meaning it's a candidate for further analysis as a metric or measurement. The task focuses on identifying these potential mentions, not on validating or classifying them as definitive metrics.

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

        - For example, in "health cover of Rs. 5 lakhs per family per year", "health cover" corresponds to what is being measured, "5 lakhs" is the quantity/value (including magnitude), and "Rs. per family per year" is the explicit unit.
        - **Handling Implicit Units:** In phrases like "55 crore beneficiaries", the unit (a count) is **implied** by the noun "beneficiaries". Such phrases are **valid and required**. The task is to extract the phrase exactly as it appears, preserving the term ("beneficiaries") that provides the implicit unit context. **Do NOT attempt to add or substitute a generic unit like 'people' or 'count'.**
        - Context is Prioritized: Notice that shorter phrases like just "5 lakhs", "55 crore", or "40%" are **not** included as standalone outputs in the expected list. This is because the task prioritizes extracting *contextually rich phrases* that provide more information about *what* is being measured.
        - Meaningful Phrases: The extracted phrases are meaningful units of text that represent complete metric mentions within the context of the input statement.
        - **Direct Extraction Re-emphasis:** The requirement to copy phrases *exactly* means no summarization, normalization, or altering of the text is permitted in this step.
        - Dates Excluded (in this context): Dates like "01.01.2025" are generally excluded as metric *measurements* in this task, focusing on quantities, rates, and values representing amounts or counts. Date values might be handled by a different entity extraction task.
        """,

        agent=agent,
        
        async_execution=False,
        
        output_pydantic=MetricMentionPhrasesOutput
    )

    return metric_highlighting_task
