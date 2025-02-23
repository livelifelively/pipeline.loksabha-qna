Analyze the provided statement and categorize its nouns as described below. Return the results in JSON format.

**Steps:**

1. **Identify all nouns:** List all nouns in the statement.

2. **Prioritize compound nouns:** If a noun is part of a compound noun (e.g., "health outcomes"), use the compound noun instead of its individual components ("health," "outcomes").

3. **Classify entities:** Identify which nouns represent specific, identifiable real-world entities (e.g., organizations, places, specific programs).

4. **Identify potential entity pointers:** Determine which nouns, while not entities themselves, could point to or contain information about specific entities when the statement is answered (e.g., "initiatives," "reports," "details").

5. **Classify remaining nouns:** Categorize any remaining nouns as either non-entity nouns or non-entity, non-potential entity pointer nouns.

**JSON Output Format:**

```json
{
  "statement": "the original statement text",
  "nouns": ["list", "of", "all", "nouns"],
  "entities": ["list", "of", "entity", "nouns"],
  "potential_entity_pointers": ["list", "of", "potential", "entity", "pointers"],
  "non_entity_nouns": ["list", "of", "non-entity", "nouns"],
  "non_entity_non_potential_entity_pointer_nouns": ["list", "of", "remaining", "nouns"]
}
```

Example Input Statement:

"whether the Government has launched specific initiatives under the National Health Mission (NHM) in Maharashtra and Bihar to improve maternal and infant health outcomes and if so, the details thereof;"

Example Output:

```json
{
  "statement": "whether the Government has launched specific initiatives under the National Health Mission (NHM) in Maharashtra and Bihar to improve maternal and infant health outcomes and if so, the details thereof;",
  "nouns": [
    "Government",
    "initiatives",
    "National Health Mission (NHM)",
    "Maharashtra",
    "Bihar",
    "health outcomes",
    "details"
  ],
  "entities": ["Government", "National Health Mission (NHM)", "Maharashtra", "Bihar"],
  "potential_entity_pointers": ["initiatives", "health outcomes", "details"],
  "non_entity_nouns": [],
  "non_entity_non_potential_entity_pointer_nouns": []
}
```
