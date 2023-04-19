



import re
import semver
from typing import List
from models.version import Version
from configuration import Configuration

# Regex from the official documentation of semantic versioning 
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEM_VER_REGEX = r".*((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"

BASEVERSION = re.compile(
    r"""[vV]?
        (?P<major>0|[1-9]\d*)
        (\.
        (?P<minor>0|[1-9]\d*)
        (\.
            (?P<patch>0|[1-9]\d*)
        )?
        )?
    """,
    re.VERBOSE,
)

def coerce(version):
    """
    Convert an incomplete version string into a semver-compatible VersionInfo
    object

    * Tries to detect a "basic" version string (``major.minor.patch``).
    * If not enough components can be found, missing components are
        set to zero to obtain a valid semver version.

    :param str version: the version string to convert
    :return: a tuple with a :class:`VersionInfo` instance (or ``None``
        if it's not a version) and the rest of the string which doesn't
        belong to a basic version.
    :rtype: tuple(:class:`VersionInfo` | None, str)
    """
    match = BASEVERSION.search(version)
    if not match:
        return ("*", version)

    ver = {
        key: 0 if value is None else value
        for key, value in match.groupdict().items()
    }
    ver = semver.VersionInfo(**ver)
    rest = match.string[match.end() :]
    return ver, rest

def get_semver(version):
    ver = None
    if not semver.Version.is_valid(version):
        ver, rest = coerce(version)
    else:
        ver = semver.Version.parse(version)
    return ver

class Rule:
    OP_REGEX = r"([<>!=]=|[<>]|==)"
    RULE_REGEX = r"^" + OP_REGEX + r".*" + SEM_VER_REGEX
    OPS_PRIORITY = {"*": -1, "!=": 0, "<": 1, ">": 1, "<=": 2, ">=": 2, "==": 3}

    str_rule: str = None

    semver: str = None
    operator: str = None
    priority: int = None

    def __gt__(self, other: "Rule") -> bool:
        if self.str_rule == "*":
            return False
        if other.str_rule == "*":
            return True
        if self.semver == other.semver:
            return self.priority > other.priority
        return self.semver > other.semver

    def __lt__(self, other: "Rule") -> bool:
        if self.str_rule == "*":
            return False
        if other.str_rule == "*":
            return True
        if self.semver == other.semver:
            return self.priority < other.priority
        return self.semver < other.semver

    def __init__(self, str_rule) -> None:
        self.str_rule = str_rule
        if str_rule == "*":
            self.operator = "*"
            self.semver = "*"
        else:
            match = re.match(self.OP_REGEX, str_rule)
            if match:
                self.operator = match.group(1)
            self.semver = get_semver(self.str_rule)

        self.priority = self.OPS_PRIORITY[self.operator]

        if not self.semver or not self.operator:
            raise ValueError(f"Malformed rule {str_rule}")
        
    def match(self, version):
        if self.str_rule == "*":
            return True
        if not isinstance(version, semver.Version):
            return False
        return version.match(self.operator + str(self.semver))
    
    def is_stronger(self, other: "Rule"):
        if self.operator == "*":
            return False
        if other.operator == "*":
            return True
        
        if self.operator == ">" or self.operator == ">=":
            return self.semver < other.semver

        if self.operator == "<" or self.operator == "<=":
            return self.semver > other.semver
                
        return self.priority > other.priority

    
class RestrictFolder:

    include_folders = {}
    exclude_folders = {}

    def __init__(self, versions: List[Version], configuration: Configuration) -> None:
        self.versions = versions
        self.include_folders_filters = configuration.include_folders
        self.exclude_folders_filters = configuration.exclude_folders

        self.semver_names = {}
        self.__prepare_versions()
        self.include_ruleset = sorted([Rule(rule) for rule in self.include_folders_filters.keys()])
        self.exclude_ruleset = sorted([Rule(rule) for rule in self.exclude_folders_filters.keys()])
        self.__compute_rules()

        print("include : ", self.include_folders)
        print("exclude : ", self.exclude_folders)

    def __prepare_versions(self) -> None:
        # bind a version to a semver
        # * is the default field.
        # unprocessable version refer to default
        # all unspecified version refer also to default
        for version in self.versions:
            ver = ""
            if version.name:
                ver = get_semver(version.name)
            else:
                ver = get_semver(version.tag)
            self.semver_names[version] = ver

        # Prepare the versions
        self.include_folders["*"] = set()
        self.exclude_folders["*"] = set()
        for version in self.semver_names.values():
            self.include_folders[version] = set()
            self.exclude_folders[version] = set()

    def __compute_rules(self) -> None:
        for version in self.include_folders.keys():
            # Compute include rules
            strongest_rule = None
            for rule in self.include_ruleset:
                if rule.match(version):
                    if not strongest_rule:
                        strongest_rule = rule
                    else:
                        if rule.is_stronger(strongest_rule):
                            strongest_rule = rule
            print(self.include_folders_filters[strongest_rule.str_rule])
            self.include_folders[version].update(self.include_folders_filters[strongest_rule.str_rule])
            # Compute exclude rules
            strongest_rule = None
            for rule in self.exclude_ruleset:
                if rule.match(version):
                    if not strongest_rule:
                        strongest_rule = rule
                    else:
                        if rule.is_stronger(strongest_rule):
                            strongest_rule = rule
            self.exclude_folders[version].update(self.exclude_folders_filters[strongest_rule.str_rule])
        
    def get_include_folders(self, version: Version) -> List[str]:
        if self.include_folders[self.semver_names[version]]:
            print(self.include_folders[self.semver_names[version]])
            return list(self.include_folders[self.semver_names[version]])
        return list()
    
    def get_exclude_folders(self, version: Version) -> List[str]:
        if self.exclude_folders[self.semver_names[version]]:
            return list(self.exclude_folders[self.semver_names[version]])
        return list()

    
