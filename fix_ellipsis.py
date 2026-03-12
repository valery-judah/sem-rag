import re


def fix_file(path):
    with open(path) as f:
        content = f.read()

    # match `def method(self...) -> Type:\n    """docstring"""\n\n`
    # and append `    ...\n`
    pattern = re.compile(
        r'(\s*def [^\n]+\n(?:[ \t]+[^\n]+\n)*?\s*""")([^\n]*?)(""")(\s*\n\n)', re.MULTILINE
    )

    def replacer(match):
        indent = match.group(1).split("def")[0]
        # if there's already `...` or `pass` or `return` below the docstring, we shouldn't insert
        # wait, the regex specifically captures the end of the docstring followed by double newline `\n\n`
        # meaning there was no body
        return match.group(1) + match.group(2) + match.group(3) + f"\n{indent}    ...\n\n"

    new_content = pattern.sub(replacer, content)

    # also handle the case where it's single-line docstring
    pattern2 = re.compile(
        r'(\s*def [^\n]+\n(?:[ \t]+[^\n]+\n)*?\s*""")([^\n]*?)(""")(\s*\n(?:\s*@|\s*def |$))',
        re.MULTILINE,
    )

    def replacer2(match):
        indent = match.group(1).split("def")[0]
        # Only replace if the body is empty (immediately followed by a decorator, a def, or EOF)
        return (
            match.group(1) + match.group(2) + match.group(3) + f"\n{indent}    ..." + match.group(4)
        )

    new_content2 = pattern2.sub(replacer2, new_content)

    if new_content2 != content:
        with open(path, "w") as f:
            f.write(new_content2)
            print(f"Fixed {path}")


import sys

for arg in sys.argv[1:]:
    fix_file(arg)
