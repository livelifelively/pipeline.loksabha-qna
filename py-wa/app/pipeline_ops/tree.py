from .decision_tree import DecisionTreeRunner, TreeNode
from .providers import create_ministry_selection_node, get_available_sansads, get_available_sessions


def create_pipeline_ops_tree() -> TreeNode:
    # Ministry selection node
    ministry_node = create_ministry_selection_node()

    # Session selection node
    session_node = TreeNode(
        id="session",
        message="Select Session number",
        data_provider=lambda: get_available_sessions(DecisionTreeRunner.current_decisions.get("sansad", "")),
        next_nodes={"<dynamic>": ministry_node},
    )

    # Sansad selection node
    sansad_node = TreeNode(
        id="sansad",
        message="Select Sansad number",
        data_provider=get_available_sansads,
        next_nodes={"<dynamic>": session_node},
    )

    # Root node - Action selection
    root_node = TreeNode(
        id="action",
        message="Select action",
        choices=["View logs", "Delete logs"],
        next_nodes={"View logs": sansad_node, "Delete logs": sansad_node},
    )

    return root_node
