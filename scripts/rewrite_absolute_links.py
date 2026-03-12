#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ABSOLUTE_LINK_PATTERN = re.compile(r"/Users/val/[^\s)\]>\"']+")


@dataclass(frozen=True)
class Replacement:
    source_file: Path
    original: str
    rewritten: str


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        message = stderr or stdout or f"git {' '.join(args)} failed"
        raise RuntimeError(message)
    return result


def split_suffix(absolute_target: str) -> tuple[str, str]:
    suffix_start = len(absolute_target)
    for marker in ("?", "#"):
        index = absolute_target.find(marker)
        if index != -1:
            suffix_start = min(suffix_start, index)
    return absolute_target[:suffix_start], absolute_target[suffix_start:]


def relativize_target(source_file: Path, absolute_target: str) -> str:
    target_path, suffix = split_suffix(absolute_target)
    relative_path = os.path.relpath(target_path, start=source_file.parent)
    return Path(relative_path).as_posix() + suffix


def rewrite_text(source_file: Path, text: str) -> tuple[str, list[Replacement]]:
    replacements: list[Replacement] = []

    def replace_match(match: re.Match[str]) -> str:
        original = match.group(0)
        rewritten = relativize_target(source_file, original)
        replacements.append(
            Replacement(
                source_file=source_file,
                original=original,
                rewritten=rewritten,
            )
        )
        return rewritten

    updated_text = ABSOLUTE_LINK_PATTERN.sub(replace_match, text)
    return updated_text, replacements


def is_probably_text_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return b"\0" not in handle.read(4096)
    except OSError:
        return False


def iter_tracked_files(repo_root: Path) -> Iterable[Path]:
    result = run_git(repo_root, "ls-files", "-z")
    for raw_path in result.stdout.split("\0"):
        if raw_path:
            yield repo_root / raw_path


def scan_or_rewrite_worktree(
    repo_root: Path,
    *,
    apply: bool,
    quiet: bool = False,
) -> tuple[int, int]:
    changed_files = 0
    total_replacements = 0

    for path in iter_tracked_files(repo_root):
        if not is_probably_text_file(path):
            continue

        try:
            original_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        rewritten_text, replacements = rewrite_text(path, original_text)
        if not replacements:
            continue

        changed_files += 1
        total_replacements += len(replacements)

        if apply:
            path.write_text(rewritten_text, encoding="utf-8")

        if quiet:
            continue

        relative_path = path.relative_to(repo_root).as_posix()
        action = "rewrote" if apply else "would rewrite"
        print(f"{action}: {relative_path}")
        for replacement in replacements:
            print(f"  {replacement.original} -> {replacement.rewritten}")

    return changed_files, total_replacements


def scan_or_rewrite_directory(
    directory_root: Path,
    *,
    canonical_root: Path,
    apply: bool,
    quiet: bool = False,
) -> tuple[int, int]:
    changed_files = 0
    total_replacements = 0
    canonical_root_str = canonical_root.as_posix().rstrip("/")

    shutil.rmtree(directory_root / ".venv", ignore_errors=True)

    for path in directory_root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if not is_probably_text_file(path):
            continue

        try:
            original_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        replacements: list[Replacement] = []

        def replace_match(match: re.Match[str]) -> str:
            original = match.group(0)
            target_path, suffix = split_suffix(original)
            prefix = canonical_root_str + "/"
            if not target_path.startswith(prefix):
                return original

            repo_relative = target_path[len(prefix) :]
            target_in_tree = directory_root / repo_relative
            rewritten = Path(os.path.relpath(target_in_tree, start=path.parent)).as_posix() + suffix
            replacements.append(
                Replacement(
                    source_file=path,
                    original=original,
                    rewritten=rewritten,
                )
            )
            return rewritten

        rewritten_text = ABSOLUTE_LINK_PATTERN.sub(replace_match, original_text)
        if not replacements:
            continue

        changed_files += 1
        total_replacements += len(replacements)

        if apply:
            path.write_text(rewritten_text, encoding="utf-8")

        if quiet:
            continue

        relative_path = path.relative_to(directory_root).as_posix()
        action = "rewrote" if apply else "would rewrite"
        print(f"{action}: {relative_path}")
        for replacement in replacements:
            print(f"  {replacement.original} -> {replacement.rewritten}")

    return changed_files, total_replacements


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def scan_history(repo_root: Path) -> list[str]:
    revisions = [line for line in run_git(repo_root, "rev-list", "--all").stdout.splitlines() if line]
    matches: list[str] = []

    for batch in chunked(revisions, 128):
        result = run_git(repo_root, "grep", "-n", "/Users/val/", *batch, check=False)
        if result.returncode not in (0, 1):
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            raise RuntimeError(stderr or stdout or "git grep failed while scanning history")
        matches.extend(line for line in result.stdout.splitlines() if line)

    return matches


def ensure_clean_worktree(repo_root: Path) -> None:
    status = run_git(repo_root, "status", "--porcelain").stdout.strip()
    if status:
        raise RuntimeError("rewrite-history requires a clean worktree")


def print_current_summary(changed_files: int, replacements: int, *, apply: bool) -> None:
    action = "rewritten" if apply else "matched"
    print(f"current checkout: {changed_files} files {action}, {replacements} links")


def command_audit(repo_root: Path) -> int:
    changed_files, replacements = scan_or_rewrite_worktree(repo_root, apply=False)
    print_current_summary(changed_files, replacements, apply=False)

    history_matches = scan_history(repo_root)
    if history_matches:
        print("history matches:")
        for line in history_matches:
            print(line)
    else:
        print("history matches: none")

    return 0


def command_rewrite_current(repo_root: Path, *, apply: bool, quiet: bool) -> int:
    changed_files, replacements = scan_or_rewrite_worktree(repo_root, apply=apply, quiet=quiet)
    if not quiet:
        print_current_summary(changed_files, replacements, apply=apply)
    return 0


def command_rewrite_history(repo_root: Path, *, confirmed: bool) -> int:
    if not confirmed:
        raise RuntimeError("rewrite-history requires --yes because it rewrites all reachable commits")

    ensure_clean_worktree(repo_root)

    temp_script_path: Path | None = None
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".py",
        prefix="rewrite_absolute_links_",
        delete=False,
    ) as temp_script:
        script_path = Path(__file__).resolve()
        temp_script.write(script_path.read_text(encoding="utf-8"))
        temp_script_path = Path(temp_script.name)

    tree_filter_command = [
        sys.executable,
        str(temp_script_path),
        "rewrite-directory",
        "--apply",
        "--quiet",
        "--canonical-root",
        str(repo_root),
    ]

    env = os.environ.copy()
    env["FILTER_BRANCH_SQUELCH_WARNING"] = "1"
    try:
        result = subprocess.run(
            [
                "git",
                "filter-branch",
                "--force",
                "--tag-name-filter",
                "cat",
                "--tree-filter",
                shlex.join(tree_filter_command),
                "--",
                "--all",
            ],
            cwd=repo_root,
            env=env,
            check=False,
        )
    finally:
        if temp_script_path is not None:
            temp_script_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError("git filter-branch failed")

    history_matches = []
    revisions = [line for line in run_git(repo_root, "rev-list", "HEAD").stdout.splitlines() if line]
    for batch in chunked(revisions, 128):
        result = run_git(repo_root, "grep", "-n", "/Users/val/", *batch, check=False)
        if result.returncode not in (0, 1):
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            raise RuntimeError(stderr or stdout or "git grep failed while verifying rewritten history")
        history_matches.extend(
            line
            for line in result.stdout.splitlines()
            if line and ":.venv/" not in line and ":.venv\\" not in line
        )
    if history_matches:
        print("history rewrite completed, but current branch matches remain:")
        for line in history_matches:
            print(line)
        return 1

    print("history rewrite completed with no remaining /Users/val/ links")
    print("refs/original was left intact; verify the result before deleting backup refs or force-pushing")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rewrite /Users/val/... links to file-relative paths in the current checkout or full git history.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current working directory.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("audit", help="List current-checkout matches and all reachable history matches.")

    rewrite_current = subparsers.add_parser(
        "rewrite-current",
        help="Rewrite tracked files in the current checkout. Without --apply this is a dry run.",
    )
    rewrite_current.add_argument(
        "--apply",
        action="store_true",
        help="Write changes back to disk instead of printing a dry-run report.",
    )
    rewrite_current.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file output and print only the final summary.",
    )

    rewrite_directory = subparsers.add_parser(
        "rewrite-directory",
        help="Rewrite files under the current working directory using a canonical repo root prefix.",
    )
    rewrite_directory.add_argument(
        "--canonical-root",
        type=Path,
        required=True,
        help="Absolute repository root prefix to strip from /Users/val/... links.",
    )
    rewrite_directory.add_argument(
        "--apply",
        action="store_true",
        help="Write changes back to disk instead of printing a dry-run report.",
    )
    rewrite_directory.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file output and print only the final summary.",
    )

    rewrite_history = subparsers.add_parser(
        "rewrite-history",
        help="Rewrite all reachable commits with git filter-branch.",
    )
    rewrite_history.add_argument(
        "--yes",
        action="store_true",
        help="Confirm the destructive history rewrite.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    git_root = Path(run_git(repo_root, "rev-parse", "--show-toplevel").stdout.strip()).resolve()

    command = args.command or "audit"
    if command == "audit":
        return command_audit(git_root)
    if command == "rewrite-current":
        return command_rewrite_current(git_root, apply=args.apply, quiet=args.quiet)
    if command == "rewrite-directory":
        changed_files, replacements = scan_or_rewrite_directory(
            Path.cwd(),
            canonical_root=args.canonical_root.resolve(),
            apply=args.apply,
            quiet=args.quiet,
        )
        if not args.quiet:
            print_current_summary(changed_files, replacements, apply=args.apply)
        return 0
    if command == "rewrite-history":
        return command_rewrite_history(git_root, confirmed=args.yes)

    parser.error(f"unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
