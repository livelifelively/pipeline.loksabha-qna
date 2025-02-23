import asyncio
import os
from pathlib import Path

from google import genai

from .project_root import find_project_root


def init_gemini():
    """Initialize Gemini API with API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


async def extract_text_from_pdf(file_path: Path | str, genai_model: genai.Client) -> str:
    """
    Extract text from a PDF file using Gemini API.

    Args:
        file_path: Path to the PDF file
        genai_model: Initialized Gemini model

    Returns:
        Extracted text content as string
    """
    file = genai_model.files.upload(file=file_path, config={"display_name": "AS61_1FU00j"})

    # prompt = """
    #     Extract the tables from the following PDF file as html.
    #     Do not include any other text or comments.
    #     return the output in JSON array that includes tables as html strings.
    # """

    prompt = """
        Extract the contents of the following PDF file.
        The file has 3 parts:
        - Part 1: Information about the Question
        - Part 2: The Question
        - Part 3: The Answer, including the annexures
        
        These parts appear in the document in sequence.

        For each part, return the text in a JSON array. 
        Text separated by double newlines treat it as a separate entry in the array.
        If you encounter a new line, treat it as continuation of the current text and remove the new line characters (\n) from the text.

        If you encounter a table, return the table in html format. Do not return the table in markdown format.
        Preserve the structure of the table as it is in the PDF file.

        Preserve the order of parts of the document
        Preserve the order of text in each part.

        Result should be an array of three arrays, one for each part. 
        And each part array should have the text in the order it appears in the PDF file.

        Do not include any other text or comments.
    """

    # prompt = """
    #     Extract the contents of the following PDF file in html format.
    #     Do not include any other text or comments.
    #     The output must be in html format.
    #     Try to keep the structure of the content same as it is in the PDF file.
    # """
    response = genai_model.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, file],
        config=genai.types.GenerateContentConfig(response_mime_type="application/json"),
    )

    return response.text


async def main():
    # Fixed test file path
    file_path = Path(Path(find_project_root())) / "sansad/18/iv/ministries/health-and-family-welfare/61/AS61_1FU00j.pdf"
    print(file_path)

    # # Setup Gemini client
    api_key = os.getenv("GEMINI_API_KEY")
    print(api_key)
    # if not api_key:
    #     raise ValueError("Environment variable 'GEMINI_API_KEY' not set")

    client = genai.Client(api_key=api_key)
    print(client)

    try:
        result = await extract_text_from_pdf(file_path, client)
        print(result)
    except Exception as e:
        print(f"Error extracting text: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
