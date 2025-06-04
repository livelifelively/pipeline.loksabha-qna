import argparse
import ast
import json
from ast import ClassDef, FunctionDef, NodeVisitor, parse
from typing import Dict, List, Optional


class PythonDocstringExtractor(NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[Dict] = []
        self.functions: List[Dict] = []
        self.current_class: Optional[Dict] = None

    def visit_ClassDef(self, node: ClassDef):
        class_info = {
            "name": node.name,
            "docstring": self._get_docstring(node),
            "line_range": {"start": node.lineno, "end": node.end_lineno},
        }
        self.classes.append(class_info)

    def visit_FunctionDef(self, node: FunctionDef):
        function_info = {
            "name": node.name,
            "docstring": self._get_docstring(node),
            "line_range": {"start": node.lineno, "end": node.end_lineno},
        }
        self.functions.append(function_info)

    def _get_docstring(self, node) -> Optional[str]:
        if not node.body or not isinstance(node.body[0], ast.Expr):
            return None
        if not isinstance(node.body[0].value, ast.Str):
            return None
        return node.body[0].value.s.strip()


def parse_python_file(file_path: str) -> Dict:
    """Parse a Python file and extract class and function information."""
    with open(file_path, "r") as f:
        content = f.read()

    tree = parse(content)
    extractor = PythonDocstringExtractor(file_path)
    extractor.visit(tree)

    return {"file_path": file_path, "classes": extractor.classes, "functions": extractor.functions}


def main():
    parser = argparse.ArgumentParser(description="Parse Python files and extract docstrings")
    parser.add_argument("--file", help="Specific Python file to analyze")
    parser.add_argument("--all", action="store_true", help="Analyze all Python files")
    args = parser.parse_args()

    if args.file:
        # Parse specific file
        parsed_data = parse_python_file(args.file)
        print(json.dumps(parsed_data, indent=2))
    elif args.all:
        # TODO: Implement all files analysis
        print("Analyzing all files not implemented yet")
        return
    else:
        # Default: analyze menu.py
        parsed_data = parse_python_file("cli/py/extract_pdf/menu.py")
        print(json.dumps(parsed_data, indent=2))


if __name__ == "__main__":
    main()
