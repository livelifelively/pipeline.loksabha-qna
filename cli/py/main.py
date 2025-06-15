#!/usr/bin/env python3
"""
Loksabha CLI
A command-line tool for various Loksabha data processing tasks.
"""

import sys
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[3]))

# Import the PDF extraction menu and reports menu
from cli.py.extract_pdf.menu import pdf_menu, reports_menu


def main():
    """Main entry point for the CLI."""
    while True:
        # Clear the screen for better UI experience
        print("\033c", end="")

        print("Loksabha CLI")
        print("-----------")
        print("Version: 0.1.0\n")

        # Main menu selection using dropdown
        action = inquirer.select(
            message="Select an operation:",
            choices=[
                Choice(value="pdf", name="PDF Tools"),
                Choice(value="reports", name="Reports"),
                Choice(value="quit", name="Quit"),
            ],
            default="pdf",
        ).execute()

        if action == "pdf":
            pdf_menu()
        elif action == "reports":
            reports_menu()
        elif action == "quit":
            print("Exiting Loksabha CLI. Goodbye!")
            break


if __name__ == "__main__":
    main()
