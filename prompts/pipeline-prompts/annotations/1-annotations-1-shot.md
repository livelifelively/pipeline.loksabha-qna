"Your task is to convert the given text statement into a structured JSON annotation for a knowledge graph.

**Text Statement:**
As per the Special Bulletin on Maternal Mortality Ratio (MMR) released by the Sample Registration System (SRS) 2018-20, the MMR of Maharashtra has been reduced from 61 per lakh live births in 2014-16 to 33 per lakh live births in 2018-20 and MMR of Bihar has been reduced from 165 per lakh live births in 2014-16 to 118 per lakh live births in 2018-20.

**Desired JSON Annotation Structure:**

The JSON annotation should have the following top-level keys: 'text', 'entities', and 'relationships'.

- **'text'**: An array containing the input text statement as a single string.

- **'entities'**: A JSON object containing different entity types as keys. The entity types you should consider are:

  - **'metrics'**: For defined health metrics like 'Maternal Mortality Ratio' (MMR). Each entity should have: 'id', 'names' (array of names), 'description'.
  - **'regions'**: For geographical regions like countries, states, or global regions. Each entity should have: 'id', 'names' (array of names), 'description', 'type' (e.g., 'country', 'state', 'world'), 'country' (if applicable).
  - **'source_documents'**: For reports, bulletins, or documents that are sources of information. Each entity should have: 'id', 'names' (array of names), 'description', 'type' (e.g., 'report', 'bulletin'), 'url' (if available).
  - **'service_nodes'**: For organizations or systems providing services. Each entity should have: 'id', 'names' (array of names), 'description', 'type' (e.g., 'service_node', 'organization').
  - You may suggest **NEW ENTITY TYPES** if you identify concepts in the text that don't fit into these predefined types. If no suitable type is found, use 'miscellaneous_entities'.

- **'relationships'**: A JSON object with a 'data' array. Each element in 'data' represents a relationship between entities and should have:
  - 'description': A human-readable description of the relationship (e.g., 'percentage change measurement of maternal mortality rate in india in period of 1995-2025').
  - 'entities': A JSON object specifying the entities involved in the relationship. Use the entity type names (e.g., 'regions', 'metrics') as keys, and within each, use the 'id' of the corresponding entity.

**Instructions:**

1. **Analyze the Text Statement:** Carefully read and understand the provided text statement.
2. **Identify Entities:** Extract all relevant entities from the text and classify them into the entity types defined above ('metrics', 'regions', 'source_documents', 'service_nodes', or suggest NEW types if needed).
3. **Create Entity JSON:** For each identified entity, create a JSON object with the required fields ('id', 'names', 'description', and type-specific fields as described above). Ensure 'id's are unique and descriptive.
4. **Extract Relationships:** Identify the relationships between the extracted entities.
5. **Create Relationship JSON:** For each relationship, create a JSON object with a clear 'description' and an 'entities' object linking to the 'id's of the involved entities, categorized by their entity types.
6. **Structure as JSON:** Assemble all the entity JSON objects under the 'entities' section (grouped by entity type) and all relationship JSON objects under the 'relationships' -> 'data' section. Wrap the input text in the 'text' array.
7. **Output JSON:** Return the complete annotation as a single, valid JSON object.

**Example of Desired Output Format (Illustrative - You can provide a snippet of your Data2 example here to be even clearer):**

```json
{
  "text": [ ... ],
  "entities": {
    "metrics": { ... },
    "source_documents": { ... },
    "regions": { ... },
    ... (other entity types) ...
  },
  "relationships": {
    "data": [ ... ]
  }
}
```
