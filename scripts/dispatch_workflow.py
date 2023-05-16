#!/bin/env python3

"""Executes a Github Workflow and awaits its termination.

The workflow must contain a workflow_dispatch trigger.
This script exits with exit code 1 if the workflow does not complete with "success"
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Optional
from urllib.request import Request, urlopen

REFRESH_TIMEOUT_SEC = 5
# Time to wait until the dispached workflow shows up
WORKFLOW_RUN_TIMEOUT_SEC = 60
GITHUB_API_URL = "https://api.github.com"
GITHUB_URL = "https://github.com"


logging.basicConfig(level=logging.DEBUG)


class Github:
    def __init__(self, token: str):
        self.token = token

    def _add_github_api_headers(self, req: Request):
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Authorization", f"token {self.token}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")

    def _get_object(self, api_url: str):
        req = Request(f"{GITHUB_API_URL}{api_url}")
        self._add_github_api_headers(req)
        with urlopen(req) as f:
            return json.loads(f.read().decode("utf-8"))

    def get_default_branch(self, owner: str, repository: str) -> str:
        obj = self._get_object(f"/repos/{owner}/{repository}")
        return obj["default_branch"]

    def dispatch_workflow(
        self, owner: str, repository: str, ref: str, workflow_id_or_name: str
    ):
        data = {"ref": ref}
        req = Request(
            f"{GITHUB_API_URL}/repos/{owner}/{repository}/actions/workflows/{workflow_id_or_name}/dispatches",
            data=json.dumps(data).encode(),
            method="POST",
        )
        self._add_github_api_headers(req)
        with urlopen(req) as f:
            if f.status != 204:
                logging.error(f"Failed to create the dispatch event: {f.reason}")
                raise RuntimeError()

    def dispatch_workflow_and_get_id(
        self, owner: str, repository: str, ref: str, workflow_id_or_name: str
    ) -> int:
        """
        Dispatches a workflow, then waits until the workflow shows up in the API.
        """
        last_run = self.get_lastest_workflow_run(owner, repository, workflow_id_or_name)
        last_run_id = last_run["id"] if last_run else None
        self.dispatch_workflow(owner, repository, ref, workflow_id_or_name)
        start = datetime.now()
        while True:
            logging.debug("Checking for new workflow run")
            run = self.get_lastest_workflow_run(owner, repository, workflow_id_or_name)
            if run and run["id"] != last_run_id:
                return run["id"]
            if (datetime.now() - start).total_seconds() > WORKFLOW_RUN_TIMEOUT_SEC:
                raise RuntimeError(
                    f"New workflow did not show up after {WORKFLOW_RUN_TIMEOUT_SEC} s."
                )
            time.sleep(REFRESH_TIMEOUT_SEC)

    def get_lastest_workflow_run(
        self,
        owner: str,
        repository: str,
        filter_workflow: Optional[str] = None,
        filter_conclusion: Optional[str] = None,
    ) -> Optional[Any]:
        # Returns the last 30 workflow runs (page 1)
        resp = self._get_object(f"/repos/{owner}/{repository}/actions/runs")
        if resp["total_count"] == 0:
            return None
        for run in resp["workflow_runs"]:
            if filter_workflow and filter_workflow not in run["path"]:
                continue
            if filter_conclusion and filter_conclusion != run["conclusion"]:
                continue
            return run
        return None

    def get_workflow_run(self, owner: str, repository: str, run_id: int):
        return self._get_object(f"/repos/{owner}/{repository}/actions/runs/{run_id}")

    def get_branch(self, owner: str, repository: str, branch: str):
        return self._get_object(f"/repos/{owner}/{repository}/branches/{branch}")

    def wait_for_workflow_run_completion(
        self, owner: str, repository: str, run_id: int
    ) -> Any:
        """
        Waits for the workflow run to complete and returns the run afterwards.
        """
        while True:
            logging.debug("Checking workflow status...")
            run = self.get_workflow_run(owner, repository, run_id)
            logging.debug(f"...{run['status']}")
            if run["status"] == "completed":
                return run
            time.sleep(REFRESH_TIMEOUT_SEC)


def needs_workflow_execution(
    github: Github, owner: str, repository: str, ref: str, workflow: str
):
    # Check if a build is necessary.
    # dependencies = json.loads(os.environ["DEPENDENCIES"])
    last_run = github.get_lastest_workflow_run(owner, repository, workflow)
    if not last_run:
        logging.debug("Needs build. Reason: Workflow never run")
        return True

    last_run_date = datetime.fromisoformat(last_run["created_at"])
    logging.debug(f"Last workflow run at: {last_run_date}")
    branch = github.get_branch(owner, repository, ref)
    last_commit_date = datetime.fromisoformat(
        branch["commit"]["commit"]["committer"]["date"]
    )
    logging.debug(f"Last commit: {last_commit_date}")
    if last_run_date < last_commit_date:
        logging.debug("Needs build. Reason: Newer commit found")
        return True

    deps_json = os.environ.get("DEPENDENCIES", "[]")
    for dep in json.loads(deps_json):
        dep_owner, dep_repo = dep.split("/")
        last_dep_run = github.get_lastest_workflow_run(
            dep_owner, dep_repo, filter_conclusion="success"
        )
        if not last_dep_run:
            logging.debug(
                f"Dependency {dep} never had a successful workflow run. Skipping."
            )
            continue
        last_dep_run_date = datetime.fromisoformat(last_dep_run["created_at"])
        logging.debug(
            f"Dependency {dep} had a successful workflow run of {last_dep_run['path']} at {last_dep_run_date}"
        )
        if last_run_date < last_dep_run_date:
            logging.debug(
                f"Needs build. Reason: Newer dependency run found ({last_dep_run_date})"
            )
            return True

    return False


def main():
    parser = argparse.ArgumentParser(
        prog="dispatch_workflow.py",
        description="Executes a Github Workflow and awaits its termination",
        epilog="""Provide a token as GITHUB_OAUTH  environment variable.\n\n
Optionally, dependencies can be provided as DEPENDENCIES environment variable,
containing a JSON array of Owner/Repo strings.""",
    )

    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("workflow_name")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Enforce workflow execution",
    )

    args = parser.parse_args()

    logging.info(f"Repo: {GITHUB_URL}/{args.owner}/{args.repo}")
    logging.info(f"Workflow: {args.workflow_name}")

    token = os.environ["GITHUB_OAUTH"]
    github = Github(token)

    ref = github.get_default_branch(args.owner, args.repo)
    logging.info(f"Detected default branch {ref}")

    if args.force or needs_workflow_execution(
        github, args.owner, args.repo, ref, args.workflow_name
    ):
        logging.info(f"Dispatch workflow {args.workflow_name}")
        run_id = github.dispatch_workflow_and_get_id(
            args.owner, args.repo, ref, args.workflow_name
        )

        logging.info(f"Waiting for run {run_id} to complete")
        run = github.wait_for_workflow_run_completion(args.owner, args.repo, run_id)

        logging.info(f"Run completed with conclusion {run['conclusion']}")
    else:
        run = github.get_lastest_workflow_run(args.owner, args.repo, args.workflow_name)
        if not run:
            # In normal circumstances, this should never happen.
            logging.error("Latest workflow run could not be fetched")
            exit(1)
        logging.info(f"Already up-to-date. (conclusion {run['conclusion']})")

    if run["conclusion"] != "success":
            exit(1)


if __name__ == "__main__":
    main()
