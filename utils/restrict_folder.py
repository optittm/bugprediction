

import re
import semver
from typing import List
from models.version import Version
from configuration import Configuration

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
    """
    Parses a string `version` and returns a `semver.Version` object if it
    represents a valid semantic version, or attempts to coerce it to a valid
    format if possible.

    Args:
        version: A string representing a semantic version.

    Returns:
        If `version` is a valid semantic version string, a `semver.Version`
        object representing the version is returned. If `version` is not a
        valid semantic version string, but can be coerced into one, the coerced
        `semver.Version` object is returned. If `version` cannot be coerced or
        is `None`, `*` is returned.

    Raises:
        This function does not raise any exceptions.

    Example usage:
        >>> get_semver("1.2.3")
        <semver.Version('1.2.3')>
        >>> get_semver("1.2.3-beta.1")
        <semver.Version('1.2.3-beta.1')>
        >>> get_semver("1.2.3-rc.2+build.123")
        <semver.Version('1.2.3-rc.2+build.123')>
        >>> get_semver("v1.2.3")
        <semver.Version('1.2.3')>
        >>> get_semver("1.2.3.4")
        <semver.Version('1.2.3-4')>
        >>> get_semver('azer')
        "*"
    """
    ver = None
    if not semver.Version.is_valid(version):
        ver, rest = coerce(version)
    else:
        ver = semver.Version.parse(version)
    return ver

class Rule:
    """
    Represents a rule to compare a version with a given semantic version string pattern.

    Attributes:
        SEM_VER_REGEX (str): The regular expression pattern for a semantic version string.
        OP_REGEX (str): The regular expression pattern for a comparison operator.
        RULE_REGEX (str): The regular expression pattern for a rule.
        OPS_PRIORITY (dict): A dictionary of operators and their respective priorities.
        str_rule (str): The input string representing the rule.
        semver (str): The semantic version string extracted from the input string.
        operator (str): The comparison operator extracted from the input string.
        priority (int): The priority of the comparison operator.
    """

    # Regex from the official documentation of semantic versioning 
    # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    SEM_VER_REGEX = r"((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"

    OP_REGEX = r"([<>!=]=|[<>]|==)"
    RULE_REGEX = r"^" + OP_REGEX + r".*" + SEM_VER_REGEX

    str_rule: str = None

    semver: str = None
    operator: str = None
    
    def __hash__(self):
        """
        Return the hash value of the Rule object. This is used for fast lookup in
        hash-based data structures like dictionaries and sets. Two Rule objects
        that compare equal should have the same hash value.

        Returns:
            The hash value of the Rule object.
        """
        if self.operator == "*":
            return hash("*")
        return hash(self.operator + str(self.semver))

    def __init__(self, str_rule: str) -> None:
        """
        Initializes a new instance of the Rule class.

        Args:
        - str_rule: A string representation of the rule to be parsed and stored.
        """
        self.str_rule = str_rule
        if str_rule == "*":
            self.operator = "*"
            self.semver = "*"
        else:
            match = re.match(self.OP_REGEX, str_rule)
            if match:
                self.operator = match.group(1)
            else:
                self.operator = "*"
            self.semver = get_semver(self.str_rule)
        
    def match(self, version) -> bool:
        """
        Determine if the given version matches this rule.

        Args:
            version: A string or Version instance representing the version to match.

        Returns:
            True if the version matches the rule, False otherwise.
            
        Raises:
            TypeError: If the version is not a string or Version instance.
        """
        if self.operator == "*":
            return True
        if isinstance(version, str) and version == "*":
            return True
        return version.match(self.operator + str(self.semver))
    
class RestrictFolder:
    """
    A class to filter included and excluded folders according to specified rules and versions.

    Attributes:
    -----------
    include_folders : dict
        A dictionary of included folders for each semver version and the default "*".
    exclude_folders : dict
        A dictionary of excluded folders for each semver version and the default "*".
    """

    include_folders = {}
    exclude_folders = {}

    def __init__(self, versions: List[Version], configuration: Configuration) -> None:
        """
        Initializes a RestrictFolder object.

        Args:
        - versions: a list of Version objects representing the versions of a project.
        - configuration: a Configuration object containing the include and exclude folder filters.
        """
        self.versions = versions
        self.include_folders_filters = configuration.include_folders
        self.exclude_folders_filters = configuration.exclude_folders

        self.semver_names = {}
        self.__prepare_versions()

        self.include_ruleset = [Rule(rule) for rule in self.include_folders_filters.keys()]
        self.exclude_ruleset = [Rule(rule) for rule in self.exclude_folders_filters.keys()]
        self.__compute_rules()

    def __prepare_versions(self) -> None:
        """
        Bind each version to its corresponding semver version, either based on the name or the tag.
        "*" is used as the default field for unprocessable and unspecified versions.
        """
        for version in self.versions:
            name_ver = get_semver(version.name)
            tag_ver = get_semver(version.tag)

            if isinstance(name_ver, str) or isinstance(tag_ver, str):
                self.semver_names[version] = name_ver
            else:
                self.semver_names[version] = tag_ver

        # Prepare the versions
        for version in self.semver_names.values():
            self.include_folders[version] = set()
            self.exclude_folders[version] = set()
        self.include_folders["*"] = set()
        self.exclude_folders["*"] = set()

    def __compute_rules(self) -> None:
        """
        This method computes the include and exclude rules for each version. 
        It iterates over the list of versions and for each version it finds the strongest 
        rule for include and exclude by checking all the rules defined for that version. 
        Then it updates the include and exclude folders sets for that version using the 
        strongest rules. The method uses the Rule class to match and compare the rules.
        """

        for version in self.semver_names.values():
            if not isinstance(version, str):
                # version is semver.Version or "*"
                # Compute include rules
                # Get all rule matched with the version
                strongest_rule = set()
                for rule in self.include_ruleset:
                    if rule.match(version) and rule.str_rule != "*":
                        strongest_rule.add(rule)

                # Get all folder for the matched rule
                matched_folder = set()
                if len(strongest_rule) > 0:
                    for matched_rule in strongest_rule:
                        matched_folder.update(self.include_folders_filters[matched_rule.str_rule])
                else:
                    matched_folder.update(self.include_folders_filters["*"])

                # Store the value
                self.include_folders[version].update(matched_folder)

                # Compute exclude rules
                # Get all rule matched with the version
                strongest_rule = set()
                for rule in self.exclude_ruleset:
                    if rule.match(version) and rule.str_rule != "*":
                        strongest_rule.add(rule)

                # Get all folder for the matched rule
                matched_folder = set()
                if len(strongest_rule) > 0:
                    for matched_rule in strongest_rule:
                        matched_folder.update(self.exclude_folders_filters[matched_rule.str_rule])
                else:
                    matched_folder.update(self.exclude_folders_filters["*"])

                # Store the value
                self.exclude_folders[version].update(matched_folder)
        
    def get_include_folders(self, version: Version) -> List[str]:
        """
        This method get_include_folders returns a list of include folders for a specific version.

        Args:
            version (Version): A Version object representing the version for which to retrieve 
            the include folders.

        Returns:
            List[str]: A list of include folders for the specified version. If there are no 
            include folders for the version, an empty list is returned.
        """
        print("SEM_VER_NAME : ", self.semver_names[version], ", FOR VERSION NAME :", version.name, ", TAG : ", version.tag)
        print("INCLUDE FILE : ", self.include_folders[self.semver_names[version]])
        if self.include_folders[self.semver_names[version]]:
            return list(self.include_folders[self.semver_names[version]])
        return list()
    
    def get_exclude_folders(self, version: Version) -> List[str]:
        """
        This method get_exclude_folders returns a list of exclude folders for a specific version.

        Args:
            version (Version): A Version object representing the version for which to retrieve 
            the exclude folders.

        Returns:
            List[str]: A list of exclude folders for the specified version. If there are no 
            exclude folders for the version, an empty list is returned.
        """        
        print("SEM_VER_NAME : ", self.semver_names[version], ", FOR VERSION NAME :", version.name, ", TAG : ", version.tag)
        print("EXCLUDE FILE : ", self.exclude_folders[self.semver_names[version]])
        if self.exclude_folders[self.semver_names[version]]:
            return list(self.exclude_folders[self.semver_names[version]])
        return list()
    