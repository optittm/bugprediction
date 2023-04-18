



import re
import semver
from typing import List
from models.version import Version
from configuration import Configuration

class Rule:
    OP_REGEX = r"([<>!=]=|[<>]|==)"
    # Regex from the official documentation of semantic versioning 
    # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    SEM_VER_REGEX = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    RULE_REGEX = r"^" + OP_REGEX + r".*" + SEM_VER_REGEX
    OPS_PRIORITY = {"*": -1, "<": 0, ">": 0, "<=": 1, ">=": 1, "==": 2, "!=": 2}
    OPERATORS = {
        "==": lambda x: x == 0,
        "!=": lambda x: x != 0,
        ">": lambda x: x > 0,
        ">=": lambda x: x >= 0,
        "<": lambda x: x < 0,
        "<=": lambda x: x <= 0
    }

    def __eq__(self, other: "Rule") -> bool:
        return self.operator == other.operator and self.version_ref == other.version_ref

    def __init__(self, str_rule, versions) -> None:
        self.versions = versions
        print([v.tag for v in versions])
        self.str_rule = str_rule
        match = re.match(self.SEM_VER_REGEX, str_rule)
        if match:
            self.operator = match.group(1)
            self.version_ref = match.group(2)
            self.version = self.__get_version_from_tag(self.version_ref)
            if not self.version:
                raise ValueError(f"Unknown version {self.version_ref}")
        elif str_rule == "*":
            self.operator = "*"
            self.version_ref = "*"
            self.version = None
        else:
            raise ValueError(f"Malformed rule {str_rule}")
        
        self.priority = self.OPS_PRIORITY[self.operator]

    def __get_version_from_tag(self, tag: str) -> Version:
        for version in self.versions:
            if version.tag == tag:
                return version
        return None
    
    def __compare_version(self, version: Version) -> int:
        return (int(self.version.start_date.timestamp()) - int(version.start_date.timestamp())) * -1
    
    def match(self, version) -> bool:
        if self.version_ref == "*":
            return True

        compare = self.__compare_version(version)
        return self.OPERATORS[self.operator](compare)
    
    def matchs(self, versions: List[Version]) -> List[Version]:
        filtered_version = []
        for version in versions:
            if self.match(version):
                filtered_version.append(version)
        return filtered_version
    
    def is_prio(self, other: "Rule") -> bool:
        """TODO"""
        if not other.version or self == other:
            return True
        else:
            """TODO"""
    

class RestrictFolder:

    include_folders = {}
    exclude_folders = {}
    version_name_to_semver_name = {}

    def __init__(self, versions: List[Version], configuration: Configuration) -> None:
        self.versions = versions
        self.include_folders_filters = configuration.include_folders
        self.exclude_folders_filters = configuration.exclude_folders

        self.__prepare_versions()

        self.__compute_rules(self.include_folders_filters, self.include_folders)
        self.__compute_rules(self.exclude_folders_filters, self.exclude_folders)

    def __prepare_versions(self) -> None:
        for version in self.versions:
            match = re.match(Rule.SEM_VER_REGEX, version.tag)
            if match:
                self.version_name_to_semver_name[version.tag] = match.group(0)


        # Prepare the versions
        for version in self.versions:
            self.include_folders[version.tag] = set()
            self.exclude_folders[version.tag] = set()

    def __compute_rules(self, rules: List | dict, folders) -> None:
        if isinstance(rules, dict):
            self.__compute_rules_dict(rules, folders)
        else:
            self.__compute_rules_list(rules, folders)

    def __compute_rules_dict(self, rules: dict, folder) -> None:
        for rule in rules.keys():
            restrict_rule = Rule(rule, self.versions)
            matched_versions = restrict_rule.matchs(self.versions)
            for matched_version in matched_versions:
                folder[matched_version.tag].update(rules[rule])

    def __compute_rules_list(self, rules: List[str], folder) -> None:
        for version in self.versions:
            folder[version.tag].update(rules)

        
    def get_include_folders(self, tag: str) -> List[str]:
        if self.include_folders[tag]:
            return list(self.include_folders[tag])
        return None
    
    def get_exclude_folders(self, tag: str) -> List[str]:
        if self.exclude_folders[tag]:
            return list(self.exclude_folders[tag: str])
        return None

    
