from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Group Citizen Attribute task output
class GroupCitizenAttributeMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the *group* citizen attribute mention
    phrase extraction task.

    Contains a list of strings, each being a potential mention phrase describing
    a group classification or characteristic.
    """
    group_citizen_attribute_mention_phrases: List[str]
    """
    List of potential phrases describing citizen *group* attributes, classifications,
    or categories extracted directly from the input text.
    """

def create_group_citizen_attribute_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that mention specific
    citizen **group** attributes, classifications, or categories based on shared characteristics.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for group citizen attribute phrase highlighting.
    """

    group_citizen_attribute_highlighting_task = Task(
        name="group_citizen_attribute_phrase_highlighting",

        description="""
        Identify and extract meaningful phrases from the input statement that name or describe specific **citizen group classifications or categories based on shared characteristics**.
        Focus on identifying how collective groups of people are classified based on **shared** family structure, social identity (caste, tribe, religion), economic strata (as applied to groups), organizational membership (SHGs), or special collective status (disaster-affected).
        Include geographic terms (like 'rural', 'urban', district names) **only when they are explicitly used in the phrase to define the target group of people** (e.g., 'rural households', 'residents of aspirational districts'), not just as standalone location mentions.
        Critically, **exclude attributes primarily assessed at the individual level** (e.g., specific age, personal disability status) - these are handled by a separate task.
        Do NOT extract simple counts/metrics, organization names, program names, service descriptions, or benefit descriptions.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a **citizen group attribute, classification, or category**. These phrases are expected to be:

        - Focused on Group Attributes/Classifications: Clearly describing a collective classification based on shared traits (e.g., 'families below poverty line', 'Scheduled Tribe members', 'Self-Help Groups', 'urban poor').
        - Represents Collective Classification: Identifies how groups, communities, or populations are categorized.
        - **Includes Geographic Classifiers (Contextually):** Geographic terms are included *only* if part of a phrase defining the group (e.g., 'rural communities', 'households in urban slums', 'population of District Y'). Standalone location names ('Delhi', 'rural areas') are generally excluded unless the context strongly implies classification using that name.
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides health cover... to families constituting the economically vulnerable bottom 40% of India’s population. It targets households in rural areas and urban slums. Special provisions exist for persons with disabilities and Scheduled Tribe communities. Support is also provided to Self-Help Groups (SHGs) located in aspirational districts."

        Expected Output List (Group Citizen Attribute Phrases only):
        ```
        [
        "families constituting the economically vulnerable bottom 40% of India’s population",
        "economically vulnerable bottom 40% of India’s population",
        "bottom 40% of India’s population",
        "families",
        "households in rural areas",
        "urban slums",
        "Scheduled Tribe communities",
        "Self-Help Groups (SHGs)",
        "SHGs",
        "aspirational districts"
        ]
        ```
        (Explanation: Phrases defining economic strata ("bottom 40%..."), family units ("families"), social classifications ("Scheduled Tribe communities"), organizational types ("Self-Help Groups"), and location-defined groups ("households in rural areas", "urban slums", "aspirational districts" [implicitly referring to residents/groups within]) are included. Individual attributes are excluded. Standalone 'rural areas' is excluded, but 'households in rural areas' is included.)

        Key Considerations:

        - **Capture Group Defining Phrases:** Extract text specifying collective characteristics (family type, social group, economic strata, organization type).
        - **Contextual Geographic Extraction:** Geographic terms should only be extracted if they function within the phrase to classify the *group* being discussed (e.g., 'rural population', 'residents of X'). Avoid standalone place names unless used this way.
        - **Include Family/Household Level:** Attributes applying to family or household units are included here.
        - **Economic Strata:** Group-based economic classifications are included.
        - **Exclude Individual Attributes:** Do *not* extract phrases primarily describing individual characteristics.
        - **Exclude Other Entities:** Do not extract Program names, Service descriptions, Benefit descriptions, or Organization names.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        """,

        agent=agent,

        async_execution=False,

        output_pydantic=GroupCitizenAttributeMentionPhrasesOutput
    )

    return group_citizen_attribute_highlighting_task