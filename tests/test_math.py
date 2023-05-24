


import unittest

import numpy as np
from utils.math import Math


class TestTOPSIS(unittest.TestCase):
    def setUp(self):
        self.decision_matrix = np.array([[3.0, 4.0, 5.0],
                                         [2.0, 5.0, 1.0],
                                         [4.0, 2.0, 3.0],
                                         [1.0, 3.0, 2.0]])
        self.weights = np.array([0.5, 0.3, 0.2])
        self.impacts = np.array([Math.TOPSIS.MAX, Math.TOPSIS.MAX, Math.TOPSIS.MIN])
        self.topsis = Math.TOPSIS(self.decision_matrix, self.weights, self.impacts)
        self.topsis.topsis()

    def test_weighted_matrix(self):
        weighted_matrix = np.array([[1.5, 1.2, 1.0],
                                    [1.0, 1.5, 0.2],
                                    [2.0, 0.6, 0.6],
                                    [0.5, 0.9, 0.4]])
        np.testing.assert_allclose(self.topsis._weighted_decision_matrix, weighted_matrix)

    def test_ideal_best_worst(self):
        ideal_solution = np.array([2.0, 1.5, 0.2])
        anti_ideal_solution = np.array([0.5, 0.6, 1.0])
        np.testing.assert_array_equal(self.topsis._ideal, ideal_solution)
        np.testing.assert_array_equal(self.topsis._anti_ideal, anti_ideal_solution)

    
    def test_euclidean_distances(self):
        distances = np.array([[0.989949, 1.16619],
                              [1.0, 1.30384],
                              [0.984886, 1.552417],
                              [1.627882, 0.67082]])
        np.testing.assert_allclose(self.topsis._distances, distances, atol=1e-3)

    def test_relative_closeness(self):
        closeness = np.array([0.54087, 0.565942, 0.611838, 0.291826])
        np.testing.assert_allclose(self.topsis._closeness, closeness, atol=1e-3)

    def test_get_closeness(self):
        closeness = np.array([0.54087, 0.565942, 0.611838, 0.291826])
        np.testing.assert_allclose(self.topsis.get_closeness(), closeness, atol=1e-3)

    def test_get_ranking(self):
        ranking = np.array([3, 2, 1, 4])
        np.testing.assert_array_equal(self.topsis.get_ranking(), ranking)