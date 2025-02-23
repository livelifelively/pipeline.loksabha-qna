Analyze the provided statement and categorize its nouns as described below. Return the results in JSON format.

**Purpose:** This task is designed to extract key concepts from a statement and categorize them based on their role in representing knowledge. We are particularly interested in identifying both specific entities and the attributes that can be treated as entities in a knowledge graph. A key aspect of this task is to carefully examine combinations of adjectives and nouns, as these combinations often create more specific and meaningful concepts that should be considered for entity or potential entity pointer status.

**Steps:**

1.  **Identify all nouns and adjective+noun combinations:** List all nouns in the statement. _Pay special attention to instances where an adjective modifies a noun_. Treat adjective+noun pairs as a single unit of analysis (e.g., if you see "rural areas", consider it as a single term rather than just "areas").

2.  **Prioritize compound nouns:** If a noun or adjective+noun combination is part of a compound noun (e.g., "health outcomes," "primary health center"), use the compound noun instead of its individual components.

3.  **Classify entities:** Identify which nouns or adjective+noun combinations represent specific, identifiable real-world entities (e.g., organizations, places, specific programs). These are concrete things you could potentially look up and find detailed information about.

4.  **Classify attribute_entities:** Identify nouns or adjective+noun combinations representing attributes or properties that describe the entities. In our knowledge graph, we want to represent these attributes _as entities themselves_ because we need to store additional information about them, such as:

    - The source of the attribute's value
    - The date the attribute was last updated
    - The method used to measure or calculate the attribute
    - The confidence level or reliability of the attribute's value

    Examples of `attribute_entities`: "Maternal Mortality Ratio (MMR)", "GDP growth rate," "Average test score." Treat an item as an `attribute_entity` if it's a quantifiable or qualitative characteristic that describes a core entity and _you need to store metadata about it_.

5.  **Identify potential entity pointers:** Determine which nouns or adjective+noun combinations, while not entities or attribute_entities themselves, could point to or contain information about specific entities or attribute_entities when the statement is answered (e.g., "initiatives," "reports," "details," "rural clinics"). These are terms that suggest the presence of further, more detailed information. Remember, carefully consider adjective+noun combinations for this category.

6.  **Classify remaining nouns:** Categorize any remaining nouns as either non-entity nouns or non-entity, non-potential entity pointer nouns. These are nouns that are more abstract or don't directly relate to identifiable things or information sources.

**JSON Output Format:**

```json
{
  "statement": "the original statement text",
  "nouns": ["list", "of", "all", "nouns", "and", "adjective+noun", "combinations"],
  "entities": ["list", "of", "entity", "nouns", "and", "adjective+noun", "combinations"],
  "attribute_entities": ["list", "of", "attribute_entity", "nouns", "and", "adjective+noun", "combinations"],
  "potential_entity_pointers": [
    "list",
    "of",
    "potential",
    "entity",
    "pointers",
    "nouns",
    "and",
    "adjective+noun",
    "combinations"
  ],
  "non_entity_nouns": ["list", "of", "non-entity", "nouns"],
  "non_entity_non_potential_entity_pointer_nouns": ["list", "of", "remaining", "nouns"]
}
```

**Example:**

**Input Statement:** "The state government is investing in rural healthcare infrastructure."

**Expected JSON Output:**

```json
{
  "statement": "The state government is investing in rural healthcare infrastructure.",
  "nouns": ["state government", "rural healthcare infrastructure"],
  "entities": ["state government"],
  "attribute_entities": [],
  "potential_entity_pointers": ["rural healthcare infrastructure"],
  "non_entity_nouns": [],
  "non_entity_non_potential_entity_pointer_nouns": []
}
```
