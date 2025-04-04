Analyze the provided statement and categorize its concepts as described below. Return the results in JSON format.

**Purpose:** This task extracts key concepts from a statement and categorizes them based on their role in representing knowledge. The goal is to identify entities, attribute entities, and potential pointers to further information. A critical component is recognizing that adjective+noun combinations often create more specific and meaningful concepts. Therefore, we will explicitly identify these combinations before classifying the concepts.

**Steps:**

1.  **Identify all nouns:** List all nouns present in the statement.

2.  **Identify adjective+noun combinations:** Examine the statement and identify any instances where an adjective directly modifies a noun. Treat each adjective+noun pair as a single, combined unit (e.g., "rural areas"). If a noun is part of an identified adjective+noun combination, _do not_ include it as a separate noun in the `"nouns"` list. This list should only contain _single_ nouns.

3.  **Prioritize compound nouns/combinations:** If a single noun or adjective+noun combination is part of a larger compound noun (e.g., "health outcomes", "primary health center", "community health worker"), use the _entire compound noun_ in the appropriate category rather than its individual components.

4.  **Classify entities:** Determine which single nouns or adjective+noun combinations represent specific, identifiable, real-world entities (e.g., organizations, places, defined programs). These are concrete things you could potentially look up and find detailed information about.

5.  **Classify attribute entities:** Determine which single nouns or adjective+noun combinations represent attributes or properties that describe the entities. These are characteristics you might want to track or measure, potentially along with their sources and update dates.

6.  **Identify potential entity pointers:** Determine which single nouns or adjective+noun combinations, while not entities or attribute entities themselves, could point to or contain information _about_ specific entities or attribute entities when the statement is answered (e.g., "initiatives", "details", "reports", "rural clinics").

7.  **Classify remaining nouns:** Categorize any remaining _single nouns_ as either non-entity nouns or non-entity, non-potential entity pointer nouns. These are nouns that are more abstract or don't directly relate to identifiable things or information sources.

**JSON Output Format:**

```json
{
  "statement": "the original statement text",
  "nouns": ["list", "of", "all", "single", "nouns"],
  "adjective_noun_combinations": ["list", "of", "all", "adjective_noun", "combinations"],
  "entities": ["list", "of", "entity", "nouns", "and", "adjective_noun", "combinations"],
  "attribute_entities": ["list", "of", "attribute_entity", "nouns", "and", "adjective_noun", "combinations"],
  "potential_entity_pointers": [
    "list",
    "of",
    "potential",
    "entity",
    "pointers",
    "nouns",
    "and",
    "adjective_noun",
    "combinations"
  ],
  "non_entity_nouns": ["list", "of", "non-entity", "single", "nouns"],
  "non_entity_non_potential_entity_pointer_nouns": ["list", "of", "remaining", "single", "nouns"]
}
```
