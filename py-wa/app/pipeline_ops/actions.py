import shutil
from pathlib import Path
from typing import Dict, List, Union

import inquirer

from ..utils.project_root import find_project_root


def delete_pipeline_logs(decisions: Dict[str, Union[str, List[str]]]) -> None:
    """Delete pipeline logs for selected ministries"""
    sansad = decisions.get("sansad")
    session = decisions.get("session")
    ministries = decisions.get("ministries", [])

    if not all([sansad, session, ministries]):
        print("Missing required selections")
        return

    project_root = Path(find_project_root())
    base_path = project_root / "sansad" / sansad / session

    # List all log directories to be deleted
    log_dirs = []

    # Add sansad session level pipeline logs
    sansad_logs = base_path / "sansad-session-pipeline-logs"
    if sansad_logs.exists():
        log_dirs.append(sansad_logs)

    # Add ministry level pipeline logs
    for ministry in ministries:
        ministry_path = base_path / "ministries" / ministry
        if ministry_path.exists():
            for log_dir in ministry_path.glob("**/pipeline-logs"):
                log_dirs.append(log_dir)

    if not log_dirs:
        print("No pipeline logs found to delete")
        return

    # Show confirmation with list of directories
    print("\nFollowing pipeline log directories will be deleted:")
    for log_dir in log_dirs:
        print(f"- {log_dir.relative_to(project_root)}")

    questions = [inquirer.Confirm("confirm", message="Do you want to proceed with deletion?", default=False)]

    answers = inquirer.prompt(questions)
    if not answers or not answers["confirm"]:
        print("Operation cancelled")
        return

    # Proceed with deletion
    for log_dir in log_dirs:
        try:
            shutil.rmtree(log_dir)
            print(f"✓ Deleted: {log_dir.relative_to(project_root)}")
        except Exception as e:
            print(f"✗ Error deleting {log_dir.relative_to(project_root)}: {str(e)}")


def execute_action(action: str, decisions: Dict[str, Union[str, List[str]]]) -> None:
    """Execute the selected action with given decisions"""
    if action == "Delete logs":
        delete_pipeline_logs(decisions)
    else:
        print(f"Action {action} not implemented yet")
