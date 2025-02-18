from pathlib import Path
from typing import List

from ..utils.project_root import find_project_root
from .decision_tree import DecisionTreeRunner, TreeNode


def get_available_sansads() -> List[str]:
    """Get list of available sansad numbers"""
    project_root = Path(find_project_root())
    sansad_root = project_root / "sansad"

    if not sansad_root.exists():
        return []

    sansad_dirs = [d for d in sansad_root.glob("*") if d.is_dir()]
    return [d.name for d in sorted(sansad_dirs)]


def get_available_sessions(sansad: str) -> List[str]:
    """Get list of available sessions for a sansad"""
    project_root = Path(find_project_root())
    sansad_dir = project_root / "sansad" / sansad

    if not sansad_dir.exists():
        return ["Back"]

    session_dirs = [d for d in sansad_dir.glob("*") if d.is_dir()]
    choices = [d.name for d in sorted(session_dirs)]

    if not choices:
        print(f"No sessions found for Sansad {sansad}")
        return ["Back"]

    return choices + ["Back"]


def get_available_ministries(sansad: str, session: str) -> List[str]:
    """Get list of available ministries for a sansad session"""
    project_root = Path(find_project_root())
    ministry_dir = project_root / "sansad" / sansad / session / "ministries"

    if not ministry_dir.exists():
        print(f"No ministries found for Sansad {sansad} Session {session}")
        return ["Back"]

    ministry_dirs = [d for d in ministry_dir.glob("*") if d.is_dir()]
    choices = [d.name for d in sorted(ministry_dirs)]

    if not choices:
        return ["Back"]

    # Put "All Ministries" first, followed by individual ministries, then Back
    return ["All Ministries"] + choices + ["Back"]


def create_ministry_selection_node() -> TreeNode:
    """Create ministry selection node with multi-select support"""
    return TreeNode(
        id="ministries",
        message="Select ministries (space to select, enter to confirm)",
        data_provider=lambda: get_available_ministries(
            DecisionTreeRunner.current_decisions.get("sansad", ""),
            DecisionTreeRunner.current_decisions.get("session", ""),
        ),
        is_multi_select=True,
    )
