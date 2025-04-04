# Main script to run the highlighting crew

import os
from typing import List
# Pydantic needs to be installed: pip install pydantic
from pydantic import BaseModel, Field
# CrewAI needs to be installed: pip install crewai crewai-tools
from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool
# LangChain Google GenAI needs to be installed: pip install langchain-google-genai
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. LLM Configuration (Google Gemini) ---
if "GOOGLE_API_KEY" not in os.environ:
    # Try to load from a .env file if python-dotenv is installed
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("GOOGLE_API_KEY not found in environment variables or .env file.")
    except ImportError:
         raise ValueError("GOOGLE_API_KEY environment variable not set. Please set your Google API Key.")
    except Exception as e:
        raise ValueError(f"Error loading .env file or GOOGLE_API_KEY missing: {e}")


try:
    # Use gemini-1.5-flash-latest for speed, or another available model
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        # Optional: configure temperature, top_p, etc.
        # temperature=0.5,
        # Optional: Add safety settings if needed
        # safety_settings=...
    )
    # Quick test to confirm connection (optional)
    # response = llm.invoke("Test: Say hi.")
    # print(f"LLM Connection Test Response: {response.content}")
    print("Google Gemini LLM configured successfully.")
except Exception as e:
    print(f"FATAL ERROR: Could not configure Google Gemini LLM: {e}")
    print("Please ensure your GOOGLE_API_KEY is correct and you have the necessary permissions.")
    exit() # Stop execution if LLM fails to load

# --- 2. Import Task Creation Functions ---
# (Ensure each target directory has an __init__.py file)
print("Importing task creation functions...")
try:
    # Using the D##_ directory names provided by the user
    from .tasks.D01_ministeries_departments.task import create_government_entity_highlighting_task
    from D02_services.task import create_service_highlighting_task
    from D03_benefits.task import create_benefit_highlighting_task
    from D04_programs.task import create_program_scheme_highlighting_task
    from D05_citizens.task import create_individual_citizen_attribute_highlighting_task
    from D06_citizen_groups.task import create_group_citizen_attribute_highlighting_task
    from D07_metrics.task import create_metric_highlighting_task
    from D08_government_officials.task import create_official_role_highlighting_task
    from D09_physical_digital_service_node.task import create_service_delivery_node_highlighting_task
    from D10_domain_issues.task import create_domain_issue_highlighting_task

    # Assuming Documents is #11 and Regions is #12 based on our task list
    # *** PLEASE VERIFY / ADJUST THESE PATHS/MODULES ***
    try:
        from D11_documents.task import create_document_highlighting_task
        print("- Document task function imported.")
    except ImportError:
        print("WARNING: Could not import 'create_document_highlighting_task' from 'D11_documents.task'.")
        def create_document_highlighting_task(agent): raise NotImplementedError("Document task function missing")

    try:
        from D12_regions.task import create_region_highlighting_task
        print("- Region task function imported.")
    except ImportError:
        print("WARNING: Could not import 'create_region_highlighting_task' from 'D12_regions.task'.")
        def create_region_highlighting_task(agent): raise NotImplementedError("Region task function missing")

    print("Task creation functions imported successfully.")

except ImportError as e:
    print(f"FATAL ERROR: Could not import one or more task creation functions.")
    print(f"Please ensure all task directories (D01 to D10, plus D11 and D12) exist,")
    print(f"contain a 'task.py' file with the correct function name,")
    print(f"and contain an empty '__init__.py' file.")
    print(f"Specific error: {e}")
    exit() # Stop execution if essential imports fail


# --- 3. Define Pydantic Output Models ---
# (Includes all 12 individual models + the final AllHighlightsOutput model)

class MetricMentionPhrasesOutput(BaseModel):
    metric_mention_phrases: List[str] = Field(default_factory=list, description="List of metric mention phrases.")
class GovernmentEntityMentionPhrasesOutput(BaseModel):
    government_entity_mention_phrases: List[str] = Field(default_factory=list, description="List of government entity mention phrases.")
class ServiceMentionPhrasesOutput(BaseModel):
    service_mention_phrases: List[str] = Field(default_factory=list, description="List of service mention phrases.")
class BenefitMentionPhrasesOutput(BaseModel):
    benefit_mention_phrases: List[str] = Field(default_factory=list, description="List of benefit mention phrases.")
class ProgramSchemeMentionPhrasesOutput(BaseModel):
    program_scheme_mention_phrases: List[str] = Field(default_factory=list, description="List of program/scheme mention phrases.")
class IndividualCitizenAttributeMentionPhrasesOutput(BaseModel):
    individual_citizen_attribute_mention_phrases: List[str] = Field(default_factory=list, description="List of individual citizen attribute mention phrases.")
