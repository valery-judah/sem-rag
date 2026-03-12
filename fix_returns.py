import re

files = [
    "src/parity/evaluation/systems.py",
    "src/parity/query/answer_generation.py",
    "src/parity/query/answer_mode_policy.py",
    "src/parity/query/citation_rendering.py",
    "src/parity/query/context_assembly.py",
    "src/parity/query/interpretation.py",
    "src/parity/query/persistence.py",
    "src/parity/query/retrieval.py",
    "src/parity/query/selection.py",
    "src/parity/query/support_assessment.py",
    "src/parity/readmodels/documents.py",
]

for f in files:
    with open(f) as fd:
        content = fd.read()

    # We want to find functions that only have a docstring or pass and replace with docstring + `...`
    # But actually, they might be in Protocols or abstract base classes.
    # A simple regex for Pyright's missing return when it's just a docstring:
    # `    def my_method(...) -> ReturnType:\n        """docstring"""\n`
    # We replace it by adding `        ...\n` right after the docstring.

    lines = content.split("\n")
    new_lines = []
    in_def = False
    def_indent = ""
    for i, line in enumerate(lines):
        new_lines.append(line)
        if re.match(r"^(\s*)def .+", line):
            def_indent = re.match(r"^(\s*)def .+", line).group(1)
        elif '"""' in line and line.strip().endswith('"""'):
            # It's a single-line docstring, or the end of a multi-line docstring.
            # If the next line isn't `...` and we are in a Protocol/ABC...
            pass
