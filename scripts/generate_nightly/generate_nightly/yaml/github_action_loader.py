import re

from yaml.loader import Composer, Parser, Reader, Resolver, SafeConstructor, Scanner


class GithubActionResolver(Resolver):
    """
    A custom resolver that does not treat "on" as boolean (as per YAML spec),
    instead it is treated as string instead.
    """
    @classmethod
    def replace_implicit_resolver(cls, tag, regexp, old_first):
        for ch in old_first:
            for i, (tag_i, _) in enumerate(cls.yaml_implicit_resolvers[ch]):
                if tag_i == tag:
                    cls.yaml_implicit_resolvers[ch][i] = (tag, regexp)

GithubActionResolver.replace_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(
        r"""^(?:yes|Yes|YES|no|No|NO
                    |true|True|TRUE|false|False|FALSE)$""",
        re.X,
    ),
    list("yYnNtTfFoO"),
)

class GithubActionSafeLoader(
    Reader, Scanner, Parser, Composer, SafeConstructor, GithubActionResolver
):
    """
    A custom loader that does not treat "on" as boolean (as per YAML spec),
    instead it is treated as string instead.
    """
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        GithubActionResolver.__init__(self)
