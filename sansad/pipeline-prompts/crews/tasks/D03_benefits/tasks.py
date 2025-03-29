from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Benefit task output
class BenefitMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the government benefit mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase describing the
    **benefit, outcome, or value received** by beneficiaries of government services.
    """
    benefit_mention_phrases: List[str]
    """
    List of potential phrases describing the **benefit, outcome, or value received**
    from government services, extracted directly from the input text.
    """

def create_benefit_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that describe the **benefits, outcomes,
    or positive effects** for recipients of Indian Union Government Services.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for benefit phrase highlighting.
    """

    benefit_highlighting_task = Task(
        name="benefit_phrase_highlighting",

        description="""
        Identify and extract meaningful phrases from the input statement that specifically describe the **benefits, outcomes, positive effects, or value received** by beneficiaries as a result of government services or schemes.
        Focus on **what positive change or value the recipient gains**. Do NOT extract phrases describing the service/action itself (that is handled by a separate task).
        The goal is to capture the exact text segment describing the benefit.
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a **Benefit** (the outcome or value received). These phrases are expected to be:

        - Focused on Outcome/Value: Clearly describing the positive result, advantage, or value gained by the beneficiary (e.g., 'improved health', 'job opportunities', 'financial security', 'access to education').
        - Distinct from Services/Actions: Should not describe the government's action or offering itself (e.g., 'skill training', 'hospitalization').
        - Specific where possible: Referring to a particular benefit mentioned.
        - Can Include Quantitative Aspects: Phrases describing benefits might include quantitative details if they define the benefit itself (e.g., 'health cover of Rs. 5 lakhs per family per year' describes the value/benefit).
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example 1:

        Input Statement: "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) provides health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization, leading to reduced out-of-pocket expenditure and improved access to quality healthcare."

        Expected Output List (Benefit Phrases only):
        ```
        [
        "health cover of Rs. 5 lakhs per family per year",
        "reduced out-of-pocket expenditure",
        "improved access to quality healthcare"
        ]
        ```
        (Explanation: 'secondary and tertiary care hospitalization' is the service, excluded. The listed phrases describe the value gained by the beneficiary.)


        Example 2:

        Input Statement: "The government offers skill development training under the PMKVY scheme... Beneficiaries receive financial assistance for enrollment and placement support services upon completion. The aim is improved employability and access to jobs."

        Expected Output List (Benefit Phrases only):
        ```
        [
        "improved employability",
        "access to jobs"
        ]
        ```
        (Explanation: 'skill development training', 'financial assistance for enrollment', 'placement support services' are services, excluded. The listed phrases describe the intended positive outcomes.)

        Key Considerations:

        - **Focus on 'What is Gained/Achieved':** Extract phrases describing the positive result for the beneficiary.
        - **Exclude Service Descriptions:** Do *not* include phrases describing the government's action or offering (training, providing care, processing applications etc.).
        - **Quantitative Benefits OK:** Unlike the Service task, benefit descriptions *can* include metric-like details if they quantify the benefit itself (e.g., the amount of health cover).
        - **Verbatim Extraction:** Copy phrases *exactly*.

        **Handling Ambiguity:** If a phrase mixes service description with benefit, try to extract *only the part describing the benefit or outcome*. If a phrase *only* describes a service action or *only* names a program, do not include it.
        """,

        agent=agent,

        async_execution=False,

        output_pydantic=BenefitMentionPhrasesOutput
    )

    return benefit_highlighting_task