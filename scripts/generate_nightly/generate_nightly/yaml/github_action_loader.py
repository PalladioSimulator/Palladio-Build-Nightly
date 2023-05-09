import re

from yaml.loader import Composer, Parser, Reader, Resolver, SafeConstructor, Scanner


class GithubActionResolver(Resolver):
    @classmethod
    def replace_implicit_resolver(cls, tag, regexp, old_first):
        for ch in old_first:
            for i, (tag_i, regexp_i) in enumerate(cls.yaml_implicit_resolvers[ch]):
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
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        GithubActionResolver.__init__(self)
