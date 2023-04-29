# Palladio-Build-Nightly

This repository contains two workflows. `update_build.yml` runs a dependency tool to generate `nightly.yml` which contains the build jobs for the nightly build in the Palladio organization. The jobs no not actually build the project but trigger the workflows on the corresponding repo instead.

- `update_build.yml`

    + Runs [Palladio-Build-DependencyTool](https://github.com/PalladioSimulator/Palladio-Build-DependencyTool) to determine the repositories that need to be build and the dependencies between them.
    + Generates `nightly.yml` which contains the jobs that trigger the workflows on the repositories.

- `nightly.yml`


## Configuration

The build can be configured by changing the templates in the `/template` folder. These variables are automatically replaced by the update script.

### `nightly_template.yml`

| Variable | Type | Description |
|----------|------|-------------|
| `${{ jobs }}` | object | The jobs which are generated from `job_template.yml`. |

### `job_template.yml`

| Variable | Type | Description |
|----------|------|-------------|
| `${{ repo_name }}` | string | The full name of the repository in the form `User/Reponame`. |
