from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from pathlib import Path
import sys
import asyncio
import json
from typing import Dict, Any, List

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
    
    # Display selection summary
    display_selection_summary(selected_sansad, selected_session, selected_ministries)
    
    # Find document paths across all selected ministries
    all_document_paths = []
    for ministry in selected_ministries:
        ministry_docs = find_document_paths(ministry)
        all_document_paths.extend(ministry_docs)
    
    if not all_document_paths:
        print("\nNo PDF documents found to extract across selected ministries.")
        inquirer.text(message="Press Enter to continue...").execute()
        return
    
    # Select extractor type
    # extractor_type = inquirer.select(
    #     message="Select PDF extractor type:",
    #     choices=[
    #         Choice(value="marker", name="Marker PDF (recommended)"),
    #         Choice(value="pdfplumber", name="PDF Plumber"),
    #         Choice(value="pypdf", name="PyPDF")
    #     ],
    #     default="marker"
    # ).execute()
    extractor_type = "marker"
    
    # Confirm extraction
    print(f"\nFound {len(all_document_paths)} document paths with PDF files across {len(selected_ministries)} ministries.")
    confirm = inquirer.confirm(
        message=f"Do you want to extract text from these {len(all_document_paths)} documents?",
        default=True
    ).execute()
    
    if not confirm:
        print("\nExtraction cancelled.")
        inquirer.text(message="Press Enter to continue...").execute()
        return
    
    # Execute the extraction asynchronously
    try:
        # Run the async extraction in the event loop
        results = asyncio.run(extract_documents(all_document_paths, extractor_type))
        
        # Display results
        print("\nExtraction Complete!")
        print(f"Status: {results['status']}")
        print(f"Total documents processed: {results['total_processed']}")
        print(f"Total documents failed: {results['total_failed']}")
        
        # Save results summary if requested
        save_results = inquirer.confirm(
            message="Do you want to save extraction results summary?",
            default=True
        ).execute()
        
        if save_results:
            # Create timestamp for filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = data_root / f"extraction_results_{timestamp}.json"
            
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
                
            print(f"Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\nError during extraction process: {str(e)}")
    
    inquirer.text(message="Press Enter to continue...").execute()

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

def display_selection_summary(sansad, session, ministries):
    """Display a summary of the selected items."""
    print("\nSelected:")
    print(f"  Sansad: {sansad.name}")
    print(f"  Session: {session.name}")
    print(f"  Ministries: {', '.join(ministry.name for ministry in ministries)}")
    print(f"  Total ministries selected: {len(ministries)}")

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