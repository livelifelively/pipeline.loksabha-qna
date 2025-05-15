def print_table(headers, rows, footer=None):
    """
    Print a formatted ASCII table.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of values
        footer: Optional footer row (e.g., for totals)
    """
    # Calculate column widths based on content
    col_widths = []
    for i in range(len(headers)):
        # Width is the max of header, all row values at this index, and footer if present
        header_width = len(str(headers[i]))
        row_width = max([len(str(row[i])) for row in rows]) if rows else 0
        footer_width = len(str(footer[i])) if footer and i < len(footer) else 0
        col_widths.append(max(header_width, row_width, footer_width) + 2)  # +2 for padding

    # Helper function to create horizontal line
    def h_line(char1, char2, char3):
        line = char1
        for width in col_widths:
            line += "─" * width + char2
        return line[:-1] + char3

    # Print table header
    print(h_line("┌", "┬", "┐"))

    # Print header row
    header_str = "│"
    for i, header in enumerate(headers):
        header_str += f" {str(header):<{col_widths[i] - 2}} │"
    print(header_str)

    # Print separator line
    print(h_line("├", "┼", "┤"))

    # Print data rows
    for row in rows:
        row_str = "│"
        for i, cell in enumerate(row):
            row_str += f" {str(cell):<{col_widths[i] - 2}} │"
        print(row_str)

    # Print footer if provided
    if footer:
        print(h_line("├", "┼", "┤"))
        footer_str = "│"
        for i, cell in enumerate(footer):
            footer_str += f" {str(cell):<{col_widths[i] - 2}} │"
        print(footer_str)

    # Print bottom line
    print(h_line("└", "┴", "┘"))
