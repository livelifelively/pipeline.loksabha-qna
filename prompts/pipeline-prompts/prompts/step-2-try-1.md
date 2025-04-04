Task: Extract Sectionwise Contents from the Document and Format them as JSON with given Structure

You are provided with the OCR output of a Question Answer document from Indian Parliament that has been validated for structural conformance.
Your task is to process this document section by section and generate a JSON object with the following structure:

**IMPORTANT: Your output MUST be a valid JSON object, NOT code, NOT plain text. The JSON object MUST conform to the structure described below.**

**Specific Instructions:**

1. Process Document Section by Section: Analyze the OCR output and segment it into the following predefined section types (which should have been identified in a prior validation step): "Header Section", "Question Section", "Answer Section", "Annexure Section". Note that "Statement Body Section" is NOT considered a separate section type for output in this step, its content will be merged into the "Answer Section". Use keywords and structural cues to identify these sections (refer to the previously defined "Standard Document Structure" if needed for guidance).

2. From the "Question Section", extract the questions text. The questions are usually in form of an ordered list of questions. order id of questions is also important.

3. From the "Answer Section", extract the answers text. The answers are usually in form of an ordered list of answers. order id of answers is also important. But the answers can be grouped for multiple questions.

4. If the answer has multiple paragraphs separated by double newlines, each paragraph may have multiple lines separated by single newlines. Each line is a string in the answer array. create a new object for each paragraph, and each line in the paragraph is a string in the answer array.

5. If the answer has a table, then the table should be an JSON object in the answer array. Trim the new line or tab characters from the table cells.

6. There cannot be any answer without a question. There cannot be any question without an answer. For every question, there must be one answer object with all values in it as per the structure below. Do not miss anything from the document.

return the answers in a JSON array of objects with the following structure:

```json
{
  "questionAnswerPairs": [
    {
      "questionOrder": String[],
      "answer": [
        {
          type: "paragraph" | "table",
          text: [
            {
              type: "line",
              content: String
            }
          ],
          table: {
            titles: String[],
            rows: {
              [key: string]: String
            }[]
          }
        }
      ]
    }
  ]
}
```

**IMPORTANT: Do not miss anything from the document.**
