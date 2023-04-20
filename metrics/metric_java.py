from sqlalchemy.orm import Query

from metrics.metric_common import MetricCommon
from models.metric import Metric
from models.version import Version

class MetricJava(MetricCommon):

    def _get_ck_metrics_query(self) -> Query:
        return self.session.query(Metric.version_id, Metric.ck_cbo, Metric.ck_cbo_modified, Metric.ck_fan_in,
                                Metric.ck_fan_out, Metric.ck_dit, Metric.ck_noc, Metric.ck_nom, Metric.ck_nopm,
                                Metric.ck_noprm, Metric.ck_num_fields, Metric.ck_num_methods,
                                Metric.ck_num_visible_methods, Metric.ck_nosi, Metric.ck_rfc, Metric.ck_wmc,
                                Metric.ck_loc, Metric.ck_lcom, Metric.ck_qty_loops, Metric.ck_qty_comparisons,
                                Metric.ck_qty_returns, Metric.ck_qty_try_catch, Metric.ck_qty_parenth_exps,
                                Metric.ck_qty_str_literals, Metric.ck_qty_numbers, Metric.ck_qty_math_operations,
                                Metric.ck_qty_math_variables, Metric.ck_qty_nested_blocks,
                                Metric.ck_qty_ano_inner_cls_and_lambda, Metric.ck_qty_unique_words, Metric.ck_numb_log_stmts,
                                Metric.ck_has_javadoc, Metric.ck_modifiers, Metric.ck_usage_vars,
                                Metric.ck_usage_fields, Metric.ck_method_invok)
    
    def _get_language_specific_query(self) -> Query:
        version_metrics_query = self._get_version_metrics_query().subquery()
        lizard_metrics_query = self._get_lizard_metrics_query().subquery()
        halstead_metrics_query = self._get_halstead_metrics_query().subquery()
        ck_metrics_query = self._get_ck_metrics_query().subquery()
        return self.session.query(
            # Selects all columns of subqueries except version_id
            # version_id is needed to perform the join statements but we remove it from final output
            *[c for c in version_metrics_query.c if c.name != 'version_id'],
            *[c for c in lizard_metrics_query.c if c.name != 'version_id'],
            *[c for c in halstead_metrics_query.c if c.name != 'version_id'],
            *[c for c in ck_metrics_query.c if c.name != 'version_id']
            # Then joining all tables on version_id starting on the version subquery
        ) \
            .select_from(version_metrics_query) \
            .join(lizard_metrics_query, Version.version_id == lizard_metrics_query.c.version_id) \
            .join(halstead_metrics_query, Version.version_id == halstead_metrics_query.c.version_id) \
            .join(ck_metrics_query, Version.version_id == ck_metrics_query.c.version_id)