Task: Validate Document Structure, Extract Metadata, and Assess Conformance for Lok Sabha Question Documents

You are provided with the OCR output of a Lok Sabha Question document. Your task is to:

1.  Validate Document Structure: Analyze the document's structure and assess how well it conforms to the expected standard structure for this document type.

2.  Extract Document Metadata: Extract key metadata information from the document.

3.  Generate Conformance Score and Structured Reasoning: Provide a numerical score and detailed reasoning for the document's structure conformance.

**Standard Document Structure for Lok Sabha Questions:**

The expected standard structure for these documents is as follows, in order:

1.  Header Section:

    - Keywords to identify: "GOVERNMENT OF INDIA", "MINISTRY OF", "DEPARTMENT OF", "LOK SABHA", "STARRED QUESTION NO."
    - Content: Contains government identifiers, ministry names, document type, question number, date, and topic.

2.  Question Section:

    - Keywords to identify: Starts with a line like "\*[Number]. SHRI...", followed by "Will the Minister of...be pleased to state:", and then a lettered or numbered list of questions (a), (b), (c), (d), (e).
    - Content: Contains the actual questions being asked in lettered/numbered format.

3.  Answer Section:

    - Keyword to identify: "ANSWER" (prominently placed).
    - Content: Starts with "THE MINISTER OF..." followed by the Minister's name and a short introductory sentence, often indicating a statement is laid on the table (e.g., "(a) to (e) A Statement is laid...").

4.  Statement Body Section:

    - Keyword to identify: "STATEMENT REFERRED TO IN REPLY TO LOK SABHA".
    - Content: Contains the detailed statement providing answers and information. May include paragraphs, lists, and tables. Can span multiple pages.

5.  Table Sections:

    - Identification: Sections that are clearly formatted as data tables with rows and columns. Can appear within "Statement Body Section" or "Annexure Section".
    - Content: Tabular data in rows and columns.

6.  Annexure Section:
    - Keyword to identify: "Annexure".
    - Content: Contains supplementary information, often in tabular format ("Target and Achievement under NHM" table is typical).

**Task Instructions:**

1.  Analyze Document and Identify Sections: Process the OCR output and identify the sections present in the document, attempting to classify them into the standard section types listed above.

2.  Assess Document Structure Conformance: Evaluate how well the document's identified sections align with the "Standard Document Structure" described above. Consider:

    - Presence of all expected sections in the standard structure.
    - Correct order of sections.
    - Presence and correctness of key headings and keywords for each section type.
    - Overall structural consistency.

3.  Generate Conformance Score (0-100): Assign a `conformance_score` from 0 to 100, where 100 represents perfect conformance to the standard structure and 0 represents no conformance.

4.  Provide Structured Reasoning for Conformance Score: Generate a detailed `reasoning` in JSON format, with:

    - `reasoning.adherence`: A list of strings describing aspects of the document that _do_ conform to the standard structure and are well-formed.
    - `reasoning.deviations`: A list of strings describing aspects of the document that _deviate_ from the standard structure or are problematic. **If there are NO deviations, output an empty JSON array `[]` for `deviations`, not a list containing "None" or similar string.**
    - `reasoning.observations`: A short, overall summary observation about the document's conformance.

5.  Extract Document Metadata: Extract the following metadata:

    - `document_type`: Infer the document type (should be "Lok Sabha Question").
    - `document_title`: Extract the document title (e.g., "MATERNAL AND INFANT HEALTH OUTCOMES").
    - `question_number`: Extract the question number (e.g., "61").
    - `answer_date`: Extract the date the question is to be answered in "YYYY-MM-DD" format (e.g., "2025-02-07").
    - `answer_length_words`: Calculate the approximate word count of the **entire Answer Content**.  
      **"Answer Content" is defined as:**
      - **The text content of the "Answer Section" itself** (including "ANSWER", Minister's Name, introductory sentence).
      - **AND, the entire text content of the "Statement Body Section"** (starting from "STATEMENT REFERRED TO IN REPLY TO LOK SABHA" and continuing until the beginning of the "Annexure Section", or the end of the document if no Annexure).
      - **In essence, "Answer Content" is considered to be everything in the document that comes _after_ the "Question Section" and _before_ the "Annexure Section" (if present), OR everything after "Question Section" until the end of the document if no Annexure.**
    - `has_tables`: Determine if the document contains at least one data table (true/false).

6.  Determine Conformance Check Pass/Fail: Based on the `conformance_score`, set `document_passes_conformance_check` to `true` if the score is 80 or above, and `false` if below 80. (You can adjust the threshold later).

7.  Structure Output as JSON: Return a JSON object with the following structure:

```json
{
  "document_conformance": {
    "conformance_score": <integer>,
    "reasoning": {
      "adherence": <list of strings>,
      "deviations": <list of strings>,
      "observations": <string>
    }
  },
  "document_metadata": {
    "document_type": <string>,
    "document_title": <string>,
    "question_number": <string>,
    "answer_date": <string>,
    "answer_length_words": <integer>,
    "has_tables": <boolean>
  },
  "document_passes_conformance_check": <boolean>
}
```
