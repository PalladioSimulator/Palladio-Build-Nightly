import re
from pathlib import Path
from typing import Any, Dict

from ruamel.yaml import YAML


class Template:
    """
    Class to open, substitute and dump YAML templates for GitHub actions.

    Variables are defined as {{ $variable }}. If a variable can not be resolved
    it is ignored. This allows using this for GitHub actions.
    """

    def __init__(self, path: Path):
        self.path = path
        self.data = None
        self.yaml = YAML()

    def load_raw(self) -> Any:
        """
        Load YAML a template without substitution.
        """
        if not self.data:
            with open(self.path) as file:
                self.data = self.yaml.load(file)

        return self.data

    def load(self, variables: Dict[str, Any]):
        """
        Loads and substitutes a YAML template.
        """
        data = Template._substitute(self.load_raw(), variables)
        return data

    def dump(self, variables: Dict[str, Any], path: Path):
        """
        Dumps the template substituted to path.
        """
        with open(path, "w") as file:
            self.yaml.dump(self.load(variables), file)

    @staticmethod
    def _substitute(yamlobject: Any, variables: Dict[str, Any]):
        """
        Recursively substitutes the variables of the YAML object.
        """
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
        """
        Finds all variables in a string.
        """
        return re.findall(r"\$\{\{\s*(\S+)\s*\}\}", string)

    @staticmethod
    def _replace_variable(string: str, variable: str, value: str):
        """
        Replaces a variable with a value.
        """
        return re.sub(
            r"\$\{\{\s*" + re.escape(variable) + r"\s*\}\}",
            value,
            string,
        )