class GroupCitizenAttributeMentionPhrasesOutput(BaseModel):
    group_citizen_attribute_mention_phrases: List[str] = Field(default_factory=list, description="List of group citizen attribute mention phrases.")
class DocumentMentionPhrasesOutput(BaseModel):
    document_mention_phrases: List[str] = Field(default_factory=list, description="List of document mention phrases.")
class RegionMentionPhrasesOutput(BaseModel):
    region_mention_phrases: List[str] = Field(default_factory=list, description="List of region mention phrases.")
class OfficialRoleMentionPhrasesOutput(BaseModel):
    official_role_mention_phrases: List[str] = Field(default_factory=list, description="List of official role mention phrases.")
class ServiceDeliveryNodeMentionPhrasesOutput(BaseModel):
    service_delivery_node_mention_phrases: List[str] = Field(default_factory=list, description="List of service delivery node mention phrases.")
class DomainIssueMentionPhrasesOutput(BaseModel):
    domain_issue_mention_phrases: List[str] = Field(default_factory=list, description="List of domain issue mention phrases.")

# Final Aggregated Output Model
class AllHighlightsOutput(BaseModel):
    """Pydantic model for the final aggregated output of all highlighting tasks."""
    metric_mention_phrases: List[str] = Field(default_factory=list, description="List of metric mention phrases.")
    government_entity_mention_phrases: List[str] = Field(default_factory=list, description="List of government entity mention phrases.")
    service_mention_phrases: List[str] = Field(default_factory=list, description="List of service mention phrases.")
    benefit_mention_phrases: List[str] = Field(default_factory=list, description="List of benefit mention phrases.")
    program_scheme_mention_phrases: List[str] = Field(default_factory=list, description="List of program/scheme mention phrases.")
    individual_citizen_attribute_mention_phrases: List[str] = Field(default_factory=list, description="List of individual citizen attribute mention phrases.")
    group_citizen_attribute_mention_phrases: List[str] = Field(default_factory=list, description="List of group citizen attribute mention phrases.")
    document_mention_phrases: List[str] = Field(default_factory=list, description="List of document mention phrases.")
    region_mention_phrases: List[str] = Field(default_factory=list, description="List of region mention phrases.")
    official_role_mention_phrases: List[str] = Field(default_factory=list, description="List of official role mention phrases.")
    service_delivery_node_mention_phrases: List[str] = Field(default_factory=list, description="List of service delivery node mention phrases.")
    domain_issue_mention_phrases: List[str] = Field(default_factory=list, description="List of domain issue mention phrases.")


