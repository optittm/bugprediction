
import logging
import re
import semver
from typing import List
from models.version import Version
from configuration import Configuration

class BaseSemVer:
    """
    The BaseSemVer class represents a base Semantic Versioning object.
    The class provides methods for parsing and coercion of a Semantic Version string
    into a valid SemVer object.

    Attributes:
        SEM_VER_REGEX (str): A regular expression for validating a semantic version string.
        BASEVERSION (re.Pattern): A regular expression pattern object for coercing a version string
                                   to a SemVer object.
    """
    
    # Regex from the official documentation of semantic versioning 
    # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
    SEM_VER_REGEX = r"((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
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

    def __hash__(self) -> int:
        return hash(self.version)

    def __init__(self, str_ver) -> None:
        pass

    def match(self, rule: str) -> bool:
        pass

    def is_default(self) -> bool:
        return isinstance(self, DefaultSemVer)

    @staticmethod
    def coerce(version: str) -> tuple:
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
        match = BaseSemVer.BASEVERSION.search(version)
        if not match:
            return (None, version)

        ver = {
            key: 0 if value is None else value
            for key, value in match.groupdict().items()
        }
        ver = semver.VersionInfo(**ver)
        rest = match.string[match.end() :]
        return ver, rest
    
    @staticmethod
    def parse(str_ver) -> "BaseSemVer":
        """
        Parses a semantic version string and returns a corresponding BaseSemVer object.

        Args:
            str_ver (str): The semantic version string to parse.

        Returns:
            BaseSemVer: A BaseSemVer object corresponding to the given string.

        Raises:
            ValueError: If the string is not a valid semantic version.
        """
        try:
            return SemVersion(str_ver)
        except ValueError:
            return DefaultSemVer()
        

class SemVersion(BaseSemVer):
    """
    A class representing a semantic version object.

    Attributes:
    - version (semver.Version): The parsed semantic version.
    - str_ver (str): The original semantic version string.
    """

    def __init__(self, ver) -> None:
        """
        This method is the constructor for the SemVersion class, which initializes the instance variables of the class.

        Args:
            ver (str or semver.Version): The version string to be parsed or a semver.Version instance.

        Raises:
        TypeError: If the input ver is neither a str nor a semver.Version.
        ValueError: If the input ver is a str but is malformed.
        """
        if isinstance(ver, semver.Version):
            self.str_ver = str(ver)
            self.version = ver

        elif isinstance(ver, str):
            self.str_ver = ver
            # Parse a semver from the str
            match = re.match(BaseSemVer.SEM_VER_REGEX, self.str_ver)
            if match:
                self.version = semver.Version.parse(match.group(0))
            else:
                self.version, rest = BaseSemVer.coerce(ver)
            
        else:
            raise TypeError("Wrong type ", type(ver))
        
        # If the str cannot be parse raise a value error
        if not self.version:
            raise ValueError("Malfermed version : ", ver)

        
    def match(self, rule: str) -> bool:
        """
        Determines whether this SemVersion object matches the given rule.

        Args:
            rule (str): A string representing a version rule.

        Returns:
            bool: True if this SemVersion object matches the rule, False otherwise.
        """
        return self.version.match(rule)

    
class DefaultSemVer(BaseSemVer):
    """
    Represents the default semver version, which matches any other version.
    """
    
    def __init__(self, str_ver = "*") -> None:
        """
        Initializes a DefaultSemVer object.

        Args:
            str_ver (str, optional): The version string to assign to the object. Defaults to "*".
        """
        self.version = "*"

    def match(self, rule: str) -> bool:
        """
        The match method checks if a rule (in the form of a string) matches the default SemVer (DefaultSemVer) 
        which is represented by the * object. This method returns True because the * object matches all versions.

        Args:
            rule (str): A string representing the rule to be checked.

        Returns:
            bool: True.
        """
        return True


class BaseRule:
    """
    Represents a rule to compare a version with a given semantic version string pattern.
    """
    
    def is_default(self):
        """
        Checks if this is a DefaultRule object.

        Returns:
            bool: True if the object is a DefaultRule object, False otherwise.
        """
        return isinstance(self, DefaultRule)
    
    def __hash__(self):
        pass
    
    def __init__(self, str_rule):
        pass

    def match(self, version):
        pass
    
    @staticmethod
    def is_default_rule(str_rule):
        """
        Checks if the specified string is a default rule.

        Args:
            str_rule (str): The string to check.

        Returns:
            bool: True if the specified string is a default rule, False otherwise.
        """
        return str_rule == "*"

    @staticmethod
    def parse(str_rule):
        """
        Parses the specified string into a rule.

        Args:
            str_rule (str): The string to parse.

        Returns:
            BaseRule: An instance of a subclass of BaseRule.
        """        
        if str_rule == "*":
            return DefaultRule()

        try:
            return BornedRule(str_rule)
        except ValueError:
            # The given string cannot be parsed as a BornedRule
            pass

        try:
            return OperatorRule(str_rule)
        except ValueError:
            # The given string cannot be parsed as a OperatorRule
            pass

        # The given string cannot be parsed raise an error
        raise ValueError("Malformed rule: ", str_rule)
        

    
class OperatorRule(BaseRule):
    """
    Represents a rule with a comparison operator to match a semantic version.
    Inherits from BaseRule.

    Attributes:
        OP_REGEX (str): The regular expression pattern for a comparison operator.
        OPERATOR_RULE_REGEX (str): The regular expression pattern for this type of rule.
        str_rule (str): The original string representation of the rule.
        operator (str): The comparison operator extracted from the string representation.
        version (semver.Version): The semantic version extracted from the string representation.
    """

    OP_REGEX = r"([<>!=]=|[<>]|==)"
    OPERATOR_RULE_REGEX = r"^" + OP_REGEX + r".*" + BaseSemVer.SEM_VER_REGEX

    def __hash__(self):
        """
        Return the hash value of the Rule object. This is used for fast lookup in
        hash-based data structures like dictionaries and sets. Two Rule objects
        that compare equal should have the same hash value.

        Returns:
            The hash value of the Rule object.
        """
        return hash(self.operator + str(self.version))

    def __init__(self, str_rule):
        """
        The __init__ method initializes an OperatorRule object with a given string rule.If the rule string does 
        not contain a valid comparison operator, it defaults to ==. If the semantic version string cannot be 
        extracted from the rule string, the method coerces the rule string to a valid semantic version string.

        Args:
            str_rule (str): A string representing the rule to be initialized.

        Raises:
            ValueError: If the rule string is malformed.
        """
        self.str_rule = str_rule
        
        self.operator = None
        match = re.match(OperatorRule.OP_REGEX, str_rule)
        if match:
            self.operator = match.group(0)
        match = re.match(BornedRule.BORNE_REGEX, str_rule)
        if not self.operator and match:
            raise ValueError("Malfermed rule : ", str_rule)
        if not self.operator:
            self.operator = "=="

        match = re.match(BaseSemVer.SEM_VER_REGEX, str_rule)
        if not match:
            transformed_ver, rest = BaseSemVer.coerce(str_rule)
            self.version = transformed_ver
        else: 
            self.version = semver.Version.parse(match.group(0))

        if not self.version:
            raise ValueError("Malfermed rule : ", str_rule)

    def match(self, version: BaseSemVer) -> bool:
        """
        Matches the given semantic version object with the rule represented by the OperatorRule object.
        Returns True if the given version matches the rule; False otherwise.

        Args:
            version (BaseSemVer): The semantic version object to match with the rule.

        Returns:
            bool: True if the given version matches the rule; False otherwise.
        """
        return version.match(self.operator + str(self.version))


class BornedRule(BaseRule):
    """
    Represents a rule that matches versions between two bounds (inclusive or exclusive).
    """

    BORNE_REGEX = r"([\[\]]{2})"
    BORNED_RULE_REGEX = r"^" + BORNE_REGEX + r"?.*" + BaseSemVer.SEM_VER_REGEX + r".*,.*" + BaseSemVer.SEM_VER_REGEX

    def __hash__(self) -> int:
        """
        Return the hash value of the Rule object. This is used for fast lookup in
        hash-based data structures like dictionaries and sets. Two Rule objects
        that compare equal should have the same hash value.

        Returns:
            The hash value of the BornedRule object.
        """
        return hash(self.operator + str(self.lower) + str(self.upper))

    def __init__(self, str_rule) -> None:
        """
        The __init__ method initializes a BornedRule object from a given string rule.

        Args:

            str_rule : str : The string rule to be parsed.

        Raises:

            ValueError: If the given string rule is malformed.
        """
        self.str_rule = str_rule
        
        self.operator = None
        match = re.match(BornedRule.BORNE_REGEX, self.str_rule)
        if match:
            self.operator = match.group(0)
        match = re.match(OperatorRule.OP_REGEX, self.str_rule)
        if not self.operator and match:
            raise ValueError("Malformed rule : ", str_rule)
        if not self.operator:
            self.operator = "[]"

        ver1 = ver2 = None
        ver_str = self.str_rule.split(",")
        if len(ver_str) != 2:
            raise ValueError("Malfermed rule : ", str_rule)
        
        match = re.match(BaseSemVer.SEM_VER_REGEX, ver_str[0])
        if match:
            ver1 = semver.Version.parse(match.group(0))
        else:
            ver1, rest = BaseSemVer.coerce(ver_str[0])

        match = re.match(BaseSemVer.SEM_VER_REGEX, ver_str[1])
        if match:
            ver2 = semver.Version.parse(match.group(1))
        else:
            ver2, rest = BaseSemVer.coerce(ver_str[1])

        if (not ver1) or (not ver2):
            raise ValueError("Malfermed rule : ", str_rule)
            
        if ver1 < ver2:
            self.lower = ver1
            self.upper = ver2
        else:
            self.upper = ver1
            self.lower = ver2
            
    def match(self, version: "BaseSemVer") -> bool:
        """
        The match method checks if a given version satisfies the bounded rule. It takes a semver.Version 
        object as an argument, representing the version to be checked. The method compares the given version 
        with the lower and upper bounds of the rule based on the operator in the rule.

        Returns:
            bool: True if the given version satisfies the rule, False otherwise.
        """
        lower_op = ">" if self.operator[0] == "]" else ">="
        upper_op = "<" if self.operator[1] == "[" else "<="

        lower_cmp = version.version.compare(self.lower)
        upper_cmp = version.version.compare(self.upper)

        return (lower_cmp > 0 if lower_op == ">" else lower_cmp >= 0) \
            and (upper_cmp < 0 if upper_op == "<" else upper_cmp <= 0)

class DefaultRule(BaseRule):
    """
    A class that represents the default rule to match all versions.
    """

    def __hash__(self):
        """
        Return the hash value of the Rule object. This is used for fast lookup in
        hash-based data structures like dictionaries and sets. Two Rule objects
        that compare equal should have the same hash value.

        Returns:
            The hash value of the DefaultRule object.
        """
        return hash("*")

    def __init__(self, str_rule = "*"):
        self.str_rule = str_rule

    def match(self, version):
        return True
    
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

        self.include_ruleset = set()
        self.exclude_ruleset = set()
        self.__compute_ruleset()
        self.__compute_rules()

    def __prepare_versions(self) -> None:
        """
        Bind each version to its corresponding semver version, either based on the name or the tag.
        "*" is used as the default field for unprocessable and unspecified versions.
        """
        for version in self.versions:
            ver = None
            # Trying to parse the version name to a semver
            try:
                ver = BaseSemVer.parse(version.name)
            except ValueError:
                ver = None
            # If the name cannot be parse trying to parse the version tag
            if not ver:
                try:
                    ver = BaseSemVer.parse(version.tag)
                except ValueError:
                    ver = None
            # If both the name and the tag cannot be parse bind the version to the default SemVer
            # The default SemVer always going to macth to the default rule and only the default rule
            if not ver:
                ver = DefaultSemVer()
            self.semver_names[version] = ver

        # Prepare the versions
        for version in set(self.semver_names.values()):
            self.include_folders[version] = set()
            self.exclude_folders[version] = set()

    def __compute_ruleset(self):
        for rule in self.include_folders_filters.keys():
            try:
                self.include_ruleset.add(BaseRule.parse(rule))
            except ValueError:
                # ignore un parsabled rules
                logging.warning(f"The given rule '{rule}' in OTTM_INCLUDE_FOLDER can not be parsed and is ignored")

        for rule in self.exclude_folders_filters.keys():
            try:
                self.exclude_ruleset.add(BaseRule.parse(rule))
            except ValueError:
                # ignore un parsabled rules
                logging.warning(f"The given rule '{rule}' in OTTM_EXCLUDE_FOLDER can not be parsed and is ignored")

    def __compute_rules(self) -> None:
        """
        This method computes the include and exclude rules for each version. 
        It iterates over the list of versions and for each version it finds the strongest 
        rule for include and exclude by checking all the rules defined for that version. 
        Then it updates the include and exclude folders sets for that version using the 
        strongest rules. The method uses the Rule class to match and compare the rules.
        """

        for version in set(self.semver_names.values()):
            # Dont compute for the default version because it's a special case
            if not version.is_default():
                # Compute include rules for this verison
                matched_rule = set()
                for rule in self.include_ruleset:
                    if rule.match(version):
                        matched_rule.add(rule)
                # Convert rules to path list
                for rule in matched_rule:
                    # Dont convert for the default rule because it's a special case
                    if not rule.is_default():
                        self.include_folders[version].update(
                            self.include_folders_filters[rule.str_rule]
                        )
                # Compute exclude rules for this version
                matched_rule = set()
                for rule in self.exclude_ruleset:
                    if rule.match(version):
                        matched_rule.add(rule)
                # Convert rules to path list
                for rule in matched_rule:
                    # Dont convert for the default rule because it's a special case
                    if not rule.is_default():
                        self.exclude_folders[version].update(
                            self.exclude_folders_filters[rule.str_rule]
                        )

            # If the version don't have include rule bind it to the default rule
            if len(self.include_folders[version]) == 0:
                self.include_folders[version].update(
                    self.include_folders_filters[DefaultRule().str_rule]
                )
            # If the version don't have exclude rule bind it to the default rule
            if len(self.exclude_folders[version]) == 0:
                self.exclude_folders[version].update(
                    self.exclude_folders_filters[DefaultRule().str_rule]
                )
        
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
        if self.exclude_folders[self.semver_names[version]]:
            return list(self.exclude_folders[self.semver_names[version]])
        return list()
    