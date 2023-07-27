
from abc import ABC, abstractmethod

from sklearn import preprocessing

from exceptions.topsis_configuration import InvalidAlternativeError, NoAlternativeProvidedError

class AlternativesParser:
    """
    A class responsible for parsing alternatives.

    Attributes:
        alternatives_map (dict): A mapping of alternative names to Alternative instances.

    Methods:
        parse_alternatives(alternatives_names): Parses alternatives with their names.
    """

    def __init__(self):
        self.alternatives_map = {
            'bug_velocity': BugVelocityAlternative(),
            'changes': ChangesAlternative(),
            'team_xp': AvgTeamXPAlternative(),
            'complexity': AvgComplexityAlternative(),
            'code_churn': CodeChurnAlternative(),
            'legacy_files': NbLegacyFileAlternative()
        }

    def parse_alternatives(self, alternatives_names):
        """
        Parses alternatives with their names.

        Args:
            alternatives_names (list of str): Names of the alternatives to parse.

        Returns:
            list of Alternative: List of parsed alternatives.

        Raises:
            InvalidAlternativeError: If an invalid alternative name is encountered.
        """
        if not alternatives_names:
            raise NoAlternativeProvidedError("No alternatives provided")
        
        alternatives = [self.alternatives_map.get(name) for name in alternatives_names]
        alternatives = [alternative for alternative in alternatives if alternative is not None]

        if len(alternatives) != len(alternatives_names):
            raise InvalidAlternativeError("Invalid alternatives name(s)")

        return alternatives


class Alternative(ABC):
    """
    An abstract base class representing an alternative.

    Methods:
        get_name(): Returns the name of the alternative.
        get_data(df): Returns the data corresponding to the alternative from the DataFrame.
    """

    @abstractmethod
    def get_name(self):
        pass

    def get_data(self, df):
        """
        Returns the data corresponding to the alternative from the DataFrame.

        Args:
            df (DataFrame): The DataFrame containing the data.

        Returns:
            numpy.ndarray: Normalized data corresponding to the alternative.
        """
        return preprocessing.normalize([df[self.get_name()].to_numpy()])


class BugVelocityAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'bug_velocity' alternative.
    """

    def get_name(self):
        return 'bug_velocity'


class ChangesAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'changes' alternative.
    """

    def get_name(self):
        return 'changes'


class AvgTeamXPAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'avg_team_xp' alternative.
    """

    def get_name(self):
        return 'avg_team_xp'


class AvgComplexityAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'avg_complexity' alternative.
    """

    def get_name(self):
        return 'lizard_avg_complexity'


class CodeChurnAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'code_churn' alternative.
    """

    def get_name(self):
        return 'code_churn_avg'
    
class NbLegacyFileAlternative(Alternative):
    """
    A concrete implementation of the Alternative class for the 'nb_legacy_files' alternative.
    """

    def get_name(self):
        return 'nb_legacy_files'

