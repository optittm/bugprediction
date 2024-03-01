from datetime import datetime
from distutils.version import Version
from sqlalchemy.orm import Session
import numpy as np
from sqlalchemy.ext.declarative import DeclarativeMeta

from configuration import Configuration
from models.project import Project
from models.metric import Metric
from models.legacy import Legacy
from models.file import File
from models.version import Version
from utils.timeit import timeit
from metrics.versions import assess_next_release_risk


class MetricsExporter:
    """
    Generate metrics

    Attributes
    ----------
        session : Session
            Sqlalchemy ORM session object
        configuration : Configuration
            Application configuration
    """

    def __init__(self, session:Session, configuration: Configuration, model):
        """
        MetricsExporter constructor

        Parameters
        ----------
        session : Session
            Sqlalchemy ORM session object
        directory : str
            Output path of the report
        """
        self.session = session
        self.configuration = configuration
        self.__model = model

    
    @timeit
    def generate_metrics_release(self, project:Project)->None:
        """
        Generate the metrics about the next release

        Parameters
        ----------
        project : Project
            Project object
        """

        excluded_versions = self.configuration.exclude_versions
        included_versions = self.configuration.include_versions

        releases = self.session.query(Version, Metric) \
                .join(Metric, Version.version_id == Metric.version_id) \
                .order_by(Version.end_date.desc()) \
                .filter(Version.project_id == project.project_id) \
                .filter(Version.name != self.configuration.next_version_name) \
                .filter(Version.include_filter(included_versions)) \
                .filter(Version.exclude_filter(excluded_versions)).all()

        current_release = self.session.query(Version, Metric) \
                .join(Metric, Version.version_id == Metric.version_id) \
                .order_by(Version.end_date.desc()) \
                .filter(Version.project_id == project.project_id) \
                .filter(Version.name == self.configuration.next_version_name).first()

        legacy_files = self.session.query(Legacy, File) \
                .join(File, Legacy.file_id == File.file_id) \
                .filter(Legacy.version_id == current_release.Version.version_id) \
                .all()

        bugs_median = np.median([row.Version.bugs for row in releases])
        changes_median = np.median([row.Version.changes for row in releases])
        xp_devs_median = np.median([row.Version.avg_team_xp for row in releases])
        lizard_avg_complexity_median = np.median([row.Metric.lizard_avg_complexity for row in releases])
        code_churn_avg_median = np.median([row.Version.code_churn_avg for row in releases])

        predicted_bugs = -1
        predicted_bugs = self.__model.predict()

        risk = assess_next_release_risk(self.session, self.configuration, project.project_id)

        legacy_files_path = [f[1].path for f in legacy_files]

        metrics = {
            "project": project.project_id,
            "model_name" : self.__model.name,
            "current_release_version" : self.encoder_class(current_release.Version),
            "current_release_metric" : self.encoder_class(current_release.Metric),
            "bugs_median" : bugs_median,
            "changes_median" : changes_median,
            "xp_devs_median" : xp_devs_median,
            "code_churn_avg_median" : code_churn_avg_median,
            "lizard_avg_complexity_median" : lizard_avg_complexity_median,
            "predicted_bugs" : predicted_bugs,
            "legacy_files": legacy_files_path,
            "risk": risk,
        }

        return metrics
    

    def encoder_class(self, obj):
        """
        Retrieve all attribut of a class

        Parameters
        ----------
        obj : Class Object
        """
        _visited_objs = []

        if isinstance(obj.__class__, DeclarativeMeta):

            if obj in _visited_objs:
                return None
            _visited_objs.append(obj)

            fields = {}
            for field in [x for x in obj.__dict__ if not x.startswith('_') and x != 'metadata']:
                if obj.__getattribute__(field) is not None:
                    fields[field] = obj.__getattribute__(field)
                    if isinstance(fields[field], datetime):
                        fields[field] = fields[field].isoformat()

            return fields
