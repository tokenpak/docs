#!/usr/bin/env python3
"""Self-tests for the docs pull-request contract checker."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


CHECKER_PATH = Path(__file__).with_name("check-docs-pr.py")
SPEC = importlib.util.spec_from_file_location("check_docs_pr", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {CHECKER_PATH}")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def valid_spec() -> dict:
    basic_properties = {
        "status": {"type": "string"},
        "pid": {"type": "integer", "minimum": 1},
    }
    deep_properties = {
        **copy.deepcopy(basic_properties),
        "providers": {"type": "array"},
        "memory": {"type": "object"},
        "disk": {"type": "object"},
    }
    return {
        "paths": {
            "/health": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "example": {"status": "ok", "pid": 42}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "HealthResponseBasic": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(basic_properties),
                    "properties": basic_properties,
                },
                "HealthResponseDeep": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(deep_properties),
                    "properties": deep_properties,
                },
            }
        },
    }


def complete_body() -> str:
    return "\n\n".join(f"## {heading}\n\nContent." for heading in CHECKER.REQUIRED_HEADINGS)


def git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def commit(root: Path, message: str, *, public: bool = True) -> str:
    env = os.environ.copy()
    name = "TokenPak" if public else "Private Author"
    email = "hello@tokenpak.ai" if public else "private@example.invalid"
    env.update(
        {
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
        }
    )
    git(root, "add", ".")
    git(root, "commit", "-m", message, env=env)
    return git(root, "rev-parse", "HEAD")


class CheckerTests(unittest.TestCase):
    def write_spec(self, root: Path, value: dict) -> Path:
        path = root / "openapi.yaml"
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
        return path

    def test_openapi_pid_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            CHECKER.check_openapi(self.write_spec(root, valid_spec()))

            cases = []
            missing = valid_spec()
            del missing["components"]["schemas"]["HealthResponseBasic"]["properties"]["pid"]
            cases.append(missing)
            boolean = valid_spec()
            boolean["paths"]["/health"]["get"]["responses"]["200"]["content"][
                "application/json"
            ]["example"]["pid"] = True
            cases.append(boolean)
            zero = valid_spec()
            zero["components"]["schemas"]["HealthResponseDeep"]["properties"]["pid"][
                "minimum"
            ] = 0
            cases.append(zero)
            for value in cases:
                with self.subTest(value=value):
                    with self.assertRaises(CHECKER.ContractError):
                        CHECKER.check_openapi(self.write_spec(root, value))

    def test_headings_and_titles(self) -> None:
        CHECKER.check_headings(complete_body(), "fixture")
        with self.assertRaises(CHECKER.ContractError):
            CHECKER.check_headings("## Summary\n", "fixture")
        CHECKER.check_conventional_title("docs: align health response contract")
        with self.assertRaises(CHECKER.ContractError):
            CHECKER.check_conventional_title("Update docs")

    def test_pr_metadata_shapes(self) -> None:
        event = {
            "pull_request": {
                "title": "docs: align health response contract",
                "body": complete_body(),
                "base": {"sha": "base", "ref": "main"},
                "head": {"sha": "head", "ref": "docs/health-contract"},
            }
        }
        local = {
            "title": event["pull_request"]["title"],
            "body": event["pull_request"]["body"],
            "baseRefOid": "base",
            "headRefOid": "head",
            "baseRefName": "main",
            "headRefName": "docs/health-contract",
        }
        self.assertEqual(CHECKER.normalize_pr_metadata(event), CHECKER.normalize_pr_metadata(local))
        CHECKER.check_pr_presentation(CHECKER.normalize_pr_metadata(event), "base", "head")

    def test_public_scan_and_policy_register_exclusion(self) -> None:
        bad_path = "/home/" + "s" + "ue/" + "private"
        with self.assertRaises(CHECKER.ContractError):
            CHECKER.check_changed_file("docs/example.md", bad_path)
        CHECKER.check_changed_file(CHECKER.POLICY_REGISTER, bad_path)

        bad_body = complete_body() + "\n\n" + "gpt-" + "5 validation"
        metadata = {
            "title": "docs: align health response contract",
            "body": bad_body,
            "base_sha": "base",
            "head_sha": "head",
            "base_ref": "main",
            "head_ref": "docs/health-contract",
        }
        with self.assertRaises(CHECKER.ContractError):
            CHECKER.check_pr_presentation(metadata, "base", "head")

    def test_commit_identity_and_changed_file_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init", "-q")
            (root / "README.md").write_text("TokenPak docs\n", encoding="utf-8")
            base = commit(root, "docs: establish baseline")

            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("Public documentation.\n", encoding="utf-8")
            head = commit(root, "docs: add public guide")
            CHECKER.check_commits(root, base, head)
            CHECKER.check_public_delta(root, base, head)

            (docs / "guide.md").write_text(
                "Private path: " + "/home/" + "s" + "ue/" + "workspace\n",
                encoding="utf-8",
            )
            bad_head = commit(root, "docs: expose private path")
            with self.assertRaises(CHECKER.ContractError):
                CHECKER.check_public_delta(root, head, bad_head)

            (docs / "guide.md").write_text("Public again.\n", encoding="utf-8")
            wrong_head = commit(root, "docs: use wrong identity", public=False)
            with self.assertRaises(CHECKER.ContractError):
                CHECKER.check_commits(root, bad_head, wrong_head)

    def test_metadata_loader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pr.json"
            value = {
                "title": "docs: align health response contract",
                "body": complete_body(),
                "baseRefOid": "base",
                "headRefOid": "head",
                "baseRefName": "main",
                "headRefName": "docs/health-contract",
            }
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(CHECKER.load_pr_metadata(path)["head_sha"], "head")

    def test_workflow_contract(self) -> None:
        root = Path(__file__).resolve().parents[2]
        workflow_path = root / ".github/workflows/docs-checks.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.load(workflow_text, Loader=yaml.BaseLoader)
        pull_request = workflow["on"]["pull_request"]
        self.assertEqual(pull_request["branches"], ["main"])
        self.assertEqual(
            pull_request["types"],
            ["opened", "synchronize", "reopened", "ready_for_review", "edited"],
        )
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["validate"]
        self.assertEqual(job["name"], "Docs validation")
        self.assertEqual(job["timeout-minutes"], "10")
        uses = [step["uses"] for step in job["steps"] if "uses" in step]
        self.assertEqual(uses, ["actions/checkout@v4", "actions/setup-python@v5"])
        self.assertNotIn("secrets.", workflow_text)

        def routes(text: str) -> set[str]:
            match = re.search(r"for p in (.*?); do", text, flags=re.DOTALL)
            self.assertIsNotNone(match)
            return set(match.group(1).replace("\\\n", " ").split())

        deploy_text = (root / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
        self.assertEqual(routes(workflow_text), routes(deploy_text))


if __name__ == "__main__":
    unittest.main(verbosity=2)