# --- 4. Define Base Agent ---
class OntologySpecialistAgentDef: # Renamed slightly to avoid confusion
    def __init__(self, llm_instance):
        self.agent = Agent(
            role='Ontology Specialist',
            goal='Accurately identify and extract specific types of entity mentions from text based on precise instructions and ontology definitions.',
            backstory=(
                "An expert in semantic analysis and knowledge representation, adept at "
                "parsing documents to identify concepts defined within specific ontological frameworks. "
                "Meticulous in following instructions to highlight text segments corresponding "
                "to predefined entity types like metrics, organizations, roles, locations, etc."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm_instance # Use the passed LLM instance
        )

    def get_agent(self):
        return self.agent

# --- 5. Define Aggregator Agent ---
class OutputAggregatorAgentDef: # Renamed slightly
    def __init__(self, llm_instance):
        self.agent = Agent(
            role='Result Aggregator',
            goal='Combine the outputs from multiple parallel highlighting tasks into a single, structured final report.',
            backstory=(
                "A meticulous coordinator responsible for gathering structured data outputs "
                "from various specialist tasks. Ensures all data points are correctly compiled "
                "into the required final format without loss or modification, using provided tools."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm_instance # Use the passed LLM instance
        )

    def get_agent(self):
        return self.agent


# --- 6. Define Aggregation Tool ---
class AggregationTool(BaseTool):
    name: str = "AggregationTool"
    description: str = "Aggregates highlighting results from multiple tasks based on their outputs available in the context."

    def _run(self, **kwargs) -> dict:
        """
        Accesses the outputs of prerequisite tasks from the agent's context
        and aggregates them into the AllHighlightsOutput structure.
        """
        print("--- Aggregation Tool Running ---")
        # Access context - ** This remains the most likely part needing adjustment **
        # Depending on CrewAI version, context might be directly in kwargs,
        # or need accessing via agent's memory, or passed differently.
        # Assuming context holds outputs keyed by task or a shared dict.
        context = kwargs.get('context', {})
        tasks_outputs = getattr(context, '_tasks_output', None) # CrewAI internal? Check docs.
        # Alternative: Loop through expected context tasks if passed explicitly
        # context_tasks = kwargs.get('context_tasks_list', [])

        # Helper function to safely get list
        def get_phrases(task_output_data, key_name):
            data = {}
            if isinstance(task_output_data, BaseModel):
                data = task_output_data.model_dump() # Use model_dump() for Pydantic v2
            elif isinstance(task_output_data, dict):
                data = task_output_data
            elif isinstance(task_output_data, str):
                 # Attempt to parse if LLM returned raw JSON string
                try:
                    import json
                    data = json.loads(task_output_data)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse task output string: {task_output_data}")
                    return []
            else:
                print(f"Warning: Unexpected data type for task output: {type(task_output_data)}")
                return []

            return data.get(key_name, [])

        # Extract results based on the task context structure
        # --- This section requires careful validation with actual CrewAI execution ---
        # --- It assumes task outputs are accessible via the context object somehow ---
        # --- Using placeholder keys based on task variable names for now ---
        # --- Adjust based on how CrewAI populates context for tools ---
        aggregated_data = {
            "metric_mention_phrases": get_phrases(context.get('metric_task'), 'metric_mention_phrases'),
            "government_entity_mention_phrases": get_phrases(context.get('gov_entity_task'), 'government_entity_mention_phrases'),
            "service_mention_phrases": get_phrases(context.get('service_task'), 'service_mention_phrases'),
            "benefit_mention_phrases": get_phrases(context.get('benefit_task'), 'benefit_mention_phrases'),
            "program_scheme_mention_phrases": get_phrases(context.get('program_task'), 'program_scheme_mention_phrases'),
            "individual_citizen_attribute_mention_phrases": get_phrases(context.get('ind_attr_task'), 'individual_citizen_attribute_mention_phrases'),
            "group_citizen_attribute_mention_phrases": get_phrases(context.get('grp_attr_task'), 'group_citizen_attribute_mention_phrases'),
            "document_mention_phrases": get_phrases(context.get('doc_task'), 'document_mention_phrases'),
            "region_mention_phrases": get_phrases(context.get('region_task'), 'region_mention_phrases'),
            "official_role_mention_phrases": get_phrases(context.get('role_task'), 'official_role_mention_phrases'),
            "service_delivery_node_mention_phrases": get_phrases(context.get('node_task'), 'service_delivery_node_mention_phrases'),
            "domain_issue_mention_phrases": get_phrases(context.get('issue_task'), 'domain_issue_mention_phrases'),
        }

        # Validate and return
        try:
            validated_output = AllHighlightsOutput(**aggregated_data)
            # Return as dict for CrewAI compatibility if needed
            return validated_output.model_dump()
        except Exception as e:
            print(f"ERROR in AggregationTool Pydantic validation: {e}")
            return {"error": "Aggregation failed Pydantic validation", "details": str(e), "raw_data": aggregated_data}

aggregation_tool = AggregationTool()
print("Aggregation tool defined.")

# --- 7. Instantiate Agents ---
print("Instantiating agents...")
# Create 12 specialist instances + 1 aggregator
specialist_agent_def = OntologySpecialistAgentDef(llm)
specialist_agents = [specialist_agent_def.get_agent() for _ in range(12)]

aggregator_agent_def = OutputAggregatorAgentDef(llm)
aggregator_agent = aggregator_agent_def.get_agent()
aggregator_agent.tools = [aggregation_tool] # Assign tool
print(f"{len(specialist_agents)} specialist agents and 1 aggregator agent instantiated.")


# --- 8. Instantiate Tasks using IMPORTED functions ---
print("Instantiating tasks...")
try:
    task_functions = [
        create_metric_highlighting_task,               # Corresponds to agent[0]
        create_government_entity_highlighting_task,    # Corresponds to agent[1]
        create_service_highlighting_task,              # Corresponds to agent[2]
        create_benefit_highlighting_task,              # Corresponds to agent[3]
        create_program_scheme_highlighting_task,       # Corresponds to agent[4]
        create_individual_citizen_attribute_highlighting_task, # Corresponds to agent[5]
        create_group_citizen_attribute_highlighting_task,    # Corresponds to agent[6]
        create_document_highlighting_task,             # Corresponds to agent[7]
        create_region_highlighting_task,               # Corresponds to agent[8]
        create_official_role_highlighting_task,        # Corresponds to agent[9]
        create_service_delivery_node_highlighting_task,# Corresponds to agent[10]
        create_domain_issue_highlighting_task          # Corresponds to agent[11]
    ]

    all_highlighting_tasks = []
    task_context_keys = {} # To map task object to a key for the tool context if needed

    for i, func in enumerate(task_functions):
        task = func(specialist_agents[i]) # Assign task to corresponding agent instance
        task.async_execution = True
        all_highlighting_tasks.append(task)
        task_context_keys[task] = f"{func.__name__.replace('create_', '').replace('_highlighting_task','')}_task" # e.g., 'metric_task'

    print(f"{len(all_highlighting_tasks)} highlighting tasks instantiated and set to async.")

    # Aggregation Task
    # The description needs to tell the agent HOW to use the tool and access context.
    # This might involve instructing it to look for specific keys based on the context tasks.
    context_task_names = list(task_context_keys.values()) # Get the keys the tool might need
    aggregate_results_task = Task(
        description=(
            f"Aggregate the results from the {len(all_highlighting_tasks)} preceding highlighting tasks. "
            f"Use the AggregationTool tool to perform this combination. "
            f"The tool will need access to the outputs of the following tasks from context: {', '.join(context_task_names)}. "
            f"Ensure the tool is called correctly to produce the final structured output."
        ),
        expected_output="A single JSON object conforming to the AllHighlightsOutput model, containing aggregated lists of phrases from all input tasks. Use the AggregationTool.",
        agent=aggregator_agent,
        context=all_highlighting_tasks, # Make prior task outputs available
        output_pydantic=AllHighlightsOutput,
        tools=[aggregation_tool] # Make tool available
    )
    print("Aggregation task instantiated.")

except Exception as e:
    print(f"FATAL ERROR during task instantiation: {e}")
    exit()

# --- 9. Assemble and Run Crew ---
print("Assembling Crew...")
highlighting_crew = Crew(
    agents=specialist_agents + [aggregator_agent], # Combine agent lists
    tasks=all_highlighting_tasks + [aggregate_results_task], # Combine task lists
    process=Process.hierarchical, # Manager LLM coordinates flow (may need separate config)
    # memory=True # Optional: If context needs to be explicitly managed across tasks
    verbose=2 # Use 1 for less noise, 2 for detailed logs
)
print("Crew assembled.")

# --- 10. Example Kickoff ---
if __name__ == "__main__":
    # Replace with your actual document chunk
    text_chunk_example = """
    The Pradhan Mantri Jan Arogya Yojana (PMJAY) provides health cover of Rs. 5 lakhs.
    This service, managed by the National Health Authority (NHA), targets poor families.
    The District Collector monitors implementation via the district portal. Key challenges
    include low awareness in rural areas. Guidelines were issued by the Ministry of Health.
    The UMANG app also lists scheme details. Unemployment remains a key domain issue.
    """

    inputs = {'text_chunk': text_chunk_example} # Input key should match task {variable}

    print("\n--- Starting Crew Execution ---")
    # Note: Crew execution can take time, especially with multiple LLM calls
    result = None
    try:
        result = highlighting_crew.kickoff(inputs=inputs)
    except Exception as e:
        print(f"\n--- ERROR during Crew kickoff: {e} ---")
        # Potentially log more details about the crew state if possible
        # print(f"Crew usage metrics: {highlighting_crew.usage_metrics}")

    print("\n--- Crew Execution Finished ---")
    print("Final Result Received from Crew:")
    print(result)

    # Validate the final result structure
    if result:
        try:
            # If the result is already the Pydantic object (CrewAI might return this)
            if isinstance(result, AllHighlightsOutput):
                 final_output = result
                 print("\nValidated Output (Pydantic Model received directly):")
                 print(final_output.model_dump_json(indent=2))
            # If result is dict or string needing validation
            elif isinstance(result, (dict, str)):
                if isinstance(result, str):
                     # Try parsing if it looks like JSON
                     try:
                         import json
                         result_dict = json.loads(result)
                     except json.JSONDecodeError:
                         print("\nWarning: Final result is an unparsable string.")
                         result_dict = None
                else:
                    result_dict = result

                if result_dict and "error" not in result_dict: # Check if tool returned error
                    final_output = AllHighlightsOutput(**result_dict)
                    print("\nValidated Output (Pydantic Model from dict/str):")
                    print(final_output.model_dump_json(indent=2)) # Pretty print JSON
                elif result_dict and "error" in result_dict:
                     print(f"\nError: Aggregation Tool reported an error: {result_dict}")
                else:
                    print("\nWarning: Final result is not a valid dictionary or could not be parsed.")

        except Exception as e:
            print(f"\nError validating final result against AllHighlightsOutput: {e}")
            print(f"Raw result was: {result}")
    else:
        print("\nNo result returned from crew execution.")