import unittest

from python_parser import parse_python_file


class TestPythonParser(unittest.TestCase):
    def test_parse_python_file(self):
        # Test with a known file
        file_path = "cli/py/extract_pdf/menu.py"
        result = parse_python_file(file_path)

        # Verify basic structure
        self.assertIn("file_path", result)
        self.assertIn("classes", result)
        self.assertIn("functions", result)

        # Verify we found some classes
        self.assertTrue(len(result["classes"]) > 0)

        # Verify class structure
        for cls in result["classes"]:
            self.assertIn("name", cls)
            self.assertIn("docstring", cls)
            self.assertIn("line_range", cls)
            self.assertIn("start", cls["line_range"])
            self.assertIn("end", cls["line_range"])

        # Verify function structure
        for func in result["functions"]:
            self.assertIn("name", func)
            self.assertIn("docstring", func)
            self.assertIn("line_range", func)
            self.assertIn("start", func["line_range"])
            self.assertIn("end", func["line_range"])


if __name__ == "__main__":
    unittest.main()
