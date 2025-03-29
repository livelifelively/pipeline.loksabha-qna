from crewai import Task
from typing import List
from pydantic import BaseModel

# Define the Pydantic model for the Service Delivery Node task output
class ServiceDeliveryNodeMentionPhrasesOutput(BaseModel):
    """
    Pydantic model for the output of the service delivery node mention phrase extraction task.

    Contains a list of strings, each being a potential mention phrase identifying
    a specific channel, platform, facility, or method for service delivery.
    """
    service_delivery_node_mention_phrases: List[str]
    """
    List of potential phrases identifying specific service delivery nodes
    (e.g., CSCs, websites, mobile apps, physical offices, door-to-door methods)
    extracted directly from the input text.
    """

def create_service_delivery_node_highlighting_task(agent):
    """
    Creates a CrewAI Task for highlighting phrases that mention specific channels,
    platforms, facilities, or methods used for government service delivery.

    Args:
        agent: The CrewAI Agent that will be assigned this task.

    Returns:
        Task: A CrewAI Task object configured for service delivery node phrase highlighting.
    """

    service_delivery_node_highlighting_task = Task(
        name="service_delivery_node_phrase_highlighting",

        description="""
        Identify and extract phrases from the input statement that represent specific **service delivery nodes, channels, platforms, or facilities**.
        This includes mentions of:
        - Specific named centers/facilities (e.g., "Common Service Centres (CSCs)", "Passport Seva Kendra", "District e-Governance Society office", "Anganwadi Centre")
        - Specific digital platforms (e.g., "UMANG mobile app", "MyGov website", "e-District portal", "DigiLocker")
        - Specific instances including location/identifiers (e.g., "CSC in Anapur village", "Passport Seva Kendra, Delhi", "the website passport.gov.in")
        - Generic types of delivery channels when mentioned as the specific means of access/delivery (e.g., "services available via the mobile app", "application submitted through the website", "information disseminated via SMS", "door-to-door delivery", "at designated physical offices").
        - Delivery methods involving specific personnel (e.g., "door-to-door delivery by ASHA workers", "support provided via Anganwadi Centres").

        Focus strictly on the **channel, platform, facility, or method** used for delivery/access.
        **Do NOT extract:**
        - The service/benefit/program itself.
        - The managing organization (Ministry/Department).
        - Role titles in isolation (extract "ASHA workers" only if part of a delivery method phrase like "delivered by ASHA workers").
        - Standalone region/location names (unless part of a specific node instance name).
        """,

        expected_output="""
        A list of strings, where each string is a phrase extracted directly from the input statement representing a potential mention of a **specific service delivery node, channel, platform, or facility**. These phrases are expected to be:

        - Focused on Delivery Channel/Node: Clearly identifying how or where a service is delivered or accessed (e.g., 'Common Service Centres', 'UMANG app', 'passport.gov.in website', 'door-to-door delivery', 'designated physical offices').
        - Includes Specific Names & Types: Captures both named nodes (CSCs, specific websites/apps) and specific types of channels used (mobile app, website, SMS, door-to-door).
        - Includes Instances: Captures specific instances if mentioned with identifiers or locations (e.g., 'CSC in Anapur village', 'Passport Seva Kendra, Delhi').
        - **Directly and Exactly from Input**: MUST be extracted directly and exactly from the input text, preserving original wording. No modifications allowed.

        Example:

        Input Statement: "Citizens can apply for passports via the Passport Seva Kendra (PSK) network or through the official website passport.gov.in. Information is also available on the mPassport Seva mobile app. For rural services, Common Service Centres (CSCs) established in villages like Anapur provide assistance. Health outreach involves door-to-door delivery by ASHA workers coordinated from the local Anganwadi Centre."

        Expected Output List (Service Delivery Node Phrases only):
        ```
        [
        "Passport Seva Kendra (PSK) network",
        "PSK",
        "official website passport.gov.in",
        "website passport.gov.in",
        "mPassport Seva mobile app",
        "mobile app",
        "Common Service Centres (CSCs)",
        "CSCs",
        "CSCs established in villages like Anapur",
        "door-to-door delivery by ASHA workers",
        "local Anganwadi Centre",
        "Anganwadi Centre"
        ]
        ```
        (Explanation: Includes named nodes (PSK, CSC, Anganwadi Centre), specific website/app names, generic channel types mentioned ('mobile app'), and delivery methods ('door-to-door delivery by ASHA workers'). Excludes standalone location 'Anapur' but includes 'CSCs established in villages like Anapur'. Excludes standalone role 'ASHA workers' but includes the delivery method phrase.)

        Key Considerations:

        - **Capture Channel/Platform/Facility:** Extract phrases identifying the means of delivery (physical center, website, app, mobile van, human delivery method like door-to-door).
        - **Include Specific & Generic Types:** Capture named instances (PSK, CSC) and specific types mentioned as channels (website, mobile app, SMS, door-to-door).
        - **Handle Location Contextually:** Include location names *only* if part of the specific node's identifying phrase (e.g., "PSK, Delhi", "CSC in village X").
        - **Handle Roles Contextually:** Extract role titles *only* when part of a phrase describing the delivery method (e.g., "delivered by ASHA workers"). Do not extract the role title alone.
        - **Exclude Other Entities:** Do not extract Service names, Benefit names, Program names, Organization names (unless part of node name), standalone Role titles, standalone Region names.
        - **Verbatim Extraction:** Copy phrases *exactly*.

        """,

        agent=agent,

        async_execution=False,

        output_pydantic=ServiceDeliveryNodeMentionPhrasesOutput
    )

    return service_delivery_node_highlighting_task