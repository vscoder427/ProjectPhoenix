#!/usr/bin/env python3
"""Fail if the PR branch or commit messages ignore the branching/commit standards."""

from __future__ import annotations

import os
import re
import subprocess
import sys

ALLOWED_BRANCH_PREFIXES = ("feature/", "fix/", "docs/", "refactor/")
CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|test|chore)"
    r"(?:\([A-Za-z0-9_./-]+\))?"
    r"(?:!)?: .+"
)


def check_branch(branch: str | None) -> bool:
    if not branch:
        print("Missing HEAD branch name; cannot validate branch prefix.")
        return False
    for prefix in ALLOWED_BRANCH_PREFIXES:
        if branch.startswith(prefix):
            print(f"Branch '{branch}' follows the prefix '{prefix}'.")
            return True
    print(
        "Branch naming violation: "
        f"'{branch}' must start with one of {ALLOWED_BRANCH_PREFIXES}."
    )
    return False


def fetch_base(base_ref: str) -> None:
    subprocess.run(
        ["git", "fetch", "origin", base_ref],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def collect_commit_messages(base_ref: str, head_sha: str) -> list[str]:
    range_ref = f"origin/{base_ref}..{head_sha}"
    output = subprocess.check_output(
        ["git", "log", "--format=%s", range_ref], stderr=subprocess.DEVNULL
    ).decode("utf-8")
    return [line.strip() for line in output.splitlines() if line.strip()]


def validate_commits(messages: list[str]) -> bool:
    invalid = []
    for msg in messages:
        if not CONVENTIONAL_COMMIT_PATTERN.match(msg):
            invalid.append(msg)
    if invalid:
        print("Some commits do not fit the Conventional Commit pattern:")
        for msg in invalid:
            print(f"  * {msg}")
        return False
    if messages:
        print("All commit messages follow the Conventional Commits pattern.")
    else:
        print("No commits to validate.")
    return True


def main() -> int:
    base_ref = os.environ.get("BASE_REF", "main")
    head_ref = os.environ.get("HEAD_REF")
    head_sha = os.environ.get("HEAD_SHA")

    if not check_branch(head_ref):
        return 1

    if not head_sha:
        print("Missing HEAD SHA; cannot validate commits.")
        return 1

    fetch_base(base_ref)
    messages = collect_commit_messages(base_ref, head_sha)
    if not validate_commits(messages):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
