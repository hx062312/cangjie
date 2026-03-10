"""Utility functions for CodeQL location parsing and file operations."""

from typing import Tuple, List


def parse_location(location: str) -> Tuple[str, int, int, int, int]:
    """Parse CodeQL output location string.

    Location format: filename:startLine:startColumn:endLine:endColumn
    Example: /path/to/file.java:10:5:15:20

    Returns:
        Tuple of (path, start_line, start_col, end_line, end_col)
    """
    # Find the first colon (after drive letter on Windows, or just the path separator)
    first_colon = location.find(":")
    second_colon = location.find(":", first_colon + 1)

    path = location[first_colon + 1:second_colon]

    # Parse line and column numbers
    rest = location[second_colon + 1:]
    parts = rest.split(":")

    start_line = int(parts[0])
    start_col = int(parts[1])
    end_line = int(parts[2])
    end_col = int(parts[3])

    return path, start_line, start_col, end_line, end_col


def parse_location_simple(location: str) -> Tuple[str, int]:
    """Parse location string to get path and start line only.

    Returns:
        Tuple of (path, start_line)
    """
    path, start_line, _, _, _ = parse_location(location)
    return path, start_line


def parse_location_with_end(location: str) -> Tuple[str, int, int]:
    """Parse location string to get path, start line, and end line.

    Returns:
        Tuple of (path, start_line, end_line)
    """
    path, start_line, _, end_line, _ = parse_location(location)
    return path, start_line, end_line


def read_file_lines(path: str, start: int, end: int) -> List[str]:
    """Read specified lines from a file.

    Args:
        path: File path
        start: Start line number (1-based, inclusive)
        end: End line number (1-based, inclusive)

    Returns:
        List of lines (empty list if file not found or invalid range)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Convert to 0-based indexing
            return lines[start - 1:end]
    except (FileNotFoundError, IOError, IndexError):
        return []


def read_file_lines_safe(path: str, start: int, end: int) -> Tuple[List[str], bool]:
    """Read specified lines from a file with error handling.

    Args:
        path: File path
        start: Start line number (1-based, inclusive)
        end: End line number (1-based, inclusive)

    Returns:
        Tuple of (lines, success)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Convert to 0-based indexing
            return lines[start - 1:end], True
    except (FileNotFoundError, IOError, IndexError):
        return [], False


# Termination patterns for searching callable bodies
START_TERMINATIONS = ["*/", "@", "}"]
END_TERMINATIONS = [";", "}", "*/", "{"]


def find_callable_body(path: str, start_line: int, end_line: int) -> Tuple[List[str], int]:
    """Find and adjust callable body from source file.

    This function reads the callable body and adjusts the start line
    to find the actual method/constructor declaration.

    Args:
        path: Source file path
        start_line: Initial start line (1-based)
        end_line: End line (1-based)

    Returns:
        Tuple of (callable_body_lines, adjusted_start_line)
    """
    callable_body = read_file_lines(path, start_line, end_line)

    if not callable_body:
        return [], start_line

    searched = False
    while not (
        any(callable_body[0].strip().startswith(x) for x in START_TERMINATIONS)
        or any(callable_body[0].strip().endswith(x) for x in END_TERMINATIONS)
    ):
        searched = True
        start_line -= 1
        callable_body = read_file_lines(path, start_line, end_line)

    if searched:
        start_line += 2
        callable_body = read_file_lines(path, start_line, end_line)

        # Skip empty lines at the beginning
        for i in range(len(callable_body)):
            if callable_body[i].strip() == "":
                start_line += 1
            if callable_body[i].strip() != "":
                break
    else:
        start_line += 1

    callable_body = read_file_lines(path, start_line, end_line)
    return callable_body, start_line


def expand_callable_body(path: str, start_line: int, end_line: int) -> Tuple[List[str], int, int]:
    """Expand callable body until it contains actual code.

    Used when start == end initially to find the complete method body.

    Args:
        path: Source file path
        start_line: Start line (1-based)
        end_line: End line (1-based)

    Returns:
        Tuple of (callable_body, start_line, end_line)
    """
    callable_body = read_file_lines(path, start_line, end_line)

    while ";" not in "".join(callable_body) and "{" not in "".join(callable_body):
        end_line += 1
        callable_body = read_file_lines(path, start_line, end_line)

    return callable_body, start_line, end_line
