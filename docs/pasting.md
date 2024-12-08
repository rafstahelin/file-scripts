# JupyterLab Python Code Formatting Guide

[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

## Table of Contents
- [Text Editors](#text-editors)
- [Jupyter Magic Commands](#jupyter-magic-commands)
- [Code Formatters](#code-formatters)
- [Best Practices](#best-practices)

## Text Editors

### Nano
Simple and reliable text editor that preserves indentation:
```bash
# Open file in nano
nano /workspace/file-scripts/tools/your_script.py

# Nano commands:
# Ctrl + O : Save file
# Ctrl + X : Exit
# Ctrl + K : Cut line/selection
# Ctrl + U : Paste
```

### Vim
Advanced text editor with powerful formatting capabilities:
```bash
# Open file in vim
vim /workspace/file-scripts/tools/your_script.py

# Vim commands:
# :w   - Save file
# :q   - Quit
# :wq  - Save and quit
# :set paste  - Enter paste mode (preserves formatting)
# :set nopaste - Exit paste mode
```

## Jupyter Magic Commands

### %%writefile
Writes cell contents directly to a file:
```python
# Create new file
%%writefile /workspace/file-scripts/tools/new_script.py
def hello():
    print("Hello World")

# Append to existing file
%%writefile -a /workspace/file-scripts/tools/existing_script.py
def new_function():
    print("Adding this function")
```

### Raw NBConvert
Alternative to preserve formatting:
1. Click cell format dropdown
2. Select "Raw NBConvert"
3. Paste code
4. Change back to "Code" when done

## Code Formatters

### autopep8
PEP 8 compliant code formatter:
```bash
# Installation
pip install autopep8

# Basic usage (safe changes)
autopep8 --in-place script.py

# Aggressive mode (more changes)
autopep8 --in-place --aggressive script.py

# Very aggressive mode (most thorough)
autopep8 --in-place --aggressive --aggressive script.py

# Preview changes without modifying
autopep8 --diff script.py

# Format multiple files
autopep8 --in-place --recursive .
```

### black
Opinionated code formatter:
```bash
# Installation
pip install black

# Format a file
black script.py

# Preview changes
black --diff script.py

# Set line length (default is 88)
black --line-length 79 script.py

# Format entire directory
black .

# Format multiple files
black script1.py script2.py
```

## Best Practices

### Workflow Recommendations
1. For quick edits:
   ```bash
   nano script.py
   ```

2. For large code blocks in Jupyter:
   ```python
   %%writefile script.py
   # paste code here
   ```

3. For fixing formatting issues:
   ```bash
   # Either
   autopep8 --in-place --aggressive --aggressive script.py
   # Or
   black script.py
   ```

### Fixing Common Issues

1. Indentation Problems:
   ```bash
   # Use autopep8 for gentle fixes
   autopep8 --in-place script.py
   
   # Use black for strict formatting
   black script.py
   ```

2. Line Length Issues:
   ```bash
   # autopep8 with line length
   autopep8 --in-place --max-line-length 79 script.py
   
   # black with line length
   black --line-length 79 script.py
   ```

3. Import Sorting:
   ```bash
   # Install isort
   pip install isort
   
   # Sort imports
   isort script.py
   ```

### Tool Selection Guide

1. Use `nano` when:
   - Making quick edits
   - Working in terminal
   - Need to preserve exact formatting

2. Use `%%writefile` when:
   - Working in Jupyter
   - Creating new files
   - Need to preserve indentation

3. Use `autopep8` when:
   - Want gradual formatting
   - Need PEP 8 compliance
   - Want control over aggressiveness

4. Use `black` when:
   - Want consistent formatting
   - Working on team projects
   - Don't need formatting customization

## Version Control Integration

When using with git:
```bash
# Add pre-commit hooks
pip install pre-commit

# Create .pre-commit-config.yaml
repos:
-   repo: https://github.com/psf/black
    rev: stable
    hooks:
    - id: black
-   repo: https://github.com/pycqa/isort
    rev: 5.6.4
    hooks:
    - id: isort
```

## Additional Resources
- [Black Documentation](https://black.readthedocs.io/)
- [autopep8 Documentation](https://github.com/hhatto/autopep8)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Jupyter Documentation](https://jupyter.org/documentation)