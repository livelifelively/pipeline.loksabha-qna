from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from pathlib import Path
import sys
import asyncio
import json
from typing import Dict, Any, List
import time


# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[4]))

from apps.py.utils.project_root import get_loksabha_data_root
# Import but don't call directly - we'll handle async separately
from apps.py.parliament_questions.pdf_extraction import extract_pdf_contents

def pdf_menu():
    """Menu for PDF-related operations."""
    while True:
        # Clear the screen for better UI experience
        print("\033c", end="")
        
        print("PDF Tools")
        print("---------\n")
        
        # PDF submenu selection
        action = inquirer.select(
            message="Select an operation:",
            choices=[
                Choice(value="extract", name="Extract Text from PDF"),
                Choice(value="back", name="Back to Main Menu")
            ],
            default="extract"
        ).execute()
        
        if action == "extract":
            extract_pdf_workflow()
        elif action == "back":
            break

def find_all_document_paths(selected_ministries):
    """Find document paths across all selected ministries."""
    all_document_paths = []
    for ministry in selected_ministries:
        ministry_docs = find_document_paths(ministry)
        all_document_paths.extend(ministry_docs)
    
    return all_document_paths

def confirm_extraction_process(all_document_paths, selected_ministries):
    """Get confirmation from the user to proceed with extraction."""
    print(f"\nFound {len(all_document_paths)} document paths with PDF files across {len(selected_ministries)} ministries.")
    return inquirer.confirm(
        message=f"Do you want to extract text from these {len(all_document_paths)} documents?",
        default=True
    ).execute()

def run_extraction(all_document_paths, extractor_type="marker"):
    """Run the extraction process and return results."""
    return asyncio.run(extract_documents(all_document_paths, extractor_type))

def display_extraction_results(results):
    """Display a summary of extraction results."""
    print("\nExtraction Complete!")
    print(f"Status: {results['status']}")
    print(f"Total documents processed: {results['total_processed']}")
    print(f"Total documents failed: {results['total_failed']}")

def save_extraction_results(results, selected_sansad, selected_session, selected_ministries):
    """Save extraction results to a file if user confirms."""
    save_results = inquirer.confirm(
        message="Do you want to save extraction results summary?",
        default=True
    ).execute()
    
    if save_results:
        # Create timestamp for filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a concise representation of the ministries for the filename
        if len(selected_ministries) == 1:
            ministry_name_for_file = selected_ministries[0].name
        else:
            ministry_name_for_file = f"{selected_ministries[0].name}_and_{len(selected_ministries)-1}_more"
        
        # Create the filename with session and ministry information
        filename = f"extraction_results_{ministry_name_for_file}_{timestamp}.json"
        
        # Save in the session directory
        results_file = selected_session / filename
        
        # Ensure the directory exists
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print(f"Results saved to: {results_file}")
    
    return save_results

def extract_pdf_workflow():
    """Main workflow for PDF extraction."""
    # Get the data root directory
    data_root = get_loksabha_data_root()
    
    # Select sansad
    selected_sansad = select_sansad(data_root)
    if not selected_sansad:
        return
    
    # Select session
    selected_session = select_session(selected_sansad)
    if not selected_session:
        return
    
    # Select ministries (now returns a list)
    selected_ministries = select_ministry(selected_session)
    if not selected_ministries:
        return
    
    # Count documents across all ministries
    all_ministry_docs = []
    ministry_doc_counts = {}
    
    for ministry in selected_ministries:
        ministry_docs = find_document_paths(ministry)
        all_ministry_docs.extend(ministry_docs)
        ministry_doc_counts[ministry.name] = len(ministry_docs)
    
    # Display selection summary with document counts
    display_selection_summary(selected_sansad, selected_session, selected_ministries, 
                             ministry_doc_counts, len(all_ministry_docs))
    
    # Use marker as the default extractor type
    extractor_type = "marker"
    
    # Process each ministry separately
    overall_results = {
        "total_ministries": len(selected_ministries),
        "total_processed": 0,
        "total_failed": 0,
        "ministry_results": []
    }
    
    for ministry in selected_ministries:
        ministry_result = process_ministry(ministry, extractor_type, selected_sansad, selected_session)
        if ministry_result:
            overall_results["total_processed"] += ministry_result["total_processed"]
            overall_results["total_failed"] += ministry_result["total_failed"]
            overall_results["ministry_results"].append({
                "ministry_name": ministry.name,
                "results": ministry_result
            })
    
    # Display overall summary
    print("\nOverall Extraction Results:")
    print(f"Total ministries processed: {len(overall_results['ministry_results'])}/{overall_results['total_ministries']}")
    print(f"Total documents processed: {overall_results['total_processed']}")
    print(f"Total documents failed: {overall_results['total_failed']}")
    
    inquirer.text(message="Press Enter to continue...").execute()

def process_ministry(ministry, extractor_type, selected_sansad, selected_session):
    """Process a single ministry's documents."""
    print(f"\n\nProcessing Ministry: {ministry.name}")
    print("="*50)
    
    # Find document paths for this ministry
    document_paths = find_document_paths(ministry)
    
    if not document_paths:
        print(f"No PDF documents found in ministry: {ministry.name}")
        return None
    
    # Display information and countdown timer
    print(f"Found {len(document_paths)} document paths with PDF files in {ministry.name}.")
    print("Starting extraction in 10 seconds...")
    
    # Countdown timer with option to cancel
    for i in range(10, 0, -1):
        print(f"Starting in {i} seconds... (Press Ctrl+C to cancel)", end="\r")
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExtraction cancelled for ministry: {ministry.name}")
            return None
    
    print("\nStarting extraction for ministry: {ministry.name}".ljust(60))
    
    # Execute the extraction asynchronously
    try:
        print(f"Starting extraction of {len(document_paths)} documents...")
        
        # Run the extraction
        results = asyncio.run(extract_documents(document_paths, extractor_type))
        
        # Display results for this ministry
        print(f"\nExtraction Complete for {ministry.name}!")
        print(f"Status: {results['status']}")
        print(f"Documents processed: {results['total_processed']}")
        print(f"Documents failed: {results['total_failed']}")
        
        # Save results for this ministry automatically
        save_ministry_results(results, selected_sansad, selected_session, ministry)
        
        return results
        
    except Exception as e:
        print(f"\nError during extraction process for {ministry.name}: {str(e)}")
        return None

def save_ministry_results(results, selected_sansad, selected_session, ministry):
    """Save extraction results for a ministry to a file automatically."""
    # Create timestamp for filename
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the filename with ministry information
    filename = f"extraction_results.json"
    
    # Save in the session directory
    results_file = selected_session / 'ministries' / ministry.name / filename
    
    # Ensure the directory exists
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the results
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Results saved to: {results_file}")
    
    return results_file

def select_sansad(data_root):
    """Select a sansad from the data root directory."""
    # Get a list of all sansad directories and sort them
    sansad_dirs = sorted([d for d in data_root.iterdir() if d.is_dir()], key=lambda x: x.name)
    
    if not sansad_dirs:
        print("\nNo sansad directories found in data root.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None
    
    # Create choices for the sansad selection
    sansad_choices = [
        Choice(value=str(d), name=d.name) 
        for d in sansad_dirs
    ]
    
    # Ask user to select a sansad
    selected_sansad_path = inquirer.select(
        message="Select a Sansad/Loksabha:",
        choices=sansad_choices,
    ).execute()
    
    return Path(selected_sansad_path)

def select_session(sansad_path):
    """Select a session from the given sansad."""
    # Get all session directories for the selected sansad and sort them
    session_dirs = sorted([d for d in sansad_path.iterdir() if d.is_dir()], key=lambda x: x.name)
    
    if not session_dirs:
        print(f"\nNo session directories found in {sansad_path.name}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None
    
    # Create choices for the session selection
    session_choices = [
        Choice(value=str(d), name=d.name) 
        for d in session_dirs
    ]
    
    # Ask user to select a session
    selected_session_path = inquirer.select(
        message=f"Select a Session from {sansad_path.name}:",
        choices=session_choices,
    ).execute()
    
    return Path(selected_session_path)

def select_ministry(session_path):
    """Select one or more ministries from the given session."""
    # Check if ministries directory exists
    ministries_dir = session_path / "ministries"
    
    if not ministries_dir.exists() or not ministries_dir.is_dir():
        print(f"\nMinistries directory not found in {session_path.name}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None
    
    # Get ministries and sort them alphabetically by name
    ministry_dirs = sorted([d for d in ministries_dir.iterdir() if d.is_dir()], key=lambda x: x.name)
    
    if not ministry_dirs:
        print(f"\nNo ministry directories found in {ministries_dir}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None
    
    # Create choices for the ministry selection
    ministry_choices = [
        Choice(value=str(d), name=d.name) 
        for d in ministry_dirs
    ]
    
    # Ask user to select multiple ministries using checkbox
    selected_ministry_paths = inquirer.checkbox(
        message=f"Select Ministry/Ministries from {session_path.name}:",
        choices=ministry_choices,
        instruction="(Use space to select, enter to confirm)",
        validate=lambda result: len(result) >= 1 or "Please select at least one ministry"
    ).execute()
    
    # Convert string paths to Path objects
    selected_ministries = [Path(path) for path in selected_ministry_paths]
    
    return selected_ministries

def find_document_paths(ministry_path):
    """Find all document paths within the ministry directory."""
    try:
        # Each subfolder in the ministry directory may contain a PDF file
        document_dirs = [d for d in ministry_path.iterdir() if d.is_dir()]
        
        if not document_dirs:
            print(f"\nNo document directories found in {ministry_path.name}.")
            return []
        
        # Find directories containing PDF files
        pdf_dirs = []
        for doc_dir in document_dirs:
            pdf_files = list(doc_dir.glob("*.pdf"))
            if pdf_files:
                pdf_dirs.append(doc_dir)
        
        return pdf_dirs
    except Exception as e:
        print(f"\nError finding document paths: {str(e)}")
        return []

def display_selection_summary(sansad, session, ministries, ministry_doc_counts, total_docs):
    """Display a summary of the selected items with document counts."""
    print("\nSelected:")
    print(f"  Sansad: {sansad.name}")
    print(f"  Session: {session.name}")
    print(f"  Ministries: {', '.join(ministry.name for ministry in ministries)}")
    print(f"  Total ministries selected: {len(ministries)}")
    print(f"  Total documents to process: {total_docs}")
    
    # Show document count breakdown if there are multiple ministries
    if len(ministries) > 1:
        print("\nDocuments per ministry:")
        for ministry_name, doc_count in ministry_doc_counts.items():
            print(f"  {ministry_name}: {doc_count} document(s)")

# Add new extraction function for CLI
async def extract_documents(document_paths: List[Path], extractor_type: str = "marker"):
    """
    Process PDFs for all documents selected in the CLI.
    
    Args:
        document_paths: List of paths to document directories
        extractor_type: Type of PDF extractor to use
        
    Returns:
        Dict containing extraction results
    """
    total_documents = len(document_paths)
    processed_documents = []
    failed_extractions = []
    
    print(f"\nStarting extraction of {total_documents} documents...")
    
    for i, doc_dir in enumerate(document_paths):
        try:
            # Find PDF file in the document directory
            pdf_files = list(doc_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError(f"No PDF file found in directory: {doc_dir}")
            
            pdf_path = pdf_files[0]  # Take the first PDF if multiple exist
            
            # Show progress
            print(f"Processing [{i+1}/{total_documents}]: {pdf_path.name}")
            
            # Extract contents
            result = await extract_pdf_contents(pdf_path, extractor_type=extractor_type)
            processed_documents.append({
                "path": str(pdf_path),
                "result": result
            })
            
            print(f"  ✓ Extraction successful: {pdf_path.name}")
            
        except Exception as e:
            failed_extractions.append({
                "path": str(doc_dir),
                "error": str(e)
            })
            print(f"  ✗ Extraction failed: {doc_dir.name} - {str(e)}")
    
    status = "SUCCESS" if not failed_extractions else "PARTIAL"
    
    result_summary = {
        "status": status,
        "total_processed": len(processed_documents),
        "total_failed": len(failed_extractions),
        "extracted_documents": processed_documents,
        "failed_extractions": failed_extractions
    }
    
    return result_summary