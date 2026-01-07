#!/usr/bin/env python3
"""Validate service documentation exists for modified services."""

import os
import pathlib
import subprocess
import sys


def git_diff_names(base_ref: str) -> set[str]:
    subprocess.run(["git", "fetch", "origin", base_ref], check=True, stdout=subprocess.DEVNULL)
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]
    ).decode("utf-8")
    return {line.strip() for line in output.splitlines() if line.strip()}


def service_names_from_paths(paths: set[str]) -> set[str]:
    services = set()
    for path in paths:
        if path.startswith("services/"):
            parts = path.split("/")
            if len(parts) >= 2:
                services.add(parts[1])
        if path.startswith("docs/services/"):
            parts = path.split("/")
            if len(parts) >= 3:
                services.add(parts[2])
    return services


def check_docs_for_service(service: str) -> list[str]:
    missing = []
    base = pathlib.Path("docs/services") / service
    if not base.exists():
        missing.append(f"{base} (directory missing)")
        return missing
    for name in ("spec.md", "runbook.md", "README.md"):
        target = base / name
        if not target.exists():
            missing.append(str(target))
    return missing


def main() -> int:
    base_ref = os.environ.get("BASE_BRANCH", "main")
    paths = git_diff_names(base_ref)
    services = service_names_from_paths(paths)
    if not services:
        print("No services modified; skipping doc validation.")
        return 0

    missing = {}
    for svc in sorted(services):
        files = check_docs_for_service(svc)
        if files:
            missing[svc] = files

    if missing:
        print("Documentation gaps detected for modified services:")
        for svc, files in missing.items():
            print(f"  - {svc}:")
            for file in files:
                print(f"      * {file}")
        return 1

    print("All modified services include spec/runbook/README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
