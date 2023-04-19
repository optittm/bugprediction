from sqlalchemy.orm import Query

from metrics.metric_common import MetricCommon
from models.metric import Metric
from models.version import Version

class MetricPython(MetricCommon):

    def __init__(self, session, config):
        super(MetricPython, self).__init__(session, config)

        self.radon_metrics_query = self._get_radon_metrics_query().subquery()
        self.pylint_metrics_query = self._get_pylint_metrics_query().subquery()
        self.query = self.session.query(
            # Selects all columns of subqueries except version_id
            # version_id is needed to perform the join statements but we remove it from final output
            *[c for c in self.version_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.lizard_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.halstead_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.radon_metrics_query.c if c.name != 'version_id'],
            *[c for c in self.pylint_metrics_query.c if c.name != 'version_id']
            # Then joining all tables on version_id starting on the version subquery
        ) \
            .select_from(self.version_metrics_query) \
            .join(self.lizard_metrics_query, Version.version_id == self.lizard_metrics_query.c.version_id) \
            .join(self.halstead_metrics_query, Version.version_id == self.halstead_metrics_query.c.version_id) \
            .join(self.radon_metrics_query, Version.version_id == self.radon_metrics_query.c.version_id) \
            .join(self.pylint_metrics_query, Version.version_id == self.pylint_metrics_query.c.version_id)

    def _get_radon_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.radon_cc_total, Metric.radon_cc_avg, Metric.radon_loc_total,
                                Metric.radon_loc_avg, Metric.radon_lloc_total, Metric.radon_lloc_avg,
                                Metric.radon_sloc_total, Metric.radon_sloc_avg, Metric.radon_comments_total,
                                Metric.radon_comments_avg, Metric.radon_docstring_total, Metric.radon_docstring_avg,
                                Metric.radon_blank_total, Metric.radon_blank_avg, Metric.radon_single_comments_total,
                                Metric.radon_single_comments_avg, Metric.radon_noc_total, Metric.radon_noc_avg,
                                Metric.radon_nom_total, Metric.radon_nom_avg, Metric.radon_nof_total,
                                Metric.radon_nof_avg, Metric.radon_class_loc_total, Metric.radon_class_loc_avg,
                                Metric.radon_method_loc_total, Metric.radon_method_loc_avg, Metric.radon_func_loc_total,
                                Metric.radon_func_loc_avg)
    
    def _get_pylint_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.pylint_cbo, Metric.pylint_fan_out, Metric.pylint_dit,
                                Metric.pylint_noc, Metric.pylint_nom, Metric.pylint_nof,
                                Metric.pylint_num_field, Metric.pylint_num_returns, Metric.pylint_num_loops,
                                Metric.pylint_num_comparisons, Metric.pylint_num_try_except, Metric.pylint_num_str_literals,
                                Metric.pylint_num_numbers, Metric.pylint_num_math_op, Metric.pylint_num_variable,
                                Metric.pylint_num_inner_cls_and_lambda, Metric.pylint_num_docstring, Metric.pylint_num_import,
                                Metric.pylint_lcc)