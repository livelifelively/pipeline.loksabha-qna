Task: Perform Section-wise Sentence Splitting and Output JSON with Paragraphs (LLM-Driven)

You are provided with a JSON object as input. This JSON object is the output from the previous step (Step 2) and contains a list of document sections, where each section has a `section_type`, `section_name`, and `html_content`.

Your task is to process each "text" section in this JSON and perform sentence splitting on its text content, then structure the output as a new JSON object with sentences grouped into paragraphs.

**Input JSON Example (Snippet - one section object):**

```json
{
  "section_type": "answer",
  "section_name": "Answer Section",
  "html_content": "<p>ANSWER</p>\n<p>THE MINISTER OF HEALTH AND FAMILY WELFARE</p>\n<p>This is the first sentence of the answer. This is the second sentence. \n\nThis is the start of a new paragraph. This is the only sentence in this paragraph.</p>"
}
```

**Instructions:**

1.  **Input is JSON:** You will receive a JSON object as input, containing a list of sections, as shown in the example above.

2.  **Process Section by Section:** Iterate through each section object in the input JSON list.

3.  **Check `section_type`:** For each section, check the `section_type`.

4.  **Process "Text" Section Types Only:** Only process sections where `section_type` indicates a "text" section (e.g., "header", "question", "answer", "annexure", "paragraph"). For "table" sections, leave them unchanged in the output.

5.  **Sentence Splitting for "Text" Sections:** For each "text" section:

    - Extract the `html_content` string.
    - Remove HTML tags from the `html_content` to get the plain text content.
    - Perform sentence splitting on the plain text content. Use your best judgment to divide the text into grammatically correct and meaningful sentences.
    - Group the sentences into paragraphs. Base paragraph breaks on cues like double line breaks (`\n\n`) in the original text, or other logical paragraph divisions you can infer from the text content.

6.  **Structure Output JSON (with `paragraphs` Array):** For each "text" section, create a new section object in the output JSON that has the following structure:

    ```json
    {
      "section_type": <string>, // (Copy from input JSON) e.g., "answer"
      "section_name": <string>, // (Copy from input JSON) e.g., "Answer Section"
      "paragraphs": [           // NEW: Array of paragraphs, each paragraph is an array of sentences (strings)
        [<string>, <string>, ...], // Paragraph 1 sentences
        [<string>, <string>, ...], // Paragraph 2 sentences
        // ... more paragraphs ...
      ],
      "html_content": <string> // (Copy from input JSON) - Retain original html_content for reference
    }
    ```

    For "table" sections, simply copy the section object from the input JSON directly to the output JSON _without_ performing sentence splitting or adding a `paragraphs` array (table sections will not have a `paragraphs` field in the output).

7.  **Output JSON Format:** Return a JSON list containing the processed section objects. The output MUST be valid JSON and conform to the structure described above.

**Example of Desired JSON Output Format (Illustrative Snippet - for one "Answer Section"):**

```json
{
  "section_type": "answer",
  "section_name": "Answer Section",
  "paragraphs": [
    [
      "ANSWER" // Paragraph 1 - one sentence
    ],
    [
      "THE MINISTER OF HEALTH AND FAMILY WELFARE", // Paragraph 2 - sentence 1
      "(SHRI JAGAT PRAKASH NADDA)" // Paragraph 2 - sentence 2
    ],
    [
      "This is the first sentence of the answer.", // Paragraph 3 - sentence 1
      "This is the second sentence." // Paragraph 3 - sentence 2
    ],
    [
      "This is the start of a new paragraph.", // Paragraph 4 - sentence 1
      "This is the only sentence in this paragraph." // Paragraph 4 - sentence 2
    ]
  ],
  "html_content": "<p>ANSWER</p>\n<p>THE MINISTER OF HEALTH AND FAMILY WELFARE</p>\n<p>This is the first sentence of the answer. This is the second sentence. \n\nThis is the start of a new paragraph. This is the only sentence in this paragraph.</p>" // Original html_content retained
}
```

**Input JSON (from Step 2):**

[==Paste the JSON output from Step 2 here==]

**Expected Output:**

A JSON list of section objects, conforming to the structure above, with `paragraphs` array added to "text" sections, and `html_content` retained (or removed, as per your choice).

```json
[
  // ... JSON section objects with "section_type", "section_name", "paragraphs", and "html_content" ...
]
```
