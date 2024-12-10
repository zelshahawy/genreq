
# GenReqs

**GenReqs** is a Python tool that automatically detects the Python packages used in your project and generates a `requirements.txt` file. It also highlights packages installed in your virtual environment but not imported in your code, helping you keep your dependencies clean and manageable.

---

## Features

- Automatically scans Python files for imported packages.
- Cross-references imported packages with installed packages in your virtual environment.
- Generates a `requirements.txt` file with exact package versions.
- Identifies and lists packages installed but not used in your project.
- Supports specifying a custom virtual environment directory.

---

## Installation

### Using `pip`
First, make sure you have Python 3.7 or later installed. Then, install `genreqs` using `pip`:

```bash
pip install genreqs
```

Alternatively, clone the repository and install the package locally:

```bash
git clone https://github.com/zelshahawy/genreqs.git
cd genreqs
python -m build
pip install dist/genreqs-*.whl
```

---

## Usage

### Basic Usage

Run `genreqs` to scan all `.py` files in the current directory and subdirectories (up to a depth of 4) and generate a `requirements.txt` file:

```bash
genreqs
```

### Analyze Specific Files

You can analyze specific Python files by passing them as arguments:

```bash
genreqs file1.py file2.py
```

### Specify a Custom Virtual Environment

If your virtual environment is not named `venv` or `.venv`, you can specify its name using the `--add-venv-name` option:

```bash
genreqs --add-venv-name myenv
```

### Output Example

After running the tool, you’ll get:
1. A `requirements.txt` file containing:
   ```
   pandas==1.5.2
   requests==2.28.1
   ```
2. A console output listing unused installed packages:
   ```
   The following packages are installed but not imported:
   flask
   numpy
   ```

---

## Development Setup

To set up a local development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/zelshahawy/genreqs.git
   cd genreqs
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```

4. Run tests (requires `pytest`):
   ```bash
   pytest
   ```

---

## Contributing

We welcome contributions! To contribute:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed explanation of your changes.

---

## License

This project is licensed under the **BSD License**. See the [LICENSE](LICENSE) file for details.

---

## Links

- **GitHub Repository:** [https://github.com/zelshahawy/genreqs](https://github.com/zelshahawy/genreqs)
- **Report Issues:** [https://github.com/zelshahawy/genreqs/issues](https://github.com/zelshahawy/genreqs/issues)

---

Feel free to tweak this as necessary to fit your project!
