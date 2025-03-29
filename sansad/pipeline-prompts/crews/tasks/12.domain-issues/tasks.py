from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Domain Issue task output
class DomainIssueMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the domain issue mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase identifying
    a specific problem, challenge, or negative situation within a policy domain.
    """
    domain_issue_mention_phrases: List[str]
    """
    List of potential phrases identifying specific domain issues, problems, challenges,
    or negative situations, extracted directly from the input text.
    """

def create_domain_issue_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that mention specific domain issues,
    problems, challenges, or negative situations relevant to public policy.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for domain issue phrase highlighting.
    """

    domain_issue_highlighting_task = Task(
        name="domain_issue_phrase_highlighting",

        description="""
        Identify and extract meaningful phrases from the input statement that explicitly describe **domain issues, problems, challenges, risks, negative trends, or undesirable situations** being discussed or addressed in a public policy context.
        Focus on capturing the specific wording used to articulate the problem. This can include both established named issues (e.g., "unemployment", "air pollution") and descriptive phrases (e.g., "lack of access to healthcare", "declining water table levels").

        **Distinguish Issues from Solutions/Goals:** Extract the problem ("high dropout rates"), not the goal ("improving retention") or the solution ("mid-day meal scheme").
        **Distinguish Issues from General Topics:** Extract the problem phrase ("inadequate road infrastructure"), not just the topic ("roads").
        **Handling Metrics:** Include phrases that use metrics to describe the issue (e.g., "high Maternal Mortality Rate", "low literacy levels"). Avoid extracting only the metric name (e.g., "MMR") unless used clearly as shorthand for the issue.

        **Do NOT extract:**
        - Policy objectives, goals, targets, solutions, services, benefits, programs.
        - Simple metric names or values in isolation.
        - Names of organizations, people, specific documents, regions (unless part of the issue description itself).
        - Neutral descriptions of situations; focus on phrases indicating a problem.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a **domain issue, problem, or challenge**. These phrases are expected to be:

        - Focused on Problems/Challenges: Clearly describing a negative situation, risk, or undesirable state (e.g., 'farmer suicides', 'lack of skilled workforce', 'high levels of pollution', 'poor sanitation coverage', 'threats to internal security', 'gender disparity in wages').
        - Specific: Identifying the particular issue mentioned in the text.
        - Includes Issue Descriptions Using Metrics: Captures phrases like "high unemployment rate" or "low immunization coverage".
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example:

        Input Statement: "Addressing the challenge of poor air quality in cities requires urgent action. Factors include vehicular emissions and industrial pollution. Furthermore, the high incidence of Non-Communicable Diseases (NCDs), linked partly to lifestyle factors, poses a significant burden. Another concern is the low agricultural productivity in certain regions, impacted by climate change and water scarcity. The government aims to improve farmer income."

        Expected Output List (Domain Issue Phrases only):
        ```
        [
        "challenge of poor air quality in cities",
        "poor air quality in cities",
        "vehicular emissions",
        "industrial pollution",
        "high incidence of Non-Communicable Diseases (NCDs)",
        "Non-Communicable Diseases (NCDs)",
        "NCDs",
        "significant burden",
        "low agricultural productivity in certain regions",
        "climate change",
        "water scarcity"
        ]
        ```
        (Explanation: Includes named issues like 'NCDs', descriptive problems like 'poor air quality', contributing factors presented as problems like 'vehicular emissions', impacts like 'significant burden', and issues described using metrics/levels like 'low agricultural productivity'. Excludes the goal 'improve farmer income'.)

        Key Considerations:

        - **Capture Problem Statements:** Extract phrases articulating a difficulty, challenge, risk, negative trend, or undesirable condition.
        - **Include Named & Descriptive Issues:** Capture both established issue names (NCDs, unemployment) and descriptive phrases ('lack of access...', 'high levels of...', 'poor quality of...').
        - **Contextual Metric Phrases:** Include phrases using metrics to describe the issue severity/level (e.g., "high unemployment rate", "low enrollment"). Exclude standalone metric names/values.
        - **Exclude Goals/Solutions:** Critically distinguish the problem from the desired outcome or the intervention.
        - **Exclude Neutral Topics:** Focus on phrases with negative connotation indicating a problem.
        - **Exclude Other Entities:** Do not extract names of programs, organizations, people, specific documents, etc., unless they are part of the issue description itself.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        """,

        agent=agent,

        async_execution=False,

        output_pydantic=DomainIssueMentionPhrasesOutput
    )

    return domain_issue_highlighting_task