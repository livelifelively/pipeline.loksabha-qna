You are an expert in text annotation for healthcare program analysis. Your task is to take a single sentence or short paragraph related to healthcare programs and convert it into structured JSON data in the `annotationData` format.

The `annotationData` format is a JSON array where each element represents an annotated text segment and has the following structure:

```json
["text segment", "color_code_or_color_name", "category_description"]
```

Use the following color palette and category mapping for your annotations:

- **Orange (#FFA500):** Schemes or programs or missions (e.g., National Health Mission, specific program names)
- **Pink (#FF69B4):** Physical/digital infrastructure that deliver services directly (e.g., hospitals, clinics, health centers, digital platforms)
- **Red (#FF0000):** Top level government organizations planning & financing (e.g., Government of India, Department of Health, Ministry of Health)
- **Dark Blue (#00008B):** Rules & processes & protocols (e.g., guidelines, policies, procedures)
- **Lime Green (#32CD32):** Services provided (e.g., provides support, focuses on, strengthening, treatment, prevention, awareness)
- **Goldenrod (#DAA520):** Quantitative Data (e.g., numbers, counts, statistics related to implementation or facilities)
- **Blue (#0000FF):** Administrative regions (e.g., states, districts, cities, countries)
- **Purple (#800080):** Citizen Life cycle status or attributes (e.g., age groups, pregnancy status, economic status)
- **Cyan (#00FFFF):** Citizen or group profiles (e.g., women, infants, specific communities, demographic groups)
- **Brown (#A52A2A):** Government Official (references to individuals in government roles)
- **Yellow (#FFFF00):** Documents & Reports (references to reports, documents, datasets)
- **Grey (#808080):** Health Issues (e.g., Non-Communicable Diseases, specific diseases, health conditions)

**Instructions:**

1. **Analyze the input text statement.**
2. **Segment the text into meaningful phrases or words that correspond to the categories above.** Segments should be as specific as possible while still being coherent.
3. **For each segment, determine the most appropriate category from the palette.**
4. **Assign the corresponding color code or color name to the segment.**
5. **Write a concise `category_description` that explains why you assigned that category to the segment.**
6. **Structure the output as a JSON array of arrays in the `annotationData` format.**
7. **For the fourth element (relationship array), leave it as an empty array `[]` for now.**

**Example Input Statement:**

```
In Odisha, 30 District NCD Clinics have been established by the Department of Health and Family Welfare, Government of India.
```

**Expected JSON Output (annotationData format):**

```json
[
  ["In Odisha, ", "#0000FF", "Administrative region"],
  ["30 ", "#DAA520", "Quantitative Data - Facility Counts"],
  ["District NCD Clinics ", "#FF69B4", "Physical/digital infrastructure - Type of healthcare facility"],
  ["have been established by the ", "#32CD32", "Services provided by government"],
  ["Department of Health and Family Welfare, ", "#FF0000", "Top level government organization"],
  ["Government of India.", "#FF0000", "Top level government organization"]
]
```

**Now, process the following Input Statement and provide the `annotationData` JSON output:**

**Input Statement:**

=====================

You are an expert in text annotation for healthcare program analysis. Your task is to take a single sentence or short paragraph related to healthcare programs and convert it into structured JSON data in the `annotationData` format.

The `annotationData` format is a JSON array where each element represents an annotated text segment and has the following structure:

```json
[
  "text segment",
  "color_code_or_color_name",
  ["General Category", "Specific Data Type"], // category_description is now an array of two strings
  [] // (Optional and can be empty for now - Array for relationship objects, leave empty for this prompt)
]
```

Use the following color palette and category mapping for your annotations:

- **Orange (#FFA500):** Schemes or programs or missions
- **Pink (#FF69B4):** Physical/digital infrastructure that deliver services directly
- **Red (#FF0000):** Top level government organizations planning & financing
- **Dark Blue (#00008B):** Rules & processes & protocols
- **Lime Green (#32CD32):** Services provided
- **Goldenrod (#DAA520):** Quantitative Data
- **Blue (#0000FF):** Administrative regions
- **Purple (#800080):** Citizen Life cycle status or attributes
- **Cyan (#00FFFF):** Citizen or group profiles
- **Brown (#A52A2A):** Government Official
- **Yellow (#FFFF00):** Documents & Reports
- **Grey (#808080):** Health Issues

**Instructions:**

1. **Analyze the input text statement.**
2. **Segment the text into meaningful phrases or words that correspond to the categories above.** Segments should be as specific as possible while still being coherent.
3. **For each segment, determine the most appropriate _General Category_ from the palette.** This will determine the color.
4. **For each segment, determine the _Specific Data Type_ or sub-category within the _General Category_ (if applicable).** If no specific sub-category is relevant, use a generic term or leave it blank.
5. **Assign the corresponding color code or color name to the segment based on the _General Category_.**
6. **Structure the `category_description` as an array containing two strings: `["General Category", "Specific Data Type"]`.**
7. **Structure the output as a JSON array of arrays in the `annotationData` format.**
8. **For the fourth element (relationship array), leave it as an empty array `[]` for now.**

**Example Input Statement:**

```
In Odisha, 30 District NCD Clinics have been established by the Department of Health and Family Welfare, Government of India.
```

**Expected JSON Output (annotationData format with refined `category_description`):**

```json
[
  ["In Odisha, ", "#0000FF", ["Administrative regions", "State Name"], []],
  ["30 ", "#DAA520", ["Quantitative Data", "Facility Counts"], []],
  ["District NCD Clinics ", "#FF69B4", ["Physical/digital infrastructure", "Type of healthcare facility"], []],
  ["have been established by the ", "#32CD32", ["Services provided", "Government Action"], []],
  [
    "Department of Health and Family Welfare, ",
    "#FF0000",
    ["Top level government organizations", "Department Name"],
    []
  ],
  ["Government of India.", "#FF0000", ["Top level government organizations", "Country Name"], []]
]
```

**Now, process the following Input Statement and provide the `annotationData` JSON output in the new format:**

**Input Statement:**
