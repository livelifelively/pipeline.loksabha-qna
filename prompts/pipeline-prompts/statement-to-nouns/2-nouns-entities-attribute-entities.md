Analyze the provided statement and categorize its nouns as described below. Return the results in JSON format.

**Purpose:** This task is designed to extract key concepts from a statement and categorize them based on their role in representing knowledge. We are particularly interested in identifying specific _attributes_ that can themselves be treated as entities in a knowledge graph. This is useful when you need to track metadata or provenance information _about_ those attributes.

**Steps:**

1.  **Identify all nouns:** List all nouns in the statement.

2.  **Prioritize compound nouns:** If a noun is part of a compound noun (e.g., "health outcomes"), use the compound noun instead of its individual components ("health," "health").

3.  **Classify entities:** Identify which nouns represent specific, identifiable real-world entities (e.g., organizations, places, specific programs). These are concrete things you could potentially look up and find detailed information about.

4.  **Classify attribute_entities:** Identify nouns representing attributes or properties that describe the entities. In our knowledge graph, we want to represent these attributes _as entities themselves_ because we need to store additional information about them, such as:

    - The source of the attribute's value (e.g., a specific report or database)
    - The date the attribute was last updated
    - The method used to measure or calculate the attribute
    - The confidence level or reliability of the attribute's value

    Examples of `attribute_entities`: "Maternal Mortality Ratio (MMR)", "GDP growth rate," "Average test score." Treat an item as an `attribute_entity` if it's a quantifiable or qualitative characteristic that describes a core entity and _you need to store metadata about it_.

5.  **Identify potential entity pointers:** Determine which nouns, while not entities or attribute_entities themselves, could point to or contain information about specific entities or attribute_entities when the statement is answered (e.g., "initiatives," "reports," "details"). These are nouns that suggest the presence of further, more detailed information.

6.  **Classify remaining nouns:** Categorize any remaining nouns as either non-entity nouns or non-entity, non-potential entity pointer nouns. These are nouns that are more abstract or don't directly relate to identifiable things or information sources.

**JSON Output Format:**

```json
{
  "statement": "the original statement text",
  "nouns": ["list", "of", "all", "nouns"],
  "entities": ["list", "of", "entity", "nouns"],
  "attribute_entities": ["list", "of", "attribute_entity", "nouns"],
  "potential_entity_pointers": ["list", "of", "potential", "entity", "pointers"],
  "non_entity_nouns": ["list", "of", "non-entity", "nouns"],
  "non_entity_non_potential_entity_pointer_nouns": ["list", "of", "remaining", "nouns"]
}
```

**Example:**

**Input Statement:** "The World Health Organization (WHO) reports a decline in Maternal Mortality Ratio (MMR) in several African countries."

**Expected JSON Output:**

```json
{
  "statement": "The World Health Organization (WHO) reports a decline in Maternal Mortality Ratio (MMR) in several African countries.",
  "nouns": ["World Health Organization (WHO)", "Maternal Mortality Ratio (MMR)", "decline", "countries"],
  "entities": ["World Health Organization (WHO)", "countries"],
  "attribute_entities": ["Maternal Mortality Ratio (MMR)"],
  "potential_entity_pointers": [],
  "non_entity_nouns": ["decline"],
  "non_entity_non_potential_entity_pointer_nouns": ["decline"]
}
```
