import logging
from typing import Dict, Any, List
from pathlib import Path

from .types import ParliamentQuestion, PipelineOutput
from .utils.text import clean_text
from .context import PipelineContext

logger = logging.getLogger(__name__)

async def fetch_meta_analysis_for_questions_pdfs(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Fetch meta analysis for downloaded question PDFs.
    
    Args:
        outputs: Pipeline outputs containing downloaded questions
        context: Pipeline context for logging
        
    Returns:
        Dict containing analysis status and results
    """
    downloaded_questions = outputs.get("downloadedSansadSessionQuestions", [])
    
    context.log_step("analysis_start", 1, "Meta Analysis", 
        total_questions=len(downloaded_questions)
    )
    
    try:
        analyzed_data = []
        failed_analysis = []
        
        for i, question in enumerate(downloaded_questions):
            try:
                analysis = await analyze_question_pdf(question)
                analyzed_data.append(analysis)
                
                context.log_step("question_analyzed", 1, "Meta Analysis",
                    question_id=question.id,
                    progress=f"{i+1}/{len(downloaded_questions)}"
                )
                
            except Exception as e:
                failed_analysis.append({
                    "question": question.dict(),
                    "error": str(e)
                })
                context.log_step("question_analysis_failed", 1, "Meta Analysis",
                    question_id=question.id,
                    error=str(e)
                )
        
        status = "SUCCESS" if not failed_analysis else "PARTIAL"
        
        return {
            "status": status,
            "cleanedQnAData": analyzed_data,
            "failedAnalysis": failed_analysis
        }
        
    except Exception as e:
        context.log_step("analysis_failed", 1, "Meta Analysis",
            error=str(e)
        )
        return {
            "status": "FAILURE",
            "error": str(e)
        }

    # TODO: Implement additional meta-analysis features:
    # - Number of pages
    # - Has table detection
    # - Answer length analysis
    # - Structure conformance check 