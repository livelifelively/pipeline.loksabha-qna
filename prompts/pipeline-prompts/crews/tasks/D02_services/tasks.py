from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Service task output
class ServiceMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the government service mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase describing the
    **nature or type** of an Indian Union Government Service.
    """
    service_mention_phrases: List[str]
    """
    List of potential phrases describing the **nature or type** of an
    Indian Union Government Service, extracted directly from the input text.
    """

def create_service_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that describe the **nature or type**
    of Indian Union Government Services in an input statement.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for service description phrase highlighting.
    """

    service_highlighting_task = Task(
        name="service_description_phrase_highlighting", # Renamed for clarity

        description="""
        Identify and extract meaningful phrases from the input statement that specifically describe the **nature, type, or category of service** being provided or offered by the government.
        Focus on **what kind of action or assistance** is being given (e.g., medical care, financial help, training, advisory).
        Critically, **distinguish this from the named Program or Scheme** that delivers the service (e.g., do not extract just 'PM-JAY' itself, but extract 'tertiary care hospitalization' which PM-JAY provides). Also, do NOT extract the resulting *benefits* or *outcomes* for the recipient.
        The goal is to capture the exact text segment describing the **core service activity or type**.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of the **nature or type of a government Service**. These phrases are expected to be:

        - Focused on Service Type/Nature: Clearly describing the *kind* of action, assistance, or offering (e.g., 'medical assistance', 'skill training', 'loan processing', 'quality audit').
        - Distinct from Programs/Schemes: Should not be *just* the name of a specific program or scheme (like 'PMKVY'), unless that name inherently describes the service type clearly and is used that way in the text. Focus on the descriptive part.
        - Distinct from Benefits: Should not describe the *outcome* or *value* for the recipient (e.g., 'better health', 'employment').
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example 1:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization."

        Expected Output List (Service Nature only):
        ```
        [
        "secondary and tertiary care hospitalization"
        ]
        ```
        (Explanation: 'AB-PMJAY' is the scheme name. 'health cover of Rs. 5 lakhs...' is arguably a benefit/metric. The core service *type* described is 'secondary and tertiary care hospitalization'.)


        Example 2:

        Input Statement: "The government offers skill development training under the PMKVY scheme. This includes vocational courses and certification. Beneficiaries receive financial assistance for enrollment and placement support services upon completion. The aim is improved employability and access to jobs."

        Expected Output List (Service Nature only):
        ```
        [
        "skill development training",
        "vocational courses",
        "certification",
        "financial assistance for enrollment",
        "placement support services"
        ]
        ```
        (Explanation: 'PMKVY scheme' is the scheme name, excluded. 'improved employability' and 'access to jobs' are benefits, excluded. The listed phrases describe the *types* of services offered.)

        Key Considerations:

        - **Focus on 'What Kind of Help/Action':** Extract phrases describing the service activity (training, hospitalization, assistance, support, processing, auditing, etc.).
        - **Exclude Program/Scheme Names:** Do *not* extract phrases that *only* name the program or scheme (e.g., "PM-JAY", "National Health Mission"). If the scheme name is part of a larger descriptive phrase *about the service type*, include the whole descriptive phrase.
        - **Exclude Benefits/Outcomes:** Do *not* include phrases describing the results or value (e.g., "improved health", "job creation", "economic growth").
        - **Exclude Metrics/Organizations:** Avoid simple metric values or organization names.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        **Handling Ambiguity:** If a phrase mixes service description with program name or benefit, try to extract *only the part describing the nature of the service*. If a phrase *only* names a program or *only* describes a benefit, do not include it.
        """,

        agent=agent,

        async_execution=False,

        output_pydantic=ServiceMentionPhrasesOutput
    )

    return service_highlighting_task