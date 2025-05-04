# repos/code/loksabha/cli/py/commands/extract_pdf/menu.py

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from pathlib import Path
import sys

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[4]))

from apps.py.utils.project_root import get_loksabha_data_root

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
    
    # Select ministry
    selected_ministry = select_ministry(selected_session)
    if not selected_ministry:
        return
    
    # Display selection summary
    display_selection_summary(selected_sansad, selected_session, selected_ministry)
    
    # Next steps would be to find PDFs and extract them
    print("\nDocument selection will be implemented in the next step.")
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
    """Select a ministry from the given session."""
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
    
    # Ask user to select a ministry
    selected_ministry_path = inquirer.select(
        message=f"Select a Ministry from {session_path.name}:",
        choices=ministry_choices,
    ).execute()
    
    return Path(selected_ministry_path)

def display_selection_summary(sansad, session, ministry):
    """Display a summary of the selected items."""
    print("\nSelected:")
    print(f"  Sansad: {sansad.name}")
    print(f"  Session: {session.name}")
    print(f"  Ministry: {ministry.name}")