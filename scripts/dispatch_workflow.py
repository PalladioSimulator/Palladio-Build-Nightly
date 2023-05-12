#!/bin/env python3

# Executes a Github Workflow on the default branch and awaits its termination.
# The workflow must contain a workflow_dispatch trigger.
# This script exits with exit code 1 if the workflow does not complete with "success"

import json
import os
import sys
import time
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen

REFRESH_TIMEOUT_SEC = 5
# Time to wait until the dispached workflow shows up
WORKFLOW_RUN_TIMEOUT_SEC = 60


class Github:
    def __init__(self, token: str):
        self.token = token

    def _add_github_api_headers(self, req: Request):
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Authorization", f"token {self.token}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")

    def get_default_branch(self, owner: str, repository: str) -> str:
        req = Request(f"https://api.github.com/repos/{owner}/{repository}")
        self._add_github_api_headers(req)

        with urlopen(req) as f:
            resp = json.loads(f.read().decode("utf-8"))
            return resp["default_branch"]

    def dispatch_workflow(
        self, owner: str, repository: str, ref: str, workflow_id_or_name: str
    ):
        data = {"ref": ref}
        req = Request(
            f"https://api.github.com/repos/{owner}/{repository}/actions/workflows/{workflow_id_or_name}/dispatches",
            data=json.dumps(data).encode(),
            method="POST",
        )
        self._add_github_api_headers(req)
        with urlopen(req) as f:
            if f.status != 204:
                print("Failed to create the dispatch event")
                print(f.reason)
                raise RuntimeError()

    def get_lastest_workflow_run_id(
        self, owner: str, repository: str, workflow: str
    ) -> Optional[int]:
        req = Request(f"https://api.github.com/repos/{owner}/{repository}/actions/runs")
        self._add_github_api_headers(req)

        with urlopen(req) as f:
            resp = json.loads(f.read().decode("utf-8"))
            if resp["total_count"] == 0:
                return None
            for run in resp["workflow_runs"]:
                if workflow in run["path"]:
                    return run["id"]
            return None

    def get_workflow_run(self, owner: str, repository: str, run_id: int):
        req = Request(
            f"https://api.github.com/repos/{owner}/{repository}/actions/runs/{run_id}"
        )
        self._add_github_api_headers(req)

        with urlopen(req) as f:
            return json.loads(f.read().decode("utf-8"))


def main():
    if len(sys.argv) != 4:
        print(
            """Usage dispatch_workflow.py <owner> <repo> <workflow_name.yml>
Provide a token as GITHUB_OAUTH  environment variable
"""
        )
        raise ValueError()

    _, owner, repo_name, workflow = sys.argv
    token = os.environ["GITHUB_OAUTH"]
    github = Github(token)

    last_run_id = github.get_lastest_workflow_run_id(owner, repo_name, workflow)

    ref = github.get_default_branch(owner, repo_name)
    print(f"Detected default branch {ref}")
    github.dispatch_workflow(owner, repo_name, ref, workflow)
    print(f"Dispatched workflow {workflow}")

    start = datetime.now()
    while True:
        run_id = github.get_lastest_workflow_run_id(owner, repo_name, workflow)
        if run_id and run_id != last_run_id:
            break
        if (datetime.now() - start).total_seconds() > WORKFLOW_RUN_TIMEOUT_SEC:
            raise RuntimeError(
                f"New workflow did not show up after {WORKFLOW_RUN_TIMEOUT_SEC} s."
            )
        time.sleep(REFRESH_TIMEOUT_SEC)

    print(f"Waiting for run {run_id} to complete")
    while True:
        run = github.get_workflow_run(owner, repo_name, run_id)
        if run["status"] == "completed":
            break
        time.sleep(REFRESH_TIMEOUT_SEC)

    print(f"Run completed with conclusion {run['conclusion']}")
    if run["conclusion"] != "success":
        exit(1)


if __name__ == "__main__":
    main()
