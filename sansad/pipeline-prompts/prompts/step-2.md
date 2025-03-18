Task: Extract and Format Document Section Content as HTML (Merged Answer and Statement Body)

You are provided with the OCR output of a Lok Sabha Starred Question document that has been validated for structural conformance. Your task is to process this document section by section and format the content of each section as HTML.

**IMPORTANT: Your output MUST be a valid JSON object, NOT code, NOT plain text. The JSON object MUST conform to the structure described below.**

**Specific Instructions:**

1.  Process Document Section by Section: Analyze the OCR output and segment it into the following predefined section types (which should have been identified in a prior validation step): "Header Section", "Question Section", "Answer Section", "Table Section", "Annexure Section". Note that "Statement Body Section" is NOT considered a separate section type for output in this step, its content will be merged into the "Answer Section". Use keywords and structural cues to identify these sections (refer to the previously defined "Standard Document Structure" if needed for guidance).

2.  For Each Identified Section:

    - Determine Section Data Type: Classify the content of the current section as either "text" or "table". (If you are unsure, default to "text").

    - Generate HTML Content based on Section Type:

      - If "text" section: Format the section's text content as semantic HTML. Your goal is to create well-structured and readable HTML using appropriate tags. Use the following HTML tags where appropriate:

        - `<p>` for paragraphs of text.
        - `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>` for headings. Use heading levels semantically (e.g., `<h1>` for main section headings, `<h2>` for subheadings, etc., if discernible).
        - `<ul>` and `<li>` for unordered (bulleted) lists.
        - `<ol>` and `<li>` for ordered (numbered) lists. If the original document uses letters for lists, you can still use `<ol>` for ordered lists in HTML, or use CSS for letter styling if precise letter representation is crucial.
        - `<strong>` or `<b>` for bold text (where emphasis is intended).
        - `<em>` or `<i>` for italic text (where emphasis is intended).
        - `<br>` for line breaks within paragraphs if needed to preserve important line breaks from the original document.
        - Clean OCR artifacts and normalize whitespace in the text _before_ embedding it within HTML tags.
        - For plain text that doesn't clearly fit into paragraphs or lists, enclose it in `<p>` tags as the default.

      - If "table" section: Convert the table data into HTML `<table>` markup. Ensure you create a valid HTML table structure using:
        - `<table>` to enclose the entire table.
        - `<thead>` to enclose table header rows (if header rows are clearly identifiable). Use `<tr>` for header rows and `<th>` for header cells within `<thead>`.
        - `<tbody>` to enclose the main table body rows. Use `<tr>` for table data rows and `<td>` for data cells within `<tbody>`.
        - Populate `<th>` and `<td>` cells with the text content from the table, cleaning OCR artifacts and normalizing whitespace within cell content.

    - **CRITICAL: MERGE "Statement Body Section" INTO "Answer Section":**

      - **IMPORTANT: You MUST NOT output a separate section with `section_type: "statement_body"` in the final JSON output.**
      - **MANDATORY: You MUST append ALL the HTML content that you would have generated for the "Statement Body Section" DIRECTLY to the `html_content` of the "Answer Section".**
      - **The "Answer Section" MUST contain the _combined_ HTML content of:**
        - The original "Answer Section" (header/intro part).
        - AND the entire text content of the "Statement Body Section" that follows.
      - Do not create a separate JSON object for "statement_body" in the output JSON.

    - Extract Section Name/Heading: For each section, extract a descriptive name or heading. If the section has an explicit heading in the document, use that. If not, generate a descriptive name based on the `section_type` (e.g., "Question Section Content", "Statement Body HTML Table"). For the **merged "Answer Section"**, use the section name "Answer Section".

3.  Structure Output as JSON (Array of Sections with HTML Content): Return a JSON list where each element represents a document section. Each section object MUST have the following JSON structure. **Do not deviate from this JSON structure. Ensure the JSON is valid and well-formed.**

```json
[
  {
    "section_type": <string>,
    "section_name": <string>,
    "html_content": <string>
  },
  // ... more section objects ...
]
```

Example of Desired JSON Output Format (Illustrative Snippet - for the whole document, but you will generate for your document):

```json
[
  {
    "section_type": "header",
    "section_name": "Header Section",
    "html_content": "<p>GOVERNMENT OF INDIA</p>\n<p>MINISTRY OF HEALTH AND FAMILY WELFARE</p>\n..."
  },
  {
    "section_type": "question",
    "section_name": "Question Section",
    "html_content": "<p>*70. SHRI BAIJAYANT PANDA:</p>\n<p>Will the Minister of HEALTH AND FAMILY WELFARE be pleased to state:</p>\n<ol>\n  <li>(a) ...</li>\n  ...</ol>"
  },
  {
    "section_type": "answer",
    "section_name": "Answer Section",
    "html_content": "<p>ANSWER</p>\n<p>THE MINISTER OF HEALTH AND FAMILY WELFARE</p>\n<p>...</p>\n<p>STATEMENT REFERRED TO IN REPLY TO LOK SABHA</p>\n<p>...</p>\n<ul><li>...</li></ul>\n<table>...</table>"
  },
  {
    "section_type": "table",
    "section_name": "Budget Table",
    "html_content": "<table>...</table>"
  },
  {
    "section_type": "annexure",
    "section_name": "Annexure Section",
    "html_content": "<p>Annexure</p>\n<table>...</table>"
  }
]
```

Input Document (OCR Output):

[==Paste the entire OCR output of your document here==]

Expected Output:

A valid and well-formed JSON list of section objects, conforming EXACTLY to the JSON structure defined above, with html_content as strings, and NO statement_body section.

```json
[
  // ... JSON section objects with "section_type", "section_name", and "html_content" ... (NO "statement_body", VALID JSON)
]
```
