#!/bin/env python3

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .template.template import Template

PATH_JOB_TEMPLATE = Path("template/job_template.yml")
PATH_NIGHTLY_TEMPLATE = Path("template/nightly_template.yml")
PATH_CUSTOM_JOBS_TEMPLATE = Path("template/custom_jobs_template.yml")
PATH_FORCE_BUILD_JOB = Path("template/force_rebuild_job_template.yaml")
PATH_NIGHTLY = Path(".github/workflows/nightly.yml")


def main():
    repo_dependencies_json = os.environ["DEPENDENCIES"]
    repo_dependencies: Dict[str, List[str]] = json.loads(repo_dependencies_json)

    jobs = {}
    jobs.update(Template(PATH_FORCE_BUILD_JOB).load_raw())

    custom_jobs_template = Template(PATH_CUSTOM_JOBS_TEMPLATE)
    variables = {
        "repo_names": list(repo_dependencies.keys()),
        "repo_names_short": [
            dep_name.split("/")[1] for dep_name in repo_dependencies.keys()
        ],
    }
    custom_jobs: Any = custom_jobs_template.load(variables)
    repo_dependencies.update(custom_jobs["templated"])
    if custom_jobs["custom"]:
        jobs.update(custom_jobs["custom"])

    job_template = Template(PATH_JOB_TEMPLATE)
    for repo_name, dependencies in sorted(repo_dependencies.items()):
        dependencies.sort()
        variables = {
            "repo_name": repo_name,
            "repo_name_short": repo_name.split("/")[1],
            "repo_owner": repo_name.split("/")[0],
            "needs": [dep_name.split("/")[1] for dep_name in dependencies] + ["set-force-build"],
            "deps_json": json.dumps(dependencies),
        }
        jobs.update(job_template.load(variables))  # type: ignore

    nightly_template = Template(PATH_NIGHTLY_TEMPLATE)
    variables = {"jobs": jobs}
    nightly_template.dump(variables, PATH_NIGHTLY)


if __name__ == "__main__":
    main()
