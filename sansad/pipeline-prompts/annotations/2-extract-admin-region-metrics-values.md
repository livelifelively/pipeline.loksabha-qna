## One step extraction prompt

Task: Extract structured information from the following statement and output it as a JSON object that strictly adheres to the schema described below.

Statement: "As per the Special Bulletin on Maternal Mortality Ratio (MMR) released by the Sample Registration System (SRS) 2018-20, the MMR of Maharashtra has been reduced from 61 per lakh live births in 2014-16 to 33 per lakh live births in 2018-20 and MMR of Bihar has been reduced from 165 per lakh live births in 2014-16 to 118 per lakh live births in 2018-20."

Schema Description:

The output JSON should have the following top-level structure:

```json
{
  "metrics": [
    /* Array of _Metric_ entities */
  ],
  "units": [
    /* Array of _Metric_Unit_ entities */
  ],
  "data_values_state_ut": [
    /* Array of _Data_Value_Indian_State_Union_Territory_ entities */
  ]
}
```

Detailed Schema for each entity type:

1. _Metric_ Entity: Represent each metric as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case) */
     "names": [ "...", ... ], /* Array of Strings, metric names (full and abbreviations) */
     "description": "...", /* String, brief description */
     "dataType": "...", /* String, from: Categorical_Nominal, Categorical_Ordinal, Numerical_Discrete_Interval, Numerical_Discrete_Ratio, Numerical_Continuous_Interval, Numerical_Continuous_Ratio */
     "units": [ /* Array of name_id strings of associated _Metric_Unit_ entities */ ]
   }
   ```

2. _Metric_Unit_ Entity: Represent each metric unit as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case) */
     "names": [ "...", ... ], /* Array of Strings, unit names (full and abbreviations) */
     "description": "...", /* String, brief description */
   }
   ```

3. _Data_Value_Indian_State_Union_Territory_ Entity: Represent each data value for a state/UT as a JSON object with the following attributes:

   ```json
   {
     "state_or_union_territory": "...", /* String, Name of Indian State/UT */
     "datetime_from": { "year": ..., "month": ..., "day": ... }, /* Object, Start date */
     "datetime_to": { "year": ..., "month": ..., "day": ... }, /* Object, End date */
     "data_value": { /* Object representing the associated _Data_Value_ */
       "metric_name_id": "...", /* String, name_id of the associated _Metric_ entity */
       "unit_name_id": "...", /* String, name_id of the associated _Metric_Unit_ entity */
       "numerical_value": ..., /* Float, if applicable, otherwise null */
       "categorical_value": "..." /* String, if applicable, otherwise null */
     }
   }
   ```

Instructions:

Carefully read the statement and extract the information to populate the JSON structure described above.

Strictly adhere to the JSON structure and entity schemas provided.

For each metric and unit identified in the statement, create a corresponding _Metric_ and _Metric_Unit_ entity in the "metrics" and "units" arrays respectively. Ensure you populate all attributes as described in the schema. If a description is not explicitly in the statement, provide a concise, general description. For _Metric_ entities, the "units" attribute should be an array of `name_id` strings that correspond to the `name_id` of the _Metric_Unit_ entities you create.

For each data point in the statement, create a _Data_Value_Indian_State_Union_Territory_ entity in the "data*values_state_ut" array. Populate all attributes including state/UT name, datetime ranges, and the nested "data_value" object. Within the "data_value" object, ensure you include `metric_name_id`, `unit_name_id`, and the appropriate value (`numerical_value` or `categorical_value`). Use `null` if a value is not applicable. Use `name_id` values to refer to the \_Metric* and _Metric_Unit_ entities you have defined in the "metrics" and "units" arrays.

Output the complete JSON object.

Output JSON:

```json
{
  "metrics": [],
  "units": [],
  "data_values_state_ut": []
}
```

================

## Two step extraction prompt

**Task:** Extract metric and unit information from the following statement and output it as a JSON object that strictly adheres to the schema described below for `metrics` and `units` arrays. Focus solely on identifying and defining the metrics and units mentioned in the statement.

