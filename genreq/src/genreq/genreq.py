import os
import sys
import ast
import subprocess
from collections import deque
import typer

app = typer.Typer()

def parse_imports_from_files(filepaths: list[str]) -> set[str]:
    """
    Parse imports from Python files and return a set of top-level imported packages.
    """
    imported_packages: set[str] = set()
    filepath: str
    for filepath in filepaths:
        if not os.path.isfile(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            # Skip files that fail to parse
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    top_level: str = n.name.split('.')[0]
                    imported_packages.add(top_level)
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    top_level = node.module.split('.')[0]
                    imported_packages.add(top_level)
    return imported_packages

def get_installed_packages(pip_path: str) -> set[str]:
    """
    Given a pip path, detects all installed packages in a virutal environment.
    """
    try:
        result: int = subprocess.run([pip_path, "freeze"], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=True)
        lines: list[str] = result.stdout.strip().split('\n')
        installed: set[str] = {}
        for line in lines:
            if '==' in line:
                pkg, _ = line.split('==', 1)
                installed[pkg.lower()] = line
        return installed
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error running pip freeze: {e.stderr}", err=True)
        return {}

def find_python_files_recursively(max_depth: int = 4) -> list[str]:
    """
    Recursively search the current directory and subdirectories (up to max_depth) for .py files.
    Ignore 'venv' and '.venv' directories.
    """
    python_files: list[str] = []
    start_dir: str = os.getcwd()
    queue = deque([(start_dir, 0)])
    ignored_dirs: set[str] = {'venv', '.venv'}
    while queue:
        current_dir: str
        depth: int
        current_dir, depth  = queue.popleft()
        if depth > max_depth:
            continue
        for entry in os.scandir(current_dir):
            if entry.is_dir():
                if entry.name not in ignored_dirs and depth < max_depth:
                    queue.append((entry.path, depth + 1))
            elif entry.is_file() and entry.name.endswith('.py'):
                python_files.append(os.path.join(current_dir, entry.name))
    return python_files

def find_virtual_env(custom_venv_name: str = None) -> str | None:
    """
    Locate the virtual environment. If custom_venv_name is given, use that; otherwise use 'venv' or '.venv'.
    """
    if custom_venv_name:
        if os.path.isdir(custom_venv_name):
            return os.path.join(custom_venv_name, "bin", "pip")
        else:
            return None
    else:
        if os.path.isdir("venv"):
            return os.path.join("venv", "bin", "pip")
        elif os.path.isdir(".venv"):
            return os.path.join(".venv", "bin", "pip")
        else:
            return None

@app.command()
def main(
    files: list[str] = typer.Argument(None, help="Python files to analyze. If none provided, searches recursively."),
    add_venv_name: str = typer.Option(None, "--add-venv-name", help="Specify a custom virtual environment directory name."),
    depth: int = typer.Option(4, "--depth", help="Specify your search depth starting from the parent directory.")
):
    """
    Analyze imports in Python files and generate a requirements.txt from installed packages that match those imports.
    Additionally, echo which packages are installed but not imported, and those that are imported but not installed.
    """
    if files:
        files_to_check = [f for f in files if f.endswith('.py') and os.path.isfile(f)]
    else:
        files_to_check = find_python_files_recursively(depth)

    if not files_to_check:
        typer.echo("No Python files found.")
        open("requirements.txt", "w", encoding="utf-8").close()
        sys.exit(0)

    pip_path = find_virtual_env(add_venv_name)
    if pip_path is None:
        if add_venv_name:
            typer.echo(f"No virtual environment found with the name '{add_venv_name}'.", err=True)
        else:
            typer.echo("No virtual environment found. Please create one named 'venv' or '.venv', or use --add-venv-name.", err=True)
        sys.exit(1)

    imported_packages = parse_imports_from_files(files_to_check)
    if not imported_packages:
        typer.echo("No external packages imported.")
        open("requirements.txt", "w", encoding="utf-8").close()
        sys.exit(0)

    installed_packages = get_installed_packages(pip_path)
    matched_requirements = []
    for pkg in sorted(imported_packages):
        pkg_lower = pkg.lower()
        if pkg_lower in installed_packages:
            matched_requirements.append(installed_packages[pkg_lower])
        else:
            typer.echo(f"Warning: Imported package '{pkg}' not found in \
                installed packages.", err=True)

    # Write matched packages to requirements.txt
    with open("requirements.txt", "w", encoding="utf-8") as req_file:
        for line in matched_requirements:
            req_file.write(line + "\n")

    typer.echo("requirements.txt has been generated.")

    # Identify installed but not imported packages
    imported_lower: set[str] = {p.lower() for p in imported_packages}
    unused: set[str] = set(installed_packages.keys()) - imported_lower - {"genreqs"}

    if unused:
        typer.echo("The following packages are installed but not imported:")
        for pkg in sorted(unused):
            typer.echo(pkg)

if __name__ == "__main__":
    app()
