import logging
from typing import Dict, Any, List
from pathlib import Path

from .types import ParliamentQuestion, PipelineOutput
from .utils.text import clean_text

logger = logging.getLogger(__name__)

async def fetch_meta_analysis_for_questions_pdfs(outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze metadata for downloaded parliament question PDFs.
    
    Args:
        outputs: Pipeline outputs containing downloaded questions
        
    Returns:
        Dict containing cleaned QnA data and analysis status
    """
    downloaded_questions = outputs.get("downloadedSansadSessionQuestions", [])
    
    # Clean and normalize the data
    cleaned_data = []
    for question in downloaded_questions:
        cleaned = {
            "ques_no": question["quesNo"],
            "subjects": clean_text(question["subjects"]),
            "lok_no": clean_text(question["lokNo"]),
            "member": [clean_text(m) for m in question["member"]],
            "ministry": clean_text(question["ministry"]),
            "type": clean_text(question["type"]),
            "date": clean_text(question["date"]),
            "questions_file_path_local": clean_text(question["questionsFilePathLocal"]),
            "questions_file_path_web": clean_text(question["questionsFilePathWeb"]),
            "questions_file_path_hindi_local": clean_text(question.get("questionsFilePathHindiLocal", "")),
            "questions_file_path_hindi_web": clean_text(question.get("questionsFilePathHindiWeb", "")),
            "question_text": clean_text(question.get("questionText", "")),
            "answer_text": clean_text(question.get("answerText", "")),
            "session_no": clean_text(question.get("sessionNo", ""))
        }
        cleaned_data.append(ParliamentQuestion(**cleaned))
    
    return {
        "status": "SUCCESS",
        "cleanedQnAData": [q.dict() for q in cleaned_data]
    }

    # TODO: Implement additional meta-analysis features:
    # - Number of pages
    # - Has table detection
    # - Answer length analysis
    # - Structure conformance check 