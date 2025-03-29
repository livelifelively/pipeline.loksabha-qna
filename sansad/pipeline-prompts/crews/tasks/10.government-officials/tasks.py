from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Official Role task output
class OfficialRoleMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the official role mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase identifying
    a specific government official role title or designation.
    """
    official_role_mention_phrases: List[str]
    """
    List of potential phrases identifying specific government official role titles
    (e.g., Minister, Secretary, Collector, MP, Judge, ASHA, Sarpanch)
    extracted directly from the input text.
    """

def create_official_role_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that mention specific titles or
    designations of government officials or functionaries at any level.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for official role phrase highlighting.
    """

    official_role_highlighting_task = Task(
        name="official_role_phrase_highlighting",

        description="""
        Identify and extract phrases from the input statement that represent the specific **titles or designations of government officials or functionaries**.
        This includes roles at all levels (Union, State, District, Block, Panchayat, Village, Municipal, etc.) and across all branches and functions (e.g., Political Leaders, Bureaucrats, Legislative Representatives, Judicial Officers, Scheme Delivery Agents like ASHA/Anganwadi workers, Law Enforcement).
        Focus **strictly** on extracting the **job title or official role name** itself.

        **Crucially, do NOT extract:**
        -   **Personal Names:** If text says "Prime Minister Modi", extract only "Prime Minister".
        -   **Organization Names:** If text says "Secretary, Ministry of Finance", extract only "Secretary". If text says "Mumbai Police", do not extract it (that's an organization). If text says "Police Constable", extract "Police Constable".
        -   **Generic Terms:** Avoid vague terms like "the official", "government staff", "an employee" unless part of a more specific title.
        -   **Actions/Descriptions:** Do not extract what the official does, only their title.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a **specific official government role title or designation**. These phrases are expected to be:

        - Focused on Role Titles: Clearly identifying a specific position or designation (e.g., 'Prime Minister', 'Chief Secretary', 'District Magistrate', 'Member of Parliament', 'High Court Judge', 'ASHA worker', 'Village Sarpanch', 'Anganwadi Worker', 'Tehsildar', 'Police Inspector').
        - Excludes Names & Organizations: Must NOT be a personal name or an organization/department name. Extract only the role component.
        - Covers All Levels/Types: Includes roles from national level down to village level, across legislative, executive, judicial, and program implementation functions.
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording, capitalization, and spelling. No modifications allowed.

        Example:

        Input Statement: "The decision was approved by the Prime Minister after consultation with the Finance Minister and the Chief Secretary. The District Collector reviewed the report submitted by the Tehsildar. Local implementation involves ASHA workers and the Village Sarpanch. The local Member of Parliament, Smt. X, also visited."

        Expected Output List (Official Role Titles only):
        ```
        [
        "Prime Minister",
        "Finance Minister",
        "Chief Secretary",
        "District Collector",
        "Tehsildar",
        "ASHA workers",
        "Village Sarpanch",
        "Member of Parliament"
        ]
        ```
        (Explanation: Includes various role titles across levels. Excludes personal names like "Smt. X" and generic terms. Extracts only the title part.)


        Key Considerations:

        - **Capture Specific Title:** Extract the most specific title mentioned (e.g., "Cabinet Secretary" > "Secretary" if specified).
        - **Isolate Title from Name/Org:** If a role is mentioned alongside a person's name or organization, extract *only* the role title phrase itself (e.g., from "Secretary John Doe of Dept X", extract "Secretary").
        - **Include Scheme-Specific Roles:** Capture roles like "ASHA worker", "Anganwadi Worker", "Rozgar Sevak" if mentioned.
        - **Include Local Roles:** Capture "Sarpanch", "Panchayat Secretary", "Municipal Councillor", "Patwari", "Block Development Officer", etc.
        - **Exclude Organizations:** Do not extract "Police Department", "District Court", "Ministry of Health". Extract roles within them like "Police Constable", "Judge", "Secretary".
        - **Exclude Generic Nouns:** Avoid "government", "administration", "judiciary", "officials" unless part of a specific title.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        """,

        agent=agent,

        async_execution=False,

        output_pydantic=OfficialRoleMentionPhrasesOutput
    )

    return official_role_highlighting_task