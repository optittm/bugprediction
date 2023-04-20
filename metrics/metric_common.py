import logging
from sqlalchemy.orm import Query
import pandas as pd
from pandas import DataFrame

from models.version import Version
from models.metric import Metric

class MetricCommon():

    metrics_df: DataFrame

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def _order_by_filters(
            self,
            select_query: Query,
            project_id,
            order_version_date = "asc",
            state = "train") -> Query:
        """
        Adds the order by and filter statements used for the metrics to the initial select query

        Args:
            - select_query (sqlalchemy.orm.Query): The initial select query to which to add the filters and order by
            - project_id: The project id
            - order_version_date: "asc" or "desc" to order by the version's end date
            - state: "train" or "predict" to choose which versions are filtered
        
        Returns:
            The Query object with filters and order by
        """

        if order_version_date not in ["asc", "desc"]:
            logging.error("MetricFactory::order_version_date can only be 'asc' or 'desc'")
            raise Exception("order_version_date can only be 'asc' or 'desc'")
        if state not in ["train", "predict"]:
            logging.error("MetricFactory::state can only be 'train' or 'predict'")
            raise Exception("state can only be 'train' or 'predict'")

        query = select_query \
            .order_by(Version.end_date.asc() if order_version_date == "asc" else Version.end_date.desc()) \
            .filter(Version.project_id == project_id) \
            .filter(Metric.version_id == Version.version_id)
        
        if state == "train":
            query = query \
                .filter(Version.include_filter(self.config.include_versions)) \
                .filter(Version.exclude_filter(self.config.exclude_versions)) \
                .filter(Version.name != self.config.next_version_name)
        elif state == "predict":
            query = query.filter(Version.name == self.config.next_version_name)

        return query

    def _get_version_metrics_query(self) -> Query:
        return self.session.query(Version.version_id, Version.avg_team_xp, Version.bug_velocity, Version.bugs)
    
    def _get_lizard_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.lizard_total_nloc, Metric.lizard_avg_nloc, Metric.lizard_avg_token,
                                Metric.lizard_fun_count, Metric.lizard_fun_rt, Metric.lizard_nloc_rt,
                                Metric.lizard_total_complexity, Metric.lizard_avg_complexity,
                                Metric.lizard_total_operands_count, Metric.lizard_unique_operands_count,
                                Metric.lizard_total_operators_count, Metric.lizard_unique_operators_count,
                                Metric.comments_rt, Metric.total_lines, Metric.total_blank_lines,
                                Metric.total_comments)
    
    def _get_halstead_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.halstead_length,Metric.halstead_vocabulary, Metric.halstead_volume, 
                                Metric.halstead_difficulty,Metric.halstead_effort, Metric.halstead_time, 
                                Metric.halstead_bugs)
    
    def _get_language_specific_query(self) -> Query:
        version_metrics_query = self._get_version_metrics_query().subquery()
        lizard_metrics_query = self._get_lizard_metrics_query().subquery()
        halstead_metrics_query = self._get_halstead_metrics_query().subquery()
        return self.session.query(
                # Selects all columns of subqueries except version_id
                # version_id is needed to perform the join statements but we remove it from final output
                *[c for c in version_metrics_query.c if c.name != 'version_id'],
                *[c for c in lizard_metrics_query.c if c.name != 'version_id'],
                *[c for c in halstead_metrics_query.c if c.name != 'version_id']
                # Then joining all tables on version_id starting on the version subquery
            ) \
                .select_from(version_metrics_query) \
                .join(lizard_metrics_query, Version.version_id == lizard_metrics_query.c.version_id) \
                .join(halstead_metrics_query, Version.version_id == halstead_metrics_query.c.version_id)
    
    def get_train_metrics(self, project_id) -> 'MetricCommon':
        select_query = self._get_language_specific_query()
        query = self._order_by_filters(select_query, project_id, "desc", "train")
        self.metrics_df = pd.read_sql(query.statement, self.session.get_bind())
        return self

    def get_predict_metrics(self, project_id) -> 'MetricCommon':
        select_query = self._get_language_specific_query()
        query = self._order_by_filters(select_query, project_id, "asc", "predict")
        self.metrics_df = pd.read_sql(query.statement, self.session.get_bind())
        return self