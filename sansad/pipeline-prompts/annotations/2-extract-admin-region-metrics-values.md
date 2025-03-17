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

Task: Extract structured information from the following statement and output it as a JSON object that strictly adheres to the schema described below.

Schema Description:

The output JSON should have the following top-level structure:

```json
[
  {
    "metric": _Metric_,
    "unit": _Metric_Unit_
  }
]
```

Detailed Schema for each entity type:

1. _Metric_ Entity: Represent each metric as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'maternal_mortality_ratio' */
     "names": [ "...", ... ], /* Array of Strings, metric names (full and abbreviations), e.g., ["Maternal Mortality Ratio", "MMR"] */
     "description": "...", /* String, brief description */
     "dataType": "...", /* String, from: Categorical_Nominal, Categorical_Ordinal, Numerical_Discrete_Interval, Numerical_Discrete_Ratio, Numerical_Continuous_Interval, Numerical_Continuous_Ratio */
   }
   ```

2. _Metric_Unit_ Entity: Represent each metric unit as a JSON object with the following attributes:

   ```json
   {
     "name_id": "...", /* String, unique identifier (snake_case), e.g., 'per_lakh_live_births' */
     "names": [ "...", ... ], /* Array of Strings, unit names (full and abbreviations), e.g., ["per lakh live births", "per lakh"] */
     "description": "...", /* String, brief description */
   }
   ```

Instructions:

Carefully read the statement and extract the information to populate the JSON structure described above.

Strictly adhere to the JSON structure and entity schemas provided. If there are multiple metrics are identified, return list of metric-unit pairs, with each pair represented as an element in the top-level JSON array.

For each metric and unit identified in the statement, create a corresponding _Metric_ and _Metric_Unit_ entity in the "metrics" and "units" arrays respectively within each element of the top-level JSON array. Ensure you populate all attributes as described in the schema. If a description is not explicitly in the statement, provide a concise, general description. For _Metric_ entities, the "units" attribute should be an array of `name_id` strings that correspond to the `name_id` of the _Metric_Unit_ entities you create.

Generate a unique `name_id` in snake_case based on the primary name of the metric or unit. For example, 'Maternal Mortality Ratio' should become `maternal_mortality_ratio`, and 'per lakh live births' should become `per_lakh_live_births`. Ensure `name_id`s are unique within the 'metrics' and 'units' arrays, respectively, for each pair.

Identify all the unique metrics in the input statement. Each metric must have a unit. They are a pair.

Output the complete JSON object.

Output JSON (Template - for a single pair example):

```json
[
  {
    "metrics": _Metric_,
    "units": _Metric_Unit_
  }
]
```

Input Statement:

"In Odisha 30 District NCD Clinics, 12 Cardiac Care Units (CCU), 32 District Day Care Centres and 414 Community Health Centres have been set up. The Department of Health and Family Welfare, Government of India, provides technical and financial support to the States and Union Territories under the National Programme for Prevention and Control of Non Communicable Diseases (NP-NCD) as part of National Health Mission (NHM). The programme focusses on strengthening infrastructure, human resource development, early diagnosis, referral to an appropriate level of healthcare facility for treatment and management and health promotion and awareness generation for prevention, of Non-Communicable Diseases (NCDs) including breast and cervical cancer."
