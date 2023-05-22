from statistics import mean
import logging

import numpy as np

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

    @classmethod
    def normalize_matrix(cls, matrix):
        """
        Normalize all values of a given matrix using L2 norm.

        Args:
            matrix (np.ndarray): The input matrix.

        Returns:
            np.ndarray: The normalized matrix.

        """
        norms = np.linalg.norm(matrix)
        if norms == 0:
            return matrix
        normalized_matrix = matrix / norms
        return normalized_matrix

    @classmethod
    def calculate_correlation_matrix(cls, criteria: np.ndarray, alternative: np.ndarray, criteria_labels: list, alternative_labels: list) -> tuple:
        """
        Calculates the correlation matrix between criteria and alternative arrays.

        Args:
            criteria (list): List of criteria arrays.
            alternative (list): List of alternative arrays.
            criteria_labels (list): List of labels for criteria arrays.
            alternative_labels (list): List of labels for alternative arrays.

        Returns:
            tuple: A tuple containing the correlation matrix, criteria dictionary, and alternative dictionary.
                - The correlation matrix is a numpy array representing the correlation between each criteria and alternative.
                - The criteria dictionary is a dictionary mapping criteria labels to their corresponding row indices in the correlation matrix.
                - The alternative dictionary is a dictionary mapping alternative labels to their corresponding column indices in the correlation matrix.
        
        Raises:
            ValueError: If the number of labels does not match the size of the matrices.
        """
        if len(criteria_labels) != len(criteria) or len(alternative_labels) != len(alternative):
            raise ValueError("Number of labels does not match the size of the matrices.")
        
        correlation_matrix = np.zeros((len(criteria), len(alternative)))

        criteria_dict = {label: index for index, label in enumerate(criteria_labels)}
        alternative_dict = {label: index for index, label in enumerate(alternative_labels)}

        for i in range(len(criteria)):
            if np.var(criteria[i]) != 0:
                for j in range(len(alternative)):
                    if np.var(alternative[j]) != 0:
                        correlation_matrix[i, j] = np.corrcoef(criteria[i], alternative[j])[0, 1]

        return correlation_matrix, criteria_dict, alternative_dict
    
    @classmethod
    def apply_criteria_weights(cls, correlation_matrix: np.ndarray, criteria_dict: dict, criteria_weight: dict) -> np.ndarray:
        """
        Applies criteria weights to the correlation matrix.

        Args:
            correlation_matrix (np.ndarray): The correlation matrix.
            criteria_dict (dict): Dictionary mapping criteria labels to their corresponding row indices in the correlation matrix.
            alternative_dict (dict): Dictionary mapping alternative labels to their corresponding column indices in the correlation matrix.
            criteria_weight (dict): Dictionary of criteria weights.

        Returns:
            np.ndarray: The weighted correlation matrix.
            
        Raises:
            KeyError: If a criteria weight does not exist in the criteria dictionary.
        """
        weighted_correlation_matrix = correlation_matrix.copy()

        for criteria, weight in criteria_weight.items():
            if criteria in criteria_dict:
                criteria_index = criteria_dict[criteria]
                weighted_correlation_matrix[criteria_index, :] *= weight
            else:
                raise KeyError(f"Criteria '{criteria}' does not exist in the criteria dictionary.")

        return weighted_correlation_matrix
    
    @classmethod
    def calculte_matrix_extremum(cls, weighted_matrix: np.ndarray, criteria_dict: dict, alternative_dict: dict, min_fields: list = []) -> np.ndarray:
        """
        Calculates the matrix extremum (ideal or anti-ideal) based on the weighted matrix, criteria dictionary, and alternative dictionary.

        Args:
            weighted_matrix (np.ndarray): The weighted matrix.
            criteria_dict (dict): Dictionary mapping criteria labels to their corresponding row indices in the weighted matrix.
            alternative_dict (dict): Dictionary mapping alternative labels to their corresponding column indices in the weighted matrix.
            min_fields (list, optional): List of fields that should be minimized. Defaults to [].

        Returns:
            np.ndarray: The matrix extremum (ideal or anti-ideal).

        Raises:
            ValueError: If the criteria or alternative dictionary is empty.
            ValueError: If a field in min_fields does not exist in the criteria dictionary.
        """
        if not criteria_dict or not alternative_dict:
            raise ValueError("Criteria or alternative dictionary is empty.")

        invalid_fields = set(min_fields) - set(criteria_dict.keys())
        if invalid_fields:
            raise ValueError(f"Invalid fields specified: {', '.join(invalid_fields)}")

        num_criteria = len(criteria_dict)
        num_alternatives = len(alternative_dict)

        extremum_matrix = np.zeros((num_criteria, num_alternatives))

        for criteria_label, criteria_index in criteria_dict.items():
            criteria_weights = weighted_matrix[criteria_index, :]
            if criteria_label in min_fields:
                extremum_value = np.min(criteria_weights)
            else:
                extremum_value = np.max(criteria_weights)
            extremum_matrix[criteria_index, :] = extremum_value

        return extremum_matrix
    
    @classmethod
    def calculate_euclidean_distance(cls, matrix_1: np.ndarray, matrix_2: np.ndarray) -> float:
        """
        Calculate the Euclidean distance between two matrices.

        Args:
            matrix1 (np.ndarray): The first matrix.
            matrix2 (np.ndarray): The second matrix.

        Returns:
            float: The Euclidean distance between the two matrices.

        Raises:
            ValueError: If the two matrices have different shapes.

        """
        if matrix_1.shape != matrix_2.shape:
            raise ValueError("The two matrices must have the same shape.")
    
        squared_diff = (matrix_1 - matrix_2) ** 2
        sum_squared_diff = np.sum(squared_diff)
        euclidean_distance = np.sqrt(sum_squared_diff)

        return euclidean_distance
    