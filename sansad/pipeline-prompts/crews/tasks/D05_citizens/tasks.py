from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Individual Citizen Attribute task output
class IndividualCitizenAttributeMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the *individual* citizen attribute mention
    phrase extraction task.

    Contains a list of strings, each being a potential mention phrase describing
    an attribute or characteristic assessed at the individual level.
    """
    individual_citizen_attribute_mention_phrases: List[str]
    """
    List of potential phrases describing *individual* citizen attributes or criteria
    extracted directly from the input text.
    """

def create_individual_citizen_attribute_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that mention specific
    attributes or characteristics assessed at the **individual citizen level**.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for individual citizen attribute phrase highlighting.
    """

    individual_citizen_attribute_highlighting_task = Task(
        name="individual_citizen_attribute_phrase_highlighting",

        description="""
        Identify and extract meaningful phrases from the input statement that name or describe specific **attributes, characteristics, or criteria assessed or applied at the level of individual citizens**.
        Focus on identifying how individuals are classified based on **personal** demographic (age, gender), specific health conditions, educational qualifications, individual employment status, or socioeconomic status when assessed personally (e.g., individual income check implied).
        Critically, **strictly exclude descriptions that define collective groups, geographic areas, administrative regions, family/household units, or broad economic strata** (e.g., 'rural population', 'Scheduled Tribes', 'families', 'bottom 40% population', 'urban slums', 'aspirational districts'). These group classifications are handled by a separate task. Focus only on characteristics pertaining to a single person.
        Do NOT extract simple counts/metrics, organization names, program names, service descriptions, or benefit descriptions.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of an **individual citizen attribute or criterion**. These phrases are expected to be:

        - Focused on Individual Attributes/Criteria: Clearly describing a characteristic assessable for or applied to a single person (e.g., 'senior citizens', 'pregnant women', 'persons with disabilities', 'unemployed youth', 'graduate').
        - Represents Personal Classification: Identifies how an individual person is categorized based on their personal traits or status.
        - **Excludes Group Classifiers:** Must not be phrases that primarily define a collective, location, family unit, or broad economic stratum.
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides health cover... to families constituting the economically vulnerable bottom 40% of India’s population. Recently, the scheme has been expanded to cover senior citizens of age 70 years and above. Special provisions exist for persons with disabilities. Eligibility often requires individuals to be residents and below a certain income threshold."

        Expected Output List (Individual Citizen Attribute Phrases only):
        ```
        [
        "senior citizens",
        "age 70 years and above",
        "persons with disabilities",
        "residents",
        "below a certain income threshold"
        ]
        ```
        (Explanation: "families constituting...", "economically vulnerable bottom 40%..." are group/strata descriptors, excluded. "Senior citizens," "age 70+," and "persons with disabilities" are clear individual attributes. "Residents" implies an individual status check. "Below a certain income threshold" implies an individual-level income check in this context, distinct from a broad population stratum like "bottom 40%".)

        Key Considerations:

        - **Capture Individual Defining Phrases:** Extract text specifying personal characteristics (age, health status, personal economic status check, residency status, education level, etc.).
        - **Strictly Exclude Group/Geographic/Family Descriptors:** Do *not* extract phrases defining collectives, regions, locations, family units (e.g., "rural households," "urban population," "Scheduled Tribes," "families"). This is critical for distinguishing from the Group Attribute task.
        - **Economic Terms (Individual Focus):** Include economic terms like "below poverty line" or "below income threshold" *only if* the context suggests an individual assessment, not when defining a broad population segment (like "bottom X%").
        - **Thresholds/Criteria:** Individual criteria like age thresholds ("age 70 years and above") or specific status ("unemployed," "resident") are valid targets.
        - **Exclude Metrics/Counts:** Do *not* extract simple counts/metrics.
        - **Exclude Other Entities:** Do not extract Program names, Service descriptions, Benefit descriptions, or Organization names.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        """,

        agent=agent,

        async_execution=False,

        output_pydantic=IndividualCitizenAttributeMentionPhrasesOutput
    )

    return individual_citizen_attribute_highlighting_task