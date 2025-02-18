from .actions import execute_action
from .decision_tree import DecisionTreeRunner
from .tree import create_pipeline_ops_tree


def main():
    """CLI entry point for pipeline operations"""
    tree = create_pipeline_ops_tree()
    runner = DecisionTreeRunner(tree)
    result = runner.execute()

    if result and result.decisions:
        action = result.decisions.get("action")
        if action:
            execute_action(action, result.decisions)


if __name__ == "__main__":
    main()
