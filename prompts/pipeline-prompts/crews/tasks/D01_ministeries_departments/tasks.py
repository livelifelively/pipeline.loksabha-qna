from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Government Organization task output
class GovernmentOrganizationMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the government organization mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase of an
    Indian Union Government Ministry or Department.
    """
    organization_mention_phrases: List[str]
    """
    List of potential Indian Union Government Ministry or Department mention phrases
    extracted directly from the input text.
    """

def create_government_organization_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting mentions of Indian Union Government
    Ministries and Departments in an input statement.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for government organization phrase highlighting.
    """

    government_organization_highlighting_task = Task(
        name="government_organization_phrase_highlighting",

        description="""
        Identify and extract meaningful phrases from the input statement that represent mentions of specific **Indian Union Government Ministries** or **Indian Union Government Departments**.
        Focus on extracting the official or commonly used names and acronyms of these specific governmental bodies.
        The goal is to capture the exact text segment that refers to the ministry or department entity.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted (highlighted) directly from the input statement. Each phrase represents a potential mention of an Indian Union Government Ministry or Department. These phrases are expected to be:

        - Specific to Government Bodies: Clearly referring to a named Ministry or Department within the Indian Union Government structure.
        - Contextually Relevant: Extracted as a meaningful unit from the text, potentially including acronyms if present.
        - **Directly and Exactly from Input**: The phrases MUST be extracted directly and exactly from the input text, preserving original wording, capitalization, and spelling. No modifications, additions, or interpretations are allowed.

        Example:

        Input Statement: "The initiative was launched by the Ministry of Education (MoE) in collaboration with the Department of Higher Education. Support was also provided by the Ministry of Finance. A key role was played by Dept. of Science & Technology."

        Expected Output List:
        ```
        [
        "Ministry of Education (MoE)",
        "MoE",
        "Department of Higher Education",
        "Ministry of Finance",
        "Dept. of Science & Technology"
        ]
        ```

        Key Considerations:

        - **Include Full Names and Acronyms:** Extract both full names (e.g., "Ministry of Education") and associated acronyms (e.g., "MoE") if they appear as distinct mentions referring to the entity.
        - **Capture Variations:** Include common variations or abbreviations if used in the text (e.g., "Dept. of Science & Technology").
        - **Focus on the Entity:** Extract only the phrase identifying the ministry or department itself. Do *not* include names of ministers (people), specific programs, policy names, or actions being taken by the ministry unless they are part of the official name.
        - **Exclude Generic Terms:** Avoid extracting generic phrases like "the ministry", "a department", "central government agency" unless they are part of a specific name being mentioned immediately (which is rare).
        - **Verbatim Extraction:** Reiteration: Copy the phrases *exactly* as they appear in the source text. Preserve capitalization and punctuation as found.
        """,

        agent=agent,

        async_execution=False,

        output_pydantic=GovernmentOrganizationMentionPhrasesOutput
    )

    return government_organization_highlighting_task