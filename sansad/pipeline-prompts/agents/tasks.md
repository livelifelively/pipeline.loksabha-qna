## Task description

A list of strings, where each string is a phrase extracted (highlighted) directly from the input statement. Each phrase in the list represents a potential mention of a metric, measurement, or quantitative data. These phrases are expected to be:

- **Contextually Meaningful:** Each phrase should capture a meaningful unit of text from the input, not just isolated numbers or keywords. They should provide enough context to understand what is being measured or quantified.
- **Quantitatively Focused:** The phrases should relate to numerical values, measurements, or quantities. They should contain elements like numerical values, units of measurement, magnitude words, or metric keywords.
- **Directly from Input:** The phrases are extracted directly from the input text, preserving the original wording and phrasing. No modifications or re-engineering of the phrases are expected at this stage.
- **Representing Metric Mentions:** Each phrase is identified as a _potential_ metric mention, meaning it's a candidate for further analysis as a metric or measurement. The task focuses on identifying these potential mentions, not on validating or classifying them as definitive metrics.

**Example:**

**Input Statement:** "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY) is a flagship scheme of the Government which provides health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization to approximately 55 crore beneficiaries corresponding to 12.37 crore families constituting economically vulnerable bottom 40% of India’s population. Recently, the scheme has been expanded to cover 6 crore senior citizens of age 70 years and above belonging to 4.5 crore families irrespective of their socio-economic status under AB-PMJAY with Vay Vandana Card. As on 01.01.2025, a total of 8.59 crore hospital admissions worth Rs.1.19 lakh crore have been authorized under the scheme"

**Expected Output List:**

```
[
"Rs. 5 lakhs per family per year health cover",
"55 crore beneficiaries",
"12.37 crore families",
"40% of India’s population",
"6 crore senior citizens of age 70 years and above",
"age 70 years and above",
"4.5 crore families",
"8.59 crore hospital admissions",
"hospital admissions worth Rs.1.19 lakh crore"
]
```

**Key Considerations Illustrated by the Example:**

- **Context is Prioritized:** Notice that shorter phrases like just "5 lakhs", "55 crore", or "40%" are **not** included as standalone outputs in the expected list. This is because the task prioritizes extracting _contextually rich phrases_ that provide more information about _what_ is being measured. For example, "Rs. 5 lakhs per family per year health cover" is preferred over just "5 lakhs" as it specifies the context of "health cover" and the rate "per family per year."
- **Meaningful Phrases:** The extracted phrases are meaningful units of text that represent complete metric mentions within the context of the input statement. They are not just random snippets of numbers and units.
- **Direct Extraction:** The phrases are directly copied from the input text, maintaining the original wording and order (e.g., "age 70 years and above" retains the natural phrasing).
- **Dates Excluded (in this context):** While the input contains a date "01.01.2025", it is not extracted as a metric mention in this example because, in this context, it functions as a temporal marker rather than a metric _measurement_ in the sense of quantity, rate, or value. However, in other contexts, dates _could_ potentially be considered metric mentions if they represent durations or time-based measurements.

The list should contain multiple such phrases if the input statement contains multiple potential metric mentions. The order of phrases in the list is not specified to be significant, but each item should be a valid extracted metric mention phrase.

## Task Name

metric_phrase_highlighting
