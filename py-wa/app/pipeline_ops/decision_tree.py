from typing import Callable, Dict, List, Optional, Union

import inquirer
from pydantic import BaseModel, Field


class TreeNode(BaseModel):
    """Represents a node in the decision tree"""

    id: str = Field(..., description="Unique identifier for the node")
    message: str = Field(..., description="Message to display to user")
    choices: List[str] = Field(default_factory=list, description="Static choices for the node")
    next_nodes: Dict[str, "TreeNode"] = Field(default_factory=dict, description="Mapping of choice to next node")
    data_provider: Optional[Callable[[], List[str]]] = Field(None, description="Function that returns dynamic choices")
    is_multi_select: bool = Field(default=False, description="Whether multiple choices can be selected")

    class Config:
        arbitrary_types_allowed = True


class DecisionConfig(BaseModel):
    """Configuration built from user decisions"""

    decisions: Dict[str, Union[str, List[str]]] = Field(
        default_factory=dict, description="Map of node IDs to chosen values"
    )


class DecisionTreeRunner:
    current_decisions: Dict[str, Union[str, List[str]]] = {}  # Class variable for providers to access

    def __init__(self, root: TreeNode):
        self.root = root
        self._decisions: Dict[str, Union[str, List[str]]] = {}
        DecisionTreeRunner.current_decisions = {}  # Reset class variable on initialization

    def _get_choices(self, node: TreeNode) -> List[str]:
        """Get choices for a node, either from provider or static choices"""
        choices = node.data_provider() if node.data_provider else node.choices
        return [c for c in choices if c not in ["Back", "Exit"]]

    def _create_questions(self, node: TreeNode, choices: List[str], has_parent: bool) -> List[Dict]:
        """Create appropriate questions based on node type"""
        if node.is_multi_select:
            # First question for multi-select choices
            questions = [inquirer.Checkbox("selections", message=node.message, choices=choices)]
            # Second question for navigation
            nav_choices = []
            if has_parent:
                nav_choices.append("Back")
            nav_choices.append("Exit")
            nav_choices.append("Continue")

            questions.append(inquirer.List("choice", message="Select action", choices=nav_choices, default="Continue"))
        else:
            if has_parent:
                choices.append("Back")
            choices.append("Exit")
            questions = [inquirer.List("choice", message=node.message, choices=choices)]
        return questions

    def _handle_navigation(self, answer: Dict, node_stack: List[TreeNode]) -> Optional[TreeNode]:
        """Handle navigation choices (Back/Exit)"""
        if answer.get("go_back") or answer["choice"] == "Back":
            if node_stack:
                current_node = node_stack.pop()
                if current_node.id in self._decisions:
                    del self._decisions[current_node.id]
                    del DecisionTreeRunner.current_decisions[current_node.id]  # Use class variable
                return current_node
            return None
        return None if answer["choice"] == "Exit" else False

    def _process_multi_select(self, choices: List[str], selected: List[str]) -> List[str]:
        """Process multi-select choices, handling 'All Ministries' special case"""
        if not selected:
            return []
        if "All Ministries" in selected:
            return [c for c in choices if c not in ["All Ministries", "Back", "Exit"]]
        return selected

    def execute(self) -> Optional[DecisionConfig]:
        """Walk through the decision tree and collect choices"""
        current_node = self.root
        node_stack = []

        while current_node:
            try:
                choices = self._get_choices(current_node)
                if not choices:
                    print(f"No options available for {current_node.message}")
                    current_node = node_stack.pop() if node_stack else None
                    continue

                questions = self._create_questions(current_node, choices, bool(node_stack))
                answer = inquirer.prompt(questions)
                if not answer:
                    return None

                if current_node.is_multi_select:
                    # Handle navigation choice first
                    if answer["choice"] == "Exit":
                        return None
                    if answer["choice"] == "Back":
                        if node_stack:
                            current_node = node_stack.pop()
                            if current_node.id in self._decisions:
                                del self._decisions[current_node.id]
                                del DecisionTreeRunner.current_decisions[current_node.id]
                            continue
                        return None
                    # Process selections if continuing
                    if answer["choice"] == "Continue":
                        selections = answer["selections"]
                        choice = self._process_multi_select(choices, selections)
                        self._decisions[current_node.id] = choice
                        DecisionTreeRunner.current_decisions[current_node.id] = choice
                        next_key = "<dynamic>"
                else:
                    nav_result = self._handle_navigation(answer, node_stack)
                    if nav_result is None:  # Exit was chosen
                        return None
                    if nav_result:  # Back was chosen
                        current_node = nav_result
                        continue

                    choice = answer["choice"]
                    self._decisions[current_node.id] = choice
                    DecisionTreeRunner.current_decisions[current_node.id] = choice
                    next_key = choice

                next_node = current_node.next_nodes.get(next_key) or current_node.next_nodes.get("<dynamic>")
                if next_node:
                    node_stack.append(current_node)
                    current_node = next_node
                else:
                    break

            except Exception as e:
                print(f"Error at node {current_node.id}: {str(e)}")
                return None

        return DecisionConfig(decisions=self._decisions)
