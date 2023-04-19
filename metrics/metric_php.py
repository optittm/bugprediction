from sqlalchemy.orm import Query

from metrics.metric_common import MetricCommon
from models.metric import Metric
from models.version import Version

class MetricPhp(MetricCommon):

    def __init__(self, session, config):
        super(MetricPhp, self).__init__(session, config)

        self.pdepend_metrics_query = self._get_pdepend_metrics_query().subquery()
        self.query = self.session.query(
            # Selects all columns of subqueries except version_id
            # version_id is needed to perform the join statements but we remove it from final output
            *[c for c in self.version_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.lizard_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.halstead_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.pdepend_metrics_query.c if c.name != 'version_id']
            # Then joining all tables on version_id starting on the version subquery
        ) \
            .select_from(self.version_metrics_query) \
            .join(self.lizard_metrics_query, Version.version_id == self.lizard_metrics_query.c.version_id) \
            .join(self.halstead_metrics_query, Version.version_id == self.halstead_metrics_query.c.version_id) \
            .join(self.pdepend_metrics_query, Version.version_id == self.pdepend_metrics_query.c.version_id)

    def _get_pdepend_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.pdepend_cbo, Metric.pdepend_fan_out, Metric.pdepend_dit, 
                                Metric.pdepend_nof, Metric.pdepend_noc, Metric.pdepend_nom, 
                                Metric.pdepend_nopm,Metric.pdepend_vars,Metric.pdepend_wmc, 
                                Metric.pdepend_calls, Metric.pdepend_nocc, Metric.pdepend_noom, 
                                Metric.pdepend_noi, Metric.pdepend_nop)