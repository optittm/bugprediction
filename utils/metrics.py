import logging
import sys

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject

from models.metric import Metric
from models.version import Version
from utils.container import Container


class MetricFactory:
    
    @staticmethod
    @inject
    def predict_bugs_language(project_id,
                              session = Provide[Container.session],
                              config = Provide[Container.configuration]):
        
        language = config.language

        version_metrics_query = session.query(Version.avg_team_xp, Version.bug_velocity, Version.bugs)
        lizard_metrics_query = session.query(Metric.lizard_total_nloc, Metric.lizard_avg_nloc, Metric.lizard_avg_token,
                                    Metric.lizard_fun_count, Metric.lizard_fun_rt, Metric.lizard_nloc_rt,
                                    Metric.lizard_total_complexity, Metric.lizard_avg_complexity,
                                    Metric.lizard_total_operands_count, Metric.lizard_unique_operands_count,
                                    Metric.lizard_total_operators_count, Metric.lizard_unique_operators_count,
                                    Metric.comments_rt, Metric.total_lines, Metric.total_blank_lines,
                                    Metric.total_comments)
        ck_metrics_query = session.query(Metric.ck_cbo, Metric.ck_cbo_modified, Metric.ck_fan_in,
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
        halstead_metrics_query = session.query(Metric.halstead_length,Metric.halstead_vocabulary, Metric.halstead_volume, 
                                    Metric.halstead_difficulty,Metric.halstead_effort, Metric.halstead_time, 
                                    Metric.halstead_bugs)
        pdepend_metrics_query = session.query(Metric.pdepend_cbo, Metric.pdepend_fan_out, Metric.pdepend_dit, 
                                    Metric.pdepend_nof, Metric.pdepend_noc, Metric.pdepend_nom, 
                                    Metric.pdepend_nopm,Metric.pdepend_vars,Metric.pdepend_wmc, 
                                    Metric.pdepend_calls, Metric.pdepend_nocc, Metric.pdepend_noom, 
                                    Metric.pdepend_noi, Metric.pdepend_nop)
        radon_metrics_query = session.query(Metric.radon_cc_total, Metric.radon_cc_avg, Metric.radon_loc_total,
                                    Metric.radon_loc_avg, Metric.radon_lloc_total, Metric.radon_lloc_avg,
                                    Metric.radon_sloc_total, Metric.radon_sloc_avg, Metric.radon_comments_total,
                                    Metric.radon_comments_avg, Metric.radon_docstring_total, Metric.radon_docstring_avg,
                                    Metric.radon_blank_total, Metric.radon_blank_avg, Metric.radon_single_comments_total,
                                    Metric.radon_single_comments_avg, Metric.radon_noc_total, Metric.radon_noc_avg,
                                    Metric.radon_nom_total, Metric.radon_nom_avg, Metric.radon_nof_total,
                                    Metric.radon_nof_avg, Metric.radon_class_loc_total, Metric.radon_class_loc_avg,
                                    Metric.radon_method_loc_total, Metric.radon_method_loc_avg, Metric.radon_func_loc_total,
                                    Metric.radon_func_loc_avg)

        if str(language).lower() == "java":
            logging.info('Language Java')
            return session.query(version_metrics_query.subquery(), 
                                 lizard_metrics_query.subquery(), 
                                 ck_metrics_query.subquery(), 
                                 halstead_metrics_query.subquery()). \
            order_by(Version.end_date.desc()). \
            filter(Version.project_id == project_id). \
            filter(Version.include_filter(config.include_versions)). \
            filter(Version.exclude_filter(config.exclude_versions)). \
            filter(Metric.version_id == Version.version_id). \
            filter(Version.name != config.next_version_name)

        elif str(language).lower() == "php":
            logging.info('Language PHP')
            return session.query(lizard_metrics_query.subquery(), 
                                 pdepend_metrics_query.subquery()). \
                order_by(Version.end_date.desc()). \
                filter(Version.project_id == project_id). \
                filter(Version.include_filter(config.include_versions)). \
                filter(Version.exclude_filter(config.exclude_versions)). \
                filter(Metric.version_id == Version.version_id). \
                filter(Version.name != config.next_version_name)

        elif str(language).lower() == "python":
            logging.info('Language Python')
            return session.query(lizard_metrics_query.subquery(),
                                 radon_metrics_query.subquery()). \
                order_by(Version.end_date.desc()). \
                filter(Version.project_id == project_id). \
                filter(Version.include_filter(config.include_versions)). \
                filter(Version.exclude_filter(config.exclude_versions)). \
                filter(Metric.version_id == Version.version_id). \
                filter(Version.name != config.next_version_name)

        else:
            logging.error("Unsupported Language: {language}")
            sys.exi("Unsupported Language")
