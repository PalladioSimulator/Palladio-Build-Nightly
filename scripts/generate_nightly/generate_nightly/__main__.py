#!/bin/env python3

import json
import os
from pathlib import Path
from typing import Dict, List

from .template.template import Template

PATH_JOB_TEMPLATE = Path("template/job_template.yml")
PATH_NIGHTLY_TEMPLATE = Path("template/nightly_template.yml")
PATH_NIGHTLY = Path(".github/workflows/nightly.yml")


def main():
    repo_dependencies_json = os.environ["DEPENDENCIES"]
    repo_dependencies: Dict[str, List[str]] = json.loads(repo_dependencies_json)

    job_template = Template(PATH_JOB_TEMPLATE)
    jobs = {}
    for repo_name, dependencies in sorted(repo_dependencies.items()):
        dependencies.sort()
        variables = {
            "repo_name": repo_name,
            "repo_name_short": repo_name.split("/")[1],
            "repo_owner": repo_name.split("/")[0],
            "deps_short": [dep_name.split("/")[1] for dep_name in dependencies],
            "deps_json": json.dumps(dependencies)
        }
        jobs.update(job_template.load(variables)) # type: ignore

    nightly_template = Template(PATH_NIGHTLY_TEMPLATE)
    variables = {
        "jobs": jobs
    }
    nightly_template.dump(variables, PATH_NIGHTLY)



if __name__ == "__main__":
    main()