**Statement:** "As per the Special Bulletin on Maternal Mortality Ratio (MMR) released by the Sample Registration System (SRS) 2018-20, the MMR of Maharashtra has been reduced from 61 per lakh live births in 2014-16 to 33 per lakh live births in 2018-20 and MMR of Bihar has been reduced from 165 per lakh live births in 2014-16 to 118 per lakh live births in 2018-20."

**Schema Description (Relevant Parts):**

The output JSON should have the following top-level structure:

```json
{
  "metrics": [
    /* Array of _Metric_ entities */
  ],
  "units": [
    /* Array of _Metric_Unit_ entities */
  ]
}
```

Detailed Schema for each entity type:

1. _Metric_ Entity: Represent each metric as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case) */
     "names": [ "...", ... ], /* Array of Strings, metric names (full and abbreviations) */
     "description": "...", /* String, brief description */
     "dataType": "...", /* String, from: Categorical_Nominal, Categorical_Ordinal, Numerical_Discrete_Interval, Numerical_Discrete_Ratio, Numerical_Continuous_Interval, Numerical_Continuous_Ratio */
     "units": [ /* Array of name_id strings of associated _Metric_Unit_ entities */ ]
   }
   ```

2. _Metric_Unit_ Entity: Represent each metric unit as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case) */
     "names": [ "...", ... ], /* Array of Strings, unit names (full and abbreviations) */
     "description": "...", /* String, brief description */
   }
   ```

**Instructions:**

1.  **Identify Metrics and Units:** Carefully read the statement and identify all the metrics and units that are explicitly mentioned. Focus _only_ on metrics and units.

2.  **Create _Metric_ Entities:** For each unique metric identified, create a _Metric_ entity as a JSON object.

    - Generate a unique `name_id` in snake_case (e.g., `maternal_mortality_ratio`).
    - Populate the `names` array with full names and abbreviations (e.g., ["Maternal Mortality Ratio", "MMR"]).
    - Provide a brief `description`. If not explicitly stated, provide a concise, general description.
    - Determine the appropriate `dataType` from the provided list and assign it.
    - Identify the associated units for this metric. The `units` attribute should be an array of `name_id` strings that correspond to the `name_id` of the _Metric_Unit_ entities you create in the next step.

3.  **Create _Metric_Unit_ Entities:** For each unique unit identified, create a _Metric_Unit_ entity as a JSON object.

    - Generate a unique `name_id` in snake_case (e.g., `per_lakh_live_births`).
    - Populate the `names` array with full names and abbreviations or variations (e.g., ["per lakh live births", "per lakh"]).
    - Provide a brief `description`. If not explicitly stated, provide a concise, general description.

4.  **Link Metrics and Units:** In the `_Metric_` entities, use the `units` array to link to the corresponding `_Metric_Unit_` entities by referencing their `name_id`s.

5.  **Output JSON:** Output the complete JSON object containing only the `metrics` and `units` arrays.

**Output JSON (Template):**

```json
{
  "metrics": [],
  "units": []
}
```

=============

**Task: Extract structured information and output _ONLY_ JSON. No other text is allowed.**

**IMPORTANT: Your ENTIRE response MUST be a valid JSON object conforming to the schema below. Do not include any introductory text, explanations, or any other text outside of the JSON object itself. If no metric-unit pairs are found, return an EMPTY JSON ARRAY `[]`.**

For each identified metric-unit pair in the following statement, extract structured information and output it as a JSON object that strictly adheres to the schema described below. Also, for each pair, extract the location(s) and the corresponding substring of the **metric mention** (including any associated value) within the input statement.

Schema Description:

The output JSON MUST have the following top-level structure:

```json
[
  {
    "metric": _Metric_,
    "unit": _Metric_Unit_,
    "locations": [
      {
        "start_char": Integer,  /* Zero-based start character index of the metric mention (including value) */
        "end_char": Integer,    /* Zero-based end character index of the metric mention (including value, exclusive) */
        "substring": String     /* The substring representing the metric mention (including value) from the input statement */
      }
      /* ... more location objects if metric is mentioned multiple times ... */
    ]
  }
]
```

