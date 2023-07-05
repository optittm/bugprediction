import datetime
import os
import unittest
from unittest.mock import MagicMock

from github import Github

from connectors.github import GitHubConnector


class TestGitHubConnector(unittest.TestCase):
    def setUp(self):
        self.project_id = 123
        self.directory = "test_directory"
        self.token = os.environ.get('OTTM_SCM_TOKEN')
        self.repo = "cqfn/jpeek"
        self.current = "master"
        self.session = MagicMock()
        self.config = MagicMock()
        self.connector = GitHubConnector(
            self.project_id,
            self.directory,
            self.token,
            self.repo,
            self.current,
            self.session,
            self.config,
        )

        # Simulation de l'objet GitHub API
        self.connector.api = MagicMock(spec=Github)

        # Simulation du dépôt distant (remote repository)
        self.connector.remote = MagicMock()

    def test__get_stars(self):
        # Simulation des étoiles (stargazers)
        stargazer1 = MagicMock()
        stargazer1.starred_at = datetime.datetime(2023, 1, 1)
        stargazer2 = MagicMock()
        stargazer2.starred_at = datetime.datetime(2023, 1, 2)
        stargazer3 = MagicMock()
        stargazer3.starred_at = datetime.datetime(2023, 1, 3)

        # Configuration de la valeur de retour simulée de get_stargazers_with_dates()
        self.connector.remote.get_stargazers_with_dates.return_value = [
            stargazer1,
            stargazer2,
            stargazer3,
        ]

        # Appel de la méthode _get_stars
        stars = self.connector._get_stars(to=datetime.datetime(2023, 1, 3))

        # Vérification du nombre d'étoiles attendu
        self.assertEqual(stars, 3)

    def test__get_forks(self):
        # Simulation des forks
        fork1 = MagicMock()
        fork1.created_at = datetime.datetime(2023, 1, 1)
        fork2 = MagicMock()
        fork2.created_at = datetime.datetime(2023, 1, 2)
        fork3 = MagicMock()
        fork3.created_at = datetime.datetime(2023, 1, 3)

        # Configuration de la valeur de retour simulée de get_forks()
        self.connector.remote.get_forks.return_value = [fork1, fork2, fork3]

        # Appel de la méthode _get_forks
        forks = self.connector._get_forks(to=datetime.datetime(2023, 1, 2))

        # Vérification du nombre de forks attendu
        self.assertEqual(forks, 2)

    def test__get_subscribers(self):
        # Simulation des abonnés (subscribers)
        subscriber1 = MagicMock()
        subscriber1.created_at = datetime.datetime(2023, 1, 1)
        subscriber2 = MagicMock()
        subscriber2.created_at = datetime.datetime(2023, 1, 2)
        subscriber3 = MagicMock()
        subscriber3.created_at = datetime.datetime(2023, 1, 3)

        # Configuration de la valeur de retour simulée de get_subscribers()
        self.connector.remote.get_subscribers.return_value = [
            subscriber1,
            subscriber2,
            subscriber3,
        ]

        # Appel de la méthode _get_subscribers
        subscribers = self.connector._get_subscribers(to=datetime.datetime(2023, 1, 1))

        # Vérification du nombre d'abonnés attendu
        self.assertEqual(subscribers, 1)


if __name__ == "__main__":
    unittest.main()
