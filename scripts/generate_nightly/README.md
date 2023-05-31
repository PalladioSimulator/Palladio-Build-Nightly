# generate_nightly

This is a simple templating engine that builds a GitHub workflow file from templates and dependencies.

## Usage

The dependencies must be supplied as environment variable `DEPENDENCIES` (easier GitHub Action integration) 
and represented as JSON dictionary of `Owner/Repo -> Array[Owner/Repo]`.

See the repo README for a documentation of the template files.

## Exection

```bash
# This project uses poetry for dependency management
poetry install

# Run the script in the poetry venv
DEPENDENCIES=... poetry run python -m generate_nightly
```