Detailed Schema for each entity type:

1. _Metric_ Entity: Represent each metric as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'number_of_ncd_clinics', 'maternal_mortality_ratio' */
     "names": [ "...", ... ], /* Array of Strings, metric names (full and abbreviations), e.g., ["Number of NCD Clinics", "NCD Clinics Count"], ["Maternal Mortality Ratio", "MMR"] */
     "description": "...", /* String, brief description */
     "dataType": "...", /* String, from: Categorical_Nominal, Categorical_Ordinal, Numerical_Discrete_Interval, Numerical_Discrete_Ratio, Numerical_Continuous_Interval, Numerical_Continuous_Ratio */
   }
   ```

2. _Metric_Unit_ Entity: Represent each metric unit as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'number_of_ncd_clinics', 'per_lakh_live_births_unit' */
     "names": [ "...", ... ], /* Array of Strings, unit names (full and abbreviations), e.g., ["NCD Clinics", "District NCD Clinics"], ["Per Lakh Live Births", "Per Lakh"] */
     "description": "...", /* String, brief description - could describe the type of unit */
   }
   ```

Instructions:

Carefully read the statement and extract the information to populate the JSON structure described above.

**STRICTLY adhere to the JSON structure and entity schemas provided. Your output MUST be valid JSON and ONLY JSON.** If there are multiple metric-unit pairs identified, return a list of these pairs, with each pair represented as an element in the top-level JSON array. For each pair, identify and record the location(s) of the **metric mention** (including any associated value) within the input statement as zero-based character ranges (`start_char` and `end_char`), and extract the corresponding **metric mention substring** (including the value) from the input statement. If a metric mention is repeated with different values or in different locations, record all locations and substrings.

For the `locations`, ensure that `start_char` and `end_char` are zero-based character indices into the input statement string. `start_char` should point to the first character of the **metric mention (including value)**, and `end_char` should point to the character immediately after the end of the **metric mention (including value)** (exclusive). Also, extract the exact substring representing the **metric mention (including value)** from the input statement that falls within this character range and include it as the `substring` value.

For each metric and unit identified in the statement, create a corresponding `_Metric_` and `_Metric_Unit_` entity. Ensure you populate all attributes as described in the schema. If a description is not explicitly in the statement, provide a concise, general description.

Generate a unique `name_id` in snake_case based on the primary name of the metric or unit. For example, 'Number of NCD Clinics' could become `number_of_ncd_clinics`, 'District NCD Clinics' could become `district_ncd_clinics_unit`, 'Maternal Mortality Ratio' could become `maternal_mortality_ratio`, and 'per lakh live births' could become `per_lakh_live_births_unit`. Ensure `name_id`s are unique within the 'metrics' and 'units' context, respectively, for each pair.

Identify all the unique metrics in the input statement. Each metric must have a corresponding unit. They are considered a pair. For each identified metric, locate its mention(s) in the input string, determine the zero-based start and end character indices of each **metric mention (including value)**, and extract the substring at that location, ensuring it includes the numerical value if present.

**Output ONLY the complete JSON object. Do not add any text before or after the JSON. If no metric-unit pairs are found in the input statement, output an EMPTY JSON ARRAY: `[]`**

Output JSON (Template - for a single pair example):

```json
[
  {
    "metric": {
      /* _Metric_ entity will be placed here */
    },
    "unit": {
      /* _Metric_Unit_ entity will be placed here */
    },
    "locations": [
      {
        "start_char": Integer,
        "end_char": Integer,
        "substring": String /* Metric mention substring WITH numerical value */
      }
    ]
  }
]
```

Input Statement:

"Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) is a
flagship scheme of the Government which provides health cover of Rs. 5 lakhs per
family per year for secondary and tertiary care hospitalization to approximately 55
crore beneficiaries corresponding to 12.37 crore families constituting economically
vulnerable bottom 40% of India’s population. Recently, the scheme has been
expanded to cover 6 crore senior citizens of age 70 years and above belonging to 4.5
crore families irrespective of their socio-economic status under AB-PMJAY with Vay
Vandana Card. As on 01.01.2025, a total of 8.59 crore hospital admissions worth
Rs.1.19 lakh crore have been authorized under the scheme"

"In Odisha 30 District NCD Clinics, 12 Cardiac Care Units (CCU), 32 District Day Care Centres and 414 Community Health Centres have been set up. The Department of Health and Family Welfare, Government of India, provides technical and financial support to the States and Union Territories under the National Programme for Prevention and Control of Non Communicable Diseases (NP-NCD) as part of National Health Mission (NHM). The programme focusses on strengthening infrastructure, human resource development, early diagnosis, referral to an appropriate level of healthcare facility for treatment and management and health promotion and awareness generation for prevention, of Non-Communicable Diseases (NCDs) including breast and cervical cancer."

===============

**Task: Extract structured information and output _ONLY_ JSON. No other text is allowed.**

**IMPORTANT: Your ENTIRE response MUST be a valid JSON object conforming to the schema below. Do not include any introductory text, explanations, or any other text outside of the JSON object itself. If no metric-unit-magnitude (if applicable) pairs are found, return an EMPTY JSON ARRAY `[]`.**

For each identified metric-unit-magnitude (if applicable) combination in the following statement, extract structured information and output it as a JSON object that strictly adheres to the schema described below. Also, for each combination, extract the location(s) and the corresponding substring of the **metric mention** (including any associated value and magnitude), and the **value** itself.

Schema Description:

The output JSON MUST have the following top-level structure:

```json
[
  {
    "metric": _Metric_,
    "unit": _Metric_Unit_,
    "magnitude": _Magnitude_, /* OPTIONAL: Include only if a magnitude is present */
    "value": String,          /* String representation of the value */
    "locations": [
      {
        "start_char": Integer,  /* Zero-based start character index of the metric mention (including value and magnitude) */
        "end_char": Integer,    /* Zero-based end character index of the metric mention (including value and magnitude, exclusive) */
        "substring": String     /* The substring representing the metric mention (including value and magnitude) from the input statement */
      }
      /* ... more location objects if metric is mentioned multiple times ... */
    ]
  }
]
```

Detailed Schema for each entity type:

1. _Metric_ Entity: Represent each metric as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'number_of_ncd_clinics', 'maternal_mortality_ratio' */
     "names": [ "...", ... ], /* Array of Strings, metric names (full and abbreviations), e.g., ["Number of NCD Clinics", "NCD Clinics Count"], ["Maternal Mortality Ratio", "MMR"] */
     "description": "...", /* String, brief description */
     "dataType": "...", /* String, from: Categorical_Nominal, Categorical_Ordinal, Numerical_Discrete_Interval, Numerical_Discrete_Ratio, Numerical_Continuous_Interval, Numerical_Continuous_Ratio */
   }
   ```

2. _Metric_Unit_ Entity: Represent each metric unit as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'kilogram_unit', 'per_lakh_live_births_unit', 'percentage_unit' */
     "names": [ "...", ... ], /* Array of Strings, unit names (full and abbreviations), e.g., ["Kilogram", "Kg"], ["Per Lakh Live Births", "Per Lakh"], ["Percent", "%"] */
     "description": "...", /* String, brief description - describes the type of unit (e.g., weight, currency, percentage) */
   }
   ```

