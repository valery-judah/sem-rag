import re

files = [
    "src/doc_forge/evaluation/systems.py",
    "src/doc_forge/query/answer_generation.py",
    "src/doc_forge/query/answer_mode_policy.py",
    "src/doc_forge/query/citation_rendering.py",
    "src/doc_forge/query/context_assembly.py",
    "src/doc_forge/query/interpretation.py",
    "src/doc_forge/query/persistence.py",
    "src/doc_forge/query/retrieval.py",
    "src/doc_forge/query/selection.py",
    "src/doc_forge/query/support_assessment.py",
    "src/doc_forge/readmodels/documents.py",
]

for f in files:
    with open(f) as fd:
        content = fd.read()

    # We want to find functions that only have a docstring or pass and replace with docstring
    # + `...`. But actually, they might be in Protocols or abstract base classes.
    # A simple regex for Pyright's missing return when it's just a docstring:
    # `    def my_method(...) -> ReturnType:\n        """docstring"""\n`
    # We replace it by adding `        ...\n` right after the docstring.

    lines = content.split("\n")
    new_lines = []
    in_def = False
    def_indent = ""
    for _i, line in enumerate(lines):
        new_lines.append(line)
        if re.match(r"^(\s*)def .+", line):
            def_indent = re.match(r"^(\s*)def .+", line).group(1)
        elif '"""' in line and line.strip().endswith('"""'):
            # It's a single-line docstring, or the end of a multi-line docstring.
            # If the next line isn't `...` and we are in a Protocol/ABC...
            pass
