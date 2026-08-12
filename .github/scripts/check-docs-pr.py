#!/usr/bin/env python3
"""Validate the docs contract and public pull-request presentation."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY_REGISTER = ".github/scripts/check-docs-pr.py"
PUBLIC_IDENTITY = ("TokenPak", "hello@tokenpak.ai")
REQUIRED_HEADINGS = (
    "Summary",
    "Scope",
    "Validation",
    "Risks",
    "Release impact",
    "Documentation impact",
    "Checklist",
)
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json", ".toml", ".sh", ".js", ".ts", ".tsx"}
CONVENTIONAL_TITLE = re.compile(
    r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(?:\([a-z0-9._/-]+\))?!?: \S.+$"
)
INTERNAL_IDENTITY = re.compile(
    r"(?i)(?<![a-z0-9])(?:sue|suki|cali|trix|aya|dee|reipo)(?![a-z0-9])"
)
FILE_PATTERNS = (
    ("private home path", re.compile(r"/home/sue/")),
    ("private transcript path", re.compile(r"\.claude/projects")),
    ("private vault path", re.compile(r"~/vault/[0-9]{2}_")),
    ("internal identity", INTERNAL_IDENTITY),
    (
        "internal task identifier",
        re.compile(r"(?i)\b(?:TSR|TPS|CCI|MTC|OAS|TIP7|TRIX-MTC|WS)-[A-Z0-9]"),
    ),
    ("internal standard citation", re.compile(r"(?:\bStd [0-9]{2}\b|§[0-9])")),
    (
        "internal workflow narrative",
        re.compile(
            r"(?i)\b(?:auto-commit|cycle complete|governor cycle|"
            r"validation history|dispatcher receipt|vault pin)\b"
        ),
    ),
)
METADATA_PATTERNS = FILE_PATTERNS + (
    (
        "validation-model identifier",
        re.compile(
            r"(?i)(?:\bgpt-[0-9]|\bclaude-(?:sonnet|opus|haiku|[0-9])|"
            r"\bterra\b|\bsol(?:/xhigh)?\b|\bxhigh\b)"
        ),
    ),
    (
        "internal review narrative",
        re.compile(
            r"(?i)\b(?:exact-head|governor ratification|landing authorization|"
            r"adverse evidence|binding block|runner invocation|validation lane|"
            r"model proof|receipt hash)\b"
        ),
    ),
)


class ContractError(RuntimeError):
    """Raised when one or more public contract checks fail."""


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ContractError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def check_openapi(path: Path) -> None:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    try:
        schemas = spec["components"]["schemas"]
        basic = schemas["HealthResponseBasic"]
        deep = schemas["HealthResponseDeep"]
        example = spec["paths"]["/health"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["example"]
    except (KeyError, TypeError) as exc:
        raise ContractError(f"OpenAPI health contract is incomplete: {exc}") from exc

    for name, schema in (("HealthResponseBasic", basic), ("HealthResponseDeep", deep)):
        require(schema.get("additionalProperties") is False, f"{name} must remain closed")
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        require("pid" in required, f"{name} must require pid")
        require(
            properties.get("pid") == {"type": "integer", "minimum": 1},
            f"{name}.pid must be an integer with minimum 1",
        )
        require(
            set(required) == set(properties),
            f"{name} required fields and properties must match",
        )

    pid = example.get("pid")
    require(
        isinstance(pid, int) and not isinstance(pid, bool) and pid >= 1,
        "/health example pid must be a positive integer",
    )
    require(
        set(example) == set(basic["required"]),
        "/health example must contain exactly the basic response fields",
    )
    deep_only = {"providers", "memory", "disk"}
    require(
        set(deep["required"]) == set(basic["required"]) | deep_only,
        "deep health fields must extend the basic contract only",
    )
    require(
        all(deep["properties"][key] == basic["properties"][key] for key in basic["properties"]),
        "shared basic/deep health property definitions must match",
    )


def markdown_headings(text: str) -> set[str]:
    return {
        match.group(1).strip().casefold()
        for match in re.finditer(r"^##[ \t]+(.+?)[ \t]*$", text, flags=re.MULTILINE)
    }


def check_headings(text: str, surface: str) -> None:
    found = markdown_headings(text)
    missing = [heading for heading in REQUIRED_HEADINGS if heading.casefold() not in found]
    require(not missing, f"{surface} missing headings: {', '.join(missing)}")


def check_conventional_title(title: str, surface: str = "PR title") -> None:
    require(bool(CONVENTIONAL_TITLE.fullmatch(title.strip())), f"{surface} is not conventional")


def findings(text: str, patterns: Iterable[tuple[str, re.Pattern[str]]]) -> list[str]:
    return [label for label, pattern in patterns if pattern.search(text)]


def check_metadata_text(text: str, surface: str) -> None:
    hits = findings(text, METADATA_PATTERNS)
    require(not hits, f"{surface} contains forbidden public metadata: {', '.join(hits)}")


def check_changed_file(path: str, text: str) -> None:
    if path == POLICY_REGISTER:
        return
    hits = findings(text, FILE_PATTERNS)
    require(not hits, f"{path} contains forbidden public content: {', '.join(hits)}")


def normalize_pr_metadata(data: dict[str, Any]) -> dict[str, str]:
    if isinstance(data.get("pull_request"), dict):
        pr = data["pull_request"]
        return {
            "title": pr.get("title") or "",
            "body": pr.get("body") or "",
            "base_sha": (pr.get("base") or {}).get("sha") or "",
            "head_sha": (pr.get("head") or {}).get("sha") or "",
            "base_ref": (pr.get("base") or {}).get("ref") or "",
            "head_ref": (pr.get("head") or {}).get("ref") or "",
        }
    return {
        "title": data.get("title") or "",
        "body": data.get("body") or "",
        "base_sha": data.get("baseRefOid") or "",
        "head_sha": data.get("headRefOid") or "",
        "base_ref": data.get("baseRefName") or "",
        "head_ref": data.get("headRefName") or "",
    }


def load_pr_metadata(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "PR metadata must be a JSON object")
    return normalize_pr_metadata(data)


def check_pr_presentation(metadata: dict[str, str], base: str, head: str) -> None:
    if metadata["base_sha"]:
        require(metadata["base_sha"] == base, "PR metadata base SHA does not match --base")
    if metadata["head_sha"]:
        require(metadata["head_sha"] == head, "PR metadata head SHA does not match --head")
    check_conventional_title(metadata["title"])
    check_headings(metadata["body"], "PR body")
    check_metadata_text(metadata["title"], "PR title")
    check_metadata_text(metadata["body"], "PR body")
    for ref_name in ("base_ref", "head_ref"):
        value = metadata[ref_name]
        if value:
            require(
                not INTERNAL_IDENTITY.search(value),
                f"{ref_name.replace('_', ' ')} contains an internal identity",
            )


def commit_shas(root: Path, base: str, head: str) -> list[str]:
    values = run_git(root, "rev-list", "--reverse", f"{base}..{head}").splitlines()
    require(bool(values), f"no commits found in {base}..{head}")
    return values


def check_commits(root: Path, base: str, head: str) -> None:
    for commit in commit_shas(root, base, head):
        identity = run_git(
            root,
            "show",
            "-s",
            "--format=%an%x00%ae%x00%cn%x00%ce",
            commit,
        ).rstrip("\n").split("\x00")
        require(len(identity) == 4, f"cannot parse identity for {commit}")
        author = tuple(identity[:2])
        committer = tuple(identity[2:])
        require(author == PUBLIC_IDENTITY, f"{commit} author is not TokenPak public identity")
        require(
            committer == PUBLIC_IDENTITY,
            f"{commit} committer is not TokenPak public identity",
        )
        message = run_git(root, "show", "-s", "--format=%B", commit).strip()
        subject = message.splitlines()[0] if message else ""
        check_conventional_title(subject, f"{commit} subject")
        check_metadata_text(message, f"{commit} message")


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    output = run_git(root, "diff", "--name-only", "--diff-filter=AM", "-z", base, head)
    return [path for path in output.split("\x00") if path]


def check_public_delta(root: Path, base: str, head: str) -> None:
    for relative in changed_paths(root, base, head):
        path = root / relative
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        check_changed_file(relative, path.read_text(encoding="utf-8", errors="replace"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--event", type=Path)
    source.add_argument("--pr-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = ROOT.resolve()
    resolved_head = run_git(root, "rev-parse", "HEAD").strip()
    require(resolved_head == args.head, f"checkout HEAD {resolved_head} != requested {args.head}")
    require(not run_git(root, "status", "--porcelain"), "candidate checkout is dirty")
    metadata = load_pr_metadata(args.event or args.pr_json)

    check_openapi(root / "docs/openapi.yaml")
    check_headings(
        (root / ".github/PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8"),
        "PR template",
    )
    check_pr_presentation(metadata, args.base, args.head)
    check_commits(root, args.base, args.head)
    check_public_delta(root, args.base, args.head)
    print(f"DOCS_PR_CONTRACT_OK base={args.base} head={args.head}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"DOCS_PR_CONTRACT_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