3. _Magnitude_ Entity: Represent each magnitude (numerical scale) as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'lakh_scale', 'million_scale', 'crore_scale' */
     "names": [ "...", ... ], /* Array of Strings, magnitude names (full and abbreviations), e.g., ["Lakh", "lakhs"], ["Million", "million"], ["Crore", "crores"] */
     "description": "...", /* String, brief description - describes the numerical scale (e.g., "100,000", "1,000,000", "10,000,000") */
     "scale_value": Integer /* Integer value of the scale, e.g., 100000, 1000000, 10000000 */
   }
   ```

Instructions:

Carefully read the statement and extract the information to populate the JSON structure described above.

**STRICTLY adhere to the JSON structure and entity schemas provided. Your output MUST be valid JSON and ONLY JSON.** If there are multiple metric-unit-magnitude (if applicable) combinations identified, return a list of these combinations, with each combination represented as an element in the top-level JSON array. For each combination, identify and record the location(s) of the **metric mention** (including any associated value and magnitude) within the input statement as zero-based character ranges (`start_char` and `end_char`), and extract the corresponding **metric mention substring** (including the value and magnitude) from the input statement. Also, extract the **value** as a string. If a metric mention is repeated with different values, magnitudes or in different locations, record all locations, substrings, and corresponding values. If no magnitude is mentioned for a metric-unit pair, the `magnitude` field in the JSON should be omitted for that entry.

For the `locations`, ensure that `start_char` and `end_char` are zero-based character indices into the input statement string. `start_char` should point to the first character of the **metric mention (including value and magnitude)**, and `end_char` should point to the character immediately after the end of the **metric mention (including value and magnitude)** (exclusive). Also, extract the exact substring representing the **metric mention (including value and magnitude)** from the input statement that falls within this character range and include it as the `substring` value.

For each metric, unit, and magnitude (if present) identified in the statement, create a corresponding `_Metric_`, `_Metric_Unit_`, and `_Magnitude_` entity. Ensure you populate all attributes as described in the schema. If a description is not explicitly in the statement, provide a concise, general description. For `_Magnitude_`, include the `scale_value` attribute representing the numerical value of the scale.

Generate a unique `name_id` in snake_case based on the primary name of the metric, unit, or magnitude. For example, 'Number of NCD Clinics' could become `number_of_ncd_clinics`, 'Indian Rupee' could become `indian_rupee_unit`, 'Lakh' could become `lakh_scale`, 'District NCD Clinics' could become `district_ncd_clinics_unit`, 'Maternal Mortality Ratio' could become `maternal_mortality_ratio`, and 'per lakh live births' could become `per_lakh_live_births_unit`. Ensure `name_id`s are unique within their respective entity contexts.

Identify all the unique metrics in the input statement. Each metric must have a corresponding unit and may have a magnitude. They are considered a combination. For each identified metric, locate its mention(s) in the input string, determine the zero-based start and end character indices of each **metric mention (including value and magnitude)**, and extract the substring at that location, ensuring it includes the value and magnitude if present. Also extract the ** value** itself.

**Output ONLY the complete JSON object. Do not add any text before or after the JSON. If no metric-unit-magnitude (if applicable) combinations are found in the input statement, output an EMPTY JSON ARRAY: `[]`**

Output JSON (Template - for a single combination example with magnitude):

```json
[
  {
    "metric": {
      /* _Metric_ entity will be placed here */
    },
    "unit": {
      /* _Metric_Unit_ entity will be placed here */
    },
    "magnitude": {
      /* _Magnitude_ entity will be placed here */
    },
    "value": String,          /* Numerical value as string */
    "locations": [
      {
        "start_char": Integer,
        "end_char": Integer,
        "substring": String /* Metric mention substring WITH numerical value and magnitude */
      }
    ]
  }
]
```

Input Statement:

"Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) is a
flagship scheme of the Government which provides health cover of Rs. 5 lakhs per
family per year for secondary and tertiary care hospitalization to approximately 55
crore beneficiaries corresponding to 12.37 crore families constituting economically
vulnerable bottom 40% of India’s population. Recently, the scheme has been
expanded to cover 6 crore senior citizens of age 70 years and above belonging to 4.5
crore families irrespective of their socio-economic status under AB-PMJAY with Vay
Vandana Card. As on 01.01.2025, a total of 8.59 crore hospital admissions worth
Rs.1.19 lakh crore have been authorized under the scheme"
