import re
from pathlib import Path
from typing import Any, Dict

import yaml

from ..yaml.github_action_loader import GithubActionSafeLoader


class Template:
    def __init__(self, path: Path):
        self.path = path
        self.data = None

    def load_raw(self) -> Any:
        if not self.data:
            with open(self.path) as file:
                self.data = yaml.load(
                    file,
                    Loader=GithubActionSafeLoader,
                )
        return self.data

    def load(self, variables: Dict[str, Any]):
        data = Template._substitute(self.load_raw(), variables)
        return data

    def dump(self, variables: Dict[str, Any], path: Path):
        with open(path, "w") as file:
            yaml.dump(
                self.load(variables), file, default_flow_style=False, sort_keys=False
            )

    @staticmethod
    def _substitute(yamlobject: Any, variables: Dict[str, Any]):
        match yamlobject:
            case dict():
                return {
                    Template._substitute_str(k, variables): Template._substitute(
                        v, variables
                    )
                    for k, v in yamlobject.items()
                }
            case list():
                return [Template._substitute(v, variables) for v in yamlobject]
            case str():
                return Template._substitute_str(yamlobject, variables)
            case _:
                return yamlobject

    @staticmethod
    def _substitute_str(yamlstr: str, variables: Dict[str, Any]) -> str | Any:
        """
        Substitutes all known variables in a string.

        If all variables are string valued the substituted string is returned,
        else if one variable was not string valued the first non-string is returned.
        """
        subst = yamlstr
        for variable in Template._get_variables(yamlstr):
            if variable in variables:
                value = variables[variable]
                if not isinstance(value, str):
                    return value
                subst = Template._replace_variable(subst, variable, value)
        return subst

    @staticmethod
    def _get_variables(string: str):
        return re.findall(r"\$\{\{\s*(\S+)\s*\}\}", string)

    @staticmethod
    def _replace_variable(string: str, variable: str, value: str):
        return re.sub(
            r"\$\{\{\s*" + re.escape(variable) + r"\s*\}\}",
            value,
            string,
        )
