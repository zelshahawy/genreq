import os
import sys
import ast
import subprocess
from subprocess import CompletedProcess
from collections import deque
import argparse
from typing import Optional
import importlib.util
import sysconfig

def is_std_lib(module_name: str) -> bool:
    """
    Return True if module_name is part of the stdlib (builtin or stdlib path).
    """
    if module_name in sys.builtin_module_names:
        return True
    spec = importlib.util.find_spec(module_name)
    if not spec or not spec.origin:
        return False
    stdlib_dir = sysconfig.get_paths()['stdlib']
    return spec.origin.startswith(stdlib_dir)

def parse_imports_from_files(filepaths: list[str]) -> set[str]:
    """
    Parse imports from Python files and return a set of top-level imported packages.
    """
    imported_packages: set[str] = set()
    for filepath in filepaths:
        if not os.path.isfile(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imported_packages.add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_packages.add(node.module.split('.')[0])
    return imported_packages

def get_installed_packages(pip_path: str) -> dict[str, str]:
    """
    Given a pip path, detect all installed packages in a virtual environment.
    """
    try:
        result: CompletedProcess = subprocess.run(
            [pip_path, "freeze"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        installed: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            if '==' in line:
                pkg, _ = line.split('==', 1)
                installed[pkg.lower()] = line
        return installed
    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e.stderr}", file=sys.stderr)
        return {}

def find_python_files_recursively(max_depth: int = 4) -> list[str]:
    """
    Recursively search for .py files up to max_depth, skipping venv directories.
    """
    python_files: list[str] = []
    start_dir: str = os.getcwd()
    queue: deque = deque([(start_dir, 0)])
    ignored_dirs = {'venv', '.venv'}
    while queue:
        current_dir, depth = queue.popleft()
        if depth > max_depth:
            continue
        for entry in os.scandir(current_dir):
            if entry.is_dir() and entry.name not in ignored_dirs:
                queue.append((entry.path, depth + 1))
            elif entry.is_file() and entry.name.endswith('.py'):
                python_files.append(entry.path)
    return python_files

def find_virtual_env(custom_venv_name: Optional[str]) -> Optional[str]:
    """
    Locate the virtual environment pip executable.
    """
    if custom_venv_name:
        if os.path.isdir(custom_venv_name):
            return os.path.join(custom_venv_name, "bin", "pip")
        return None
    for name in ("venv", ".venv"):
        if os.path.isdir(name):
            return os.path.join(name, "bin", "pip")
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Analyze imports in Python files and generate requirements.txt"
    )
    parser.add_argument(
        "files", nargs="*", help="Python files to analyze. If none provided, searches recursively."
    )
    parser.add_argument(
        "--add-venv-name", dest="add_venv_name",
        help="Specify a custom virtual environment directory name."
    )
    parser.add_argument(
        "--depth", type=int, default=4,
        help="Maximum directory depth to search for Python files."
    )
    args = parser.parse_args()
    files, add_venv_name, depth = args.files, args.add_venv_name, args.depth

    if files:
        files_to_check = [f for f in files if f.endswith('.py') and os.path.isfile(f)]
    else:
        files_to_check = find_python_files_recursively(depth)

    if not files_to_check:
        print("No Python files found.")
        open("requirements.txt", "w", encoding="utf-8").close()
        sys.exit(0)

    pip_path = find_virtual_env(add_venv_name)
    if pip_path is None:
        if add_venv_name:
            print(f"No virtual environment named '{add_venv_name}' found.", file=sys.stderr)
        else:
            print(
                "No virtual environment found. Create one named 'venv' or '.venv', or use --add-venv-name.",
                file=sys.stderr
            )
        sys.exit(1)

    imported_packages = parse_imports_from_files(files_to_check)
    imported_packages = filter(
        lambda pkg: not is_std_lib(pkg) and pkg not in {"genreq", "__main__"},
        imported_packages
    )

    if not imported_packages:
        print("No external packages imported.")
        open("requirements.txt", "w", encoding="utf-8").close()
        sys.exit(0)

    installed_packages = get_installed_packages(pip_path)
    matched_requirements: list[str] = []
    unmatched_imports: list[str] = []

    for pkg in sorted(imported_packages):
        if pkg.lower() in installed_packages:
            matched_requirements.append(installed_packages[pkg.lower()])
        else:
            unmatched_imports.append(pkg)
            print(
                f"Warning: Package '{pkg}' is imported but not installed\n. "
                "Set ALLOW_PKGS=1 to include it in requirements.txt."
            )

    with open("requirements.txt", "w", encoding="utf-8") as req_file:
        for line in matched_requirements:
            req_file.write(line + "\n")
        if unmatched_imports and os.getenv("ALLOW_PKGS") == "1":
            for pkg in unmatched_imports:
                req_file.write(f"{pkg}\n")

    print("requirements.txt has been generated.")

    imported_lower = {p.lower() for p in imported_packages}
    unused = set(installed_packages.keys()) - imported_lower - {"genreq"}
    if unused:
        print("\nThe following packages are installed but not directly imported:")
        for pkg in sorted(unused):
            print(pkg)

if __name__ == "__main__":
    main()
