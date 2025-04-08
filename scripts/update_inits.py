#!/usr/bin/env python3
"""Script to automatically generate __init__.py files for the project."""
from pathlib import Path
import re
from typing import List

def is_python_file(path: Path) -> bool:
    """Check if a file is a Python file (excluding __init__.py)."""
    return path.is_file() and path.suffix == '.py' and path.stem != '__init__'

def get_exports(file_path: Path) -> List[str]:
    """Extract classes and functions that should be exported."""
    content = file_path.read_text()
    # Match class and function definitions that don't start with _
    pattern = r'^(?:class|def)\s+([A-Z][a-zA-Z0-9_]*|[a-z][a-zA-Z0-9_]*(?:_[a-zA-Z0-9_]+)*)\s*[:\(]'
    matches = re.finditer(pattern, content, re.MULTILINE)
    return [m.group(1) for m in matches if not m.group(1).startswith('_')]

def update_init_file(directory: Path) -> None:
    """Update the __init__.py file in the given directory."""
    init_file = directory / '__init__.py'
    python_files = [f for f in directory.iterdir() if is_python_file(f)]
    
    exports = []
    for file in python_files:
        module_exports = get_exports(file)
        if module_exports:
            relative_import = f"from .{file.stem} import {', '.join(module_exports)}"
            exports.append(relative_import)
    
    if exports:
        content = "\n".join([
            '"""Auto-generated exports."""',
            *exports,
            "",  # trailing newline
            f"__all__ = {sorted(sum((e.split('import ')[1].split(', ') for e in exports), []))!r}",
            ""
        ])
        init_file.write_text(content)

def main():
    """Main function to update all __init__.py files in the project."""
    src_dir = Path("src")
    # Update src directory itself
    if src_dir.is_dir() and list(src_dir.glob("*.py")):
        print(f"Updating {src_dir}/__init__.py")
        update_init_file(src_dir)
    
    # Update all subdirectories
    for directory in src_dir.rglob("**/"):
        if directory.is_dir() and list(directory.glob("*.py")):
            print(f"Updating {directory}/__init__.py")
            update_init_file(directory)

if __name__ == "__main__":
    main()