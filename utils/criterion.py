
from abc import ABC, abstractmethod
from sklearn import preprocessing
from exceptions.topsis_configuration import InvalidCriterionError, MissingWeightError, NoCriteriaProvidedError

import utils.math as mt

class CriterionParser:
    """
    A class responsible for parsing criteria and alternatives.

    Attributes:
        criteria_map (dict): A mapping of criterion names to Criterion instances.

    Methods:
        parse_criteria(criteria_names, weights): Parses criteria with their weights.
    """

    def __init__(self):
        self.criteria_map = {
            'bugs': BugCriteria()
        }

    def parse_criteria(self, criteria_names, weights):
        """
        Parses criteria with their weights.

        Args:
            criteria_names (list of str): Names of the criteria to parse.
            weights (list of float): Weights corresponding to the criteria.

        Returns:
            list of Criterion: List of parsed criteria with their weights.

        Raises:
            InvalidCriterionError: If an invalid criterion name is encountered.
            MissingWeightError: If some criteria are missing weights.
            NoCriteriaProvidedError: If no criteria are provided.
        """
        if not criteria_names:
            raise NoCriteriaProvidedError("No criteria provided")

        criteria = [self.criteria_map.get(name) for name in criteria_names]
        criteria = [criterion for criterion in criteria if criterion is not None]

        if len(criteria) != len(criteria_names):
            raise InvalidCriterionError("Invalid criterion name(s)")

        if len(criteria) > len(weights):
            raise MissingWeightError("Some criteria are missing weights")

        for index, criterion in enumerate(criteria):
            criterion.set_weight(weights[index])

        return criteria


class Criterion(ABC):
    """
    An abstract base class representing a criterion.

    Attributes:
        weight (float): The weight of the criterion.

    Methods:
        get_name(): Returns the name of the criterion.
        get_direction(): Returns the direction of the criterion.
        get_data(df): Returns the data corresponding to the criterion from the DataFrame.
        set_weight(weight): Sets the weight of the criterion.
        get_weight(): Returns the weight of the criterion.
    """

    def __init__(self):
        self.weight = None

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_direction(self):
        pass

    def get_data(self, df):
        """
        Returns the data corresponding to the criterion from the DataFrame.

        Args:
            df (DataFrame): The DataFrame containing the data.

        Returns:
            numpy.ndarray: Normalized data corresponding to the criterion.
        """
        return preprocessing.normalize([df[self.get_name()].to_numpy()])

    def set_weight(self, weight):
        """
        Sets the weight of the criterion.

        Args:
            weight (float): The weight to set.
        """
        self.weight = float(weight)

    def get_weight(self):
        """
        Returns the weight of the criterion.

        Returns:
            float: The weight of the criterion.
        """
        return self.weight


class BugCriteria(Criterion):
    """
    A concrete implementation of the Criterion class for the 'bugs' criterion.
    """

    def get_name(self):
        return "bugs"

    def get_direction(self):
        return mt.Math.TOPSIS.MAX