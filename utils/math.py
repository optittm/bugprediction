from statistics import mean
import logging
from typing import List

import numpy as np
from sklearn import preprocessing

class Math():
    nb_decimal_numbers = 2

    @classmethod
    def get_rounded_mean(cls, values):
        values_mean = mean(values)
        return round(values_mean, cls.nb_decimal_numbers)

    @classmethod
    def get_rounded_rate(cls, value, total):
        rate = (1. * value / total) * 100
        return round(rate, cls.nb_decimal_numbers)
    
    @classmethod
    def get_rounded_divide(cls, dividend, divisor):
        try:
            quotient = round(dividend / divisor, cls.nb_decimal_numbers)
        except ZeroDivisionError:
            logging.exception("Math:Cannot divide by zero")
            return None
        else:
            return quotient
            
    @classmethod
    def get_rounded_mean_safe(cls, values):
        if (len(values) > 0):
            return round(mean(values), cls.nb_decimal_numbers)
        return 0
    
    class DecisionMatrixBuilder:
        """
        Builder class for creating a decision matrix using correlation coefficients as criteria values.

        Attributes:
            criteria (List[np.ndarray]): List of criteria arrays.
            criteria_label (List[str]): List of labels for the criteria.
            alternatives (List[np.ndarray]): List of alternative arrays.
            alternatives_label (List[str]): List of labels for the alternatives.
            matrix (Optional[np.ndarray]): The constructed decision matrix.
            criteria_dict (Optional[Dict[str, int]]): Dictionary mapping criteria labels to their indices.
            alternatives_dict (Optional[Dict[str, int]]): Dictionary mapping alternative labels to their indices.
        """

        def __init__(self) -> None:
            self.criteria = []
            self.criteria_label = []
            self.alternatives = []
            self.alternatives_label = []
            
            self.matrix = None
            self.criteria_dict = None
            self.alternatives_dict = None

        def add_criteria(self, values: np.ndarray, label: str) -> 'DecisionMatrixBuilder':
            """
            Add a criteria array with its label to the decision matrix.

            Args:
                values (np.ndarray): The array of criteria values.
                label (str): The label for the criteria.

            Returns:
                DecisionMatrixBuilder: The updated instance of the DecisionMatrixBuilder.
            """
            self.criteria.append(preprocessing.normalize(values))
            self.criteria_label.append(label)
            return self

        def add_alternative(self, values: np.ndarray, label: str) -> 'DecisionMatrixBuilder':
            """
            Add an alternative array with its label to the decision matrix.

            Args:
                values (np.ndarray): The array of alternative values.
                label (str): The label for the alternative.

            Returns:
                DecisionMatrixBuilder: The updated instance of the DecisionMatrixBuilder.
            """
            self.alternatives.append(preprocessing.normalize(values))
            self.alternatives_label.append(label)
            return self

        def build(self) -> 'DecisionMatrixBuilder':
            """
            Build and return the constructed decision matrix.

            Returns:
                DecisionMatrixBuilder: The updated instance of the DecisionMatrixBuilder.

            Raises:
                ValueError: If no criteria or alternatives have been added.
            """
            if not self.criteria or not self.alternatives:
                raise ValueError("No criteria or alternatives have been added.")

            num_criteria = len(self.criteria)
            num_alternatives = len(self.alternatives)

            # Create the decision matrix with zeros
            matrix = np.zeros((num_alternatives, num_criteria))

            # Fill the decision matrix with criteria values
            for i in range(num_criteria):
                for j in range(num_alternatives):
                    if np.var(self.criteria[i]) != 0 and np.var(self.alternatives) != 0:
                        matrix[j, i] = np.corrcoef(self.criteria[i], self.alternatives[j])[0, 1]

            self.matrix = matrix
            self.criteria_dict = {label: i for i, label in enumerate(self.criteria_label)}
            self.alternatives_dict = {label: i for i, label in enumerate(self.alternatives_label)}

            return self
        
    
    class TOPSIS:
        """
        Implementation of the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) algorithm.

        The TOPSIS algorithm is a multi-criteria decision-making method that aims to find the best alternative among a set of alternatives
        based on their similarity to ideal and anti-ideal solutions.

        Args:
            decision_matrix (DecisionMatrixBuilder): The decision matrix representing the performance of alternatives on different criteria.
                                        Shape: (num_alternatives, num_criteria)
                                        Example:
                                        np.array([
                                            [3.0, 4.0, 5.0], # Alternative 1
                                            [2.0, 5.0, 1.0], # Alternative 2
                                            [4.0, 2.0, 3.0], # Alternative 3
                                            [1.0, 3.0, 2.0]  # Alternative 4
                                        ])
            weights (np.ndarray): The weights assigned to each criterion. It should be a 1-dimensional array with the same length
                                as the number of criteria.
            impacts (np.ndarray): The impacts of each criterion, which can be 'positive' or 'negative'. It should be a 1-dimensional
                                array with the same length as the number of criteria.

        Raises:
            ValueError: If the dimensions or lengths of the input arrays are not valid.

        Attributes:
            _decision_matrix (np.ndarray): The decision matrix representing the performance of alternatives on different criteria.
            _weights (np.ndarray): The weights assigned to each criterion.
            _impacts (np.ndarray): The impacts of each criterion.
            _num_criteria (int): The number of criteria.
            _num_alternatives (int): The number of alternatives.
            _weighted_decision_matrix (np.ndarray): The decision matrix after applying weights.
            _ideal (np.ndarray): The ideal solution vector.
            _anti_ideal (np.ndarray): The anti-ideal solution vector.
            _ideal_distance (np.ndarray): The distances from alternatives to the ideal solution.
            _anti_ideal_distance (np.ndarray): The distances from alternatives to the anti-ideal solution.
            _distances (np.ndarray): The pairwise distances between alternatives and ideal/anti-ideal solutions.
            _closeness (np.ndarray): The relative closeness of each alternative.
        """

        MAX = 1
        MIN = -1

        def __init__(self, decision_matrix: "Math.DecisionMatrixBuilder", weights: List, impacts: List) -> None:
            weights = np.array(weights)
            impacts = np.array(impacts)
            if decision_matrix.matrix is None:
                decision_matrix = decision_matrix.build()
            if decision_matrix.matrix.ndim != 2:
                raise ValueError("Decision matrix must be a 2-dimensional array.")
            if weights.ndim != 1 or len(weights) != decision_matrix.matrix.shape[1]:
                raise ValueError("Weights must be a 1-dimensional array with the same length as the number of criteria.")
            if impacts.ndim != 1 or len(impacts) != decision_matrix.matrix.shape[1]:
                raise ValueError("Impacts must be a 1-dimensional array with the same length as the number of criteria.")
            
            self.matrix_builder = decision_matrix
            self._decision_matrix = decision_matrix.matrix
            self._weights = weights
            self._impacts = impacts
            # Compute lengths
            self._num_criteria = self._decision_matrix.shape[1]
            self._num_alternative = self._decision_matrix.shape[0]
            # Prepare matrices
            self._weighted_decision_matrix = np.zeros(shape=self._decision_matrix.shape)

            self._ideal = np.zeros(shape=(1, self._num_criteria))
            self._anti_ideal = np.zeros(shape=(1, self._num_criteria))

            self._ideal_distance = np.zeros(shape=(1, self._num_criteria))
            self._anti_ideal_distance = np.zeros(shape=(1, self._num_criteria))

            self._distances = np.zeros(shape=(self._num_alternative, 2))
            self._closeness = np.zeros(self._num_alternative)

        def _weighted_matrix(self) -> None:
            """
            Applies criteria weights to the decision matrix.

            Args:
                None

            Returns:
                None
            """
            weighted_correlation_matrix = self._decision_matrix.copy()

            for index, weight in enumerate(self._weights):
                weighted_correlation_matrix[:, index] *= weight

            self._weighted_decision_matrix = weighted_correlation_matrix

        def _calculte_matrix_extremum(self, impatcs: np.ndarray) -> np.ndarray:
            """
            Calculates the matrix extremum (ideal or anti-ideal) based on the weighted decision matrix and impacts.

            Args:
                impacts (np.ndarray): The impacts of the criteria.

            Returns:
                np.ndarray: The matrix extremum (ideal or anti-ideal).
            """
            extremum_matrix = np.zeros(self._num_criteria)

            for i in range(self._num_criteria):
                criteria_weights = self._weighted_decision_matrix[:, i]
                if impatcs[i] == Math.TOPSIS.MAX:
                    extremum_value = np.max(criteria_weights)
                else:
                    extremum_value = np.min(criteria_weights)
                extremum_matrix[i] = extremum_value

            return extremum_matrix
        
        def _ideal_best_worst(self) -> None:
            """
            Calculates the ideal and anti-ideal matrices based on the impacts.

            Args:
                None

            Returns:
                None
            """
            self._ideal = self._calculte_matrix_extremum(self._impacts)
            self._anti_ideal = self._calculte_matrix_extremum(self._impacts * -1)

        def _calculate_euclidean_distance(self, matrix_1: np.ndarray, matrix_2: np.ndarray) -> float:
            """
            Calculates the Euclidean distance between two matrices.

            Args:
                matrix1 (np.ndarray): The first matrix.
                matrix2 (np.ndarray): The second matrix.

            Returns:
                float: The Euclidean distance between the two matrices.

            Raises:
                ValueError: If the two matrices have different shapes.
            """
            if matrix_1.shape != matrix_2.shape:
                raise ValueError("The two matrices must have the same shape")
            
            squared_diff = (matrix_1 - matrix_2) ** 2
            sum_squared_diff = np.sum(squared_diff)
            euclidean_distance = np.sqrt(sum_squared_diff)

            return euclidean_distance

        def _euclidean_distances(self) -> None:
            """
            Calculates the Euclidean distances of each alternative to the ideal and anti-ideal matrices.

            Args:
                None

            Returns:
                None
            """
            for i in range(self._num_alternative):
                ideal_distance = self._calculate_euclidean_distance(self._weighted_decision_matrix[i, :], self._ideal)
                anti_ideal_distance = self._calculate_euclidean_distance(self._weighted_decision_matrix[i, :], self._anti_ideal)
                self._distances[i, 0] = ideal_distance
                self._distances[i, 1] = anti_ideal_distance

        def _relative_closeness(self):
            """
            Calculates the relative closeness of each alternative based on the distances.

            The relative closeness is calculated as the ratio of the negative distance to the sum of the positive and negative distances.
            If the sum of the positive and negative distances is zero, the relative closeness is set to zero.

            Args:
                None

            Returns:
                None
            """
            for i in range(self._num_alternative):
                positive_distance = self._distances[i, 0]
                negative_distance = self._distances[i, 1]
                if positive_distance + negative_distance == 0:
                    self._closeness[i] = 0
                else:
                    self._closeness[i] = negative_distance / (positive_distance + negative_distance)

        def topsis(self) -> None:
            """
            Performs the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) analysis.

            This method executes the following steps:
            1. Weight the decision matrix.
            2. Compute the ideal and anti-ideal matrices.
            3. Calculate the Euclidean distances of each alternative to the ideal and anti-ideal matrices.
            4. Calculate the relative closeness of each alternative.

            Args:
                None

            Returns:
                None
            """
            # Weight the matrix
            self._weighted_matrix()

            # Compute the extremum matrises
            self._ideal_best_worst()

            # Compute Euclidean distances
            self._euclidean_distances()

            # Compute relative closeness
            self._relative_closeness()

        def get_closeness(self) -> np.ndarray:
            """
            Returns the array of relative closeness values for each alternative.

            The relative closeness values represent the degree of preference for each alternative based on the TOPSIS analysis.

            Args:
                None

            Returns:
                np.ndarray: The array of relative closeness values.
            """
            return self._closeness
        
        def get_ranking(self) -> np.ndarray:
            """
            Returns the ranking of alternatives based on their relative closeness values.

            The ranking is determined by sorting the relative closeness values in descending order and assigning ranks to the alternatives accordingly.

            Args:
                None

            Returns:
                np.ndarray: The array representing the ranking of alternatives.
            """
            ranking = np.argsort(self._closeness)[::-1] + 1
            return ranking
        
        def get_coef_from_label(self, label: str) -> None:
            return self._closeness[self.matrix_builder.alternatives_dict[label]]
