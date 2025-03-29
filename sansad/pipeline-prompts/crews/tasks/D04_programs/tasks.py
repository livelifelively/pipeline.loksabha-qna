from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Program/Scheme task output
class ProgramSchemeMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the government program/scheme/mission
    mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase of an
    Indian Union Government Program, Scheme, or Mission name.
    """
    program_scheme_mention_phrases: List[str]
    """
    List of potential Indian Union Government Program, Scheme, or Mission name
    mention phrases extracted directly from the input text.
    """

def create_program_scheme_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting mentions of Indian Union Government
    Program, Scheme, or Mission names in an input statement.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for program/scheme name highlighting.
    """

    program_scheme_highlighting_task = Task(
        name="program_scheme_name_phrase_highlighting",

        description="""
        Identify and extract phrases from the input statement that represent the specific **names of Indian Union Government Programs, Schemes, or Missions**.
        Focus strictly on capturing the official or commonly used **name** of the initiative itself.
        Do NOT extract descriptions of the services offered, the benefits received, or the names of ministries/departments running the program (these are handled by separate tasks).
        The goal is to capture the exact text segment that functions as the **proper name** of the program/scheme/mission.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a government **Program, Scheme, or Mission Name**. These phrases are expected to be:

        - Focused on the Name: Clearly identifying a specific, named government initiative (Program, Scheme, Mission, Yojana, Abhiyan, etc.).
        - Includes Acronyms: Capture both full names and acronyms if used in the text to refer to the initiative.
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording, capitalization, and spelling. No modifications allowed.

        Example:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides health cover. The Ministry of Health oversees the National Health Mission (NHM). Another key initiative is the Pradhan Mantri Kaushal Vikas Yojana (PMKVY) which focuses on skill development. Enrollment in PMKVY has increased."

        Expected Output List (Program/Scheme Names only):
        ```
        [
        "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
        "AB-PMJAY",
        "National Health Mission (NHM)",
        "NHM",
        "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
        "PMKVY"
        ]
        ```

        Key Considerations:

        - **Extract Only the Name:** Capture the identifying name or acronym. If the name is presented with the acronym (e.g., "National Health Mission (NHM)"), extract that full phrase *and* potentially the standalone acronym ("NHM") if used separately later in the text.
        - **Exclude Descriptions:** Do *not* extract descriptive text about what the program does (e.g., "provides health cover", "focuses on skill development"). These are Services or Benefits.
        - **Exclude Organizations:** Do *not* extract the names of Ministries or Departments (e.g., "Ministry of Health").
        - **Exclude Generic Terms:** Avoid extracting generic phrases like "the scheme", "this program", "the mission", "the initiative" unless they are verifiably part of a specific, longer proper name being mentioned.
        - **Verbatim Extraction:** Copy phrases *exactly* as they appear.

        **Handling Ambiguity:** The main task is identifying text segments used as *proper nouns* for government initiatives. If a phrase describes *what* is done or *who* benefits, it belongs elsewhere. If it names the *implementing body*, it belongs elsewhere. Extract only the name of the initiative itself.
        """,

        agent=agent,

        async_execution=False,

        output_pydantic=ProgramSchemeMentionPhrasesOutput
    )

    return program_scheme_highlighting_task