# Palladio-Build-Nightly

This repository contains two workflows. `update_build.yml` runs a dependency tool to generate `nightly.yml` which contains the build jobs for the nightly build in the Palladio organization. The jobs do not actually build the project but trigger the workflows on the corresponding repo instead.

- `update_build.yml`

    + Runs [Palladio-Build-DependencyTool](https://github.com/PalladioSimulator/Palladio-Build-DependencyTool) to determine the repositories that need to be build and the dependencies between them.
    + Generates `nightly.yml` which contains the jobs that trigger the workflows on the repositories.
    + Caution: The dependency tool generates a lot (near 1000) API calls and can therefore be only run once per hour when using the GitHub provided token which has a rate limit of 1000 API calls/hour.

- `nightly.yml`

    + Executes the workflow on the corresponding repositories and reports their outcome.
    + The workflows are only executed if:
        * No workflow was run on the repository.
        * There was a commit since the last workflow run.
        * There was a successful workflow run on a dependency since the last workflow run. Only the last 30 workflow runs are checked.


## Configuration

The build can be configured by changing the templates in the `/template` folder. These variables are automatically replaced by the update script.

### `nightly_template.yml`

| Variable | Type | Description |
|----------|------|-------------|
| `${{ jobs }}` | object | The jobs which are generated from `job_template.yml`. |

### `job_template.yml`

| Variable | Type | Description |
|----------|------|-------------|
| `${{ repo_name }}` | string | The full name of the repository in the form `Owner/Reponame`. |
| `${{ repo_name_short }}` | string | The name of the repository in the form `Reponame` (without the owner). |
| `${{ deps_short }}` | array | The build dependencies. An array of short repository names. |
| `${{ repo_owner }}` | string | The name of the owner. |
| `${{ deps_json }}` | string | The build dependencies as JSON array. | 
