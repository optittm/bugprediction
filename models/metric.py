from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from models.database import Base
from models.version import Version

class Metric(Base):
    __tablename__ = "metric"
    metrics_id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey(Version.version_id), unique=True)

    # lizard metrics
    lizard_total_nloc = Column(Integer)
    lizard_avg_nloc = Column(Float)
    lizard_avg_token = Column(Float)
    lizard_fun_count = Column(Integer)
    lizard_fun_rt = Column(Float)
    lizard_nloc_rt = Column(Float)
    lizard_total_complexity = Column(Integer)
    lizard_avg_complexity = Column(Float)
    lizard_total_operands_count = Column(Integer)
    lizard_unique_operands_count = Column(Integer)
    lizard_total_operators_count = Column(Integer)
    lizard_unique_operators_count = Column(Integer)

    total_lines = Column(Integer)
    total_blank_lines = Column(Integer)
    total_comments = Column(Integer)
    comments_rt = Column(Float)

    # CK metrics
    ck_cbo = Column(Float)
    ck_cbo_modified = Column(Float)
    ck_fan_in = Column(Float)
    ck_fan_out = Column(Float)
    ck_dit = Column(Float)
    ck_noc = Column(Float)
    ck_nom = Column(Float)
    ck_nopm = Column(Float)
    ck_noprm = Column(Float)
    ck_num_fields = Column(Float)
    ck_num_methods = Column(Float)
    ck_num_visible_methods = Column(Float)
    ck_nosi = Column(Float)
    ck_rfc = Column(Float)
    ck_wmc = Column(Float)
    ck_loc = Column(Float)
    ck_lcom = Column(Float)
    ck_lcom_modified = Column(Float)
    ck_tcc = Column(Float)
    ck_lcc = Column(Float)
    ck_qty_returns = Column(Float)
    ck_qty_loops = Column(Float)
    ck_qty_comparisons = Column(Float)
    ck_qty_try_catch = Column(Float)
    ck_qty_parenth_exps = Column(Float)
    ck_qty_str_literals = Column(Float)
    ck_qty_numbers = Column(Float)
    ck_qty_math_operations = Column(Float)
    ck_qty_math_variables = Column(Float)
    ck_qty_nested_blocks = Column(Float)
    ck_qty_ano_inner_cls_and_lambda = Column(Float)
    ck_qty_unique_words = Column(Float)
    ck_numb_log_stmts = Column(Float)
    ck_has_javadoc = Column(Float)
    ck_modifiers = Column(Float)
    ck_usage_vars = Column(Float)
    ck_usage_fields = Column(Float)
    ck_method_invok = Column(Float)

    # JPeek metrics
    jp_camc = Column(Float)
    jp_lcom = Column(Float)
    jp_mmac = Column(Float)
    jp_nhd = Column(Float)
    jp_scom = Column(Float)

    # halstead metrics
    halstead_length = Column(Float)
    halstead_vocabulary = Column(Integer)
    halstead_volume = Column(Float)
    halstead_difficulty = Column(Float)
    halstead_effort = Column(Float)
    halstead_time = Column(Float)
    halstead_bugs = Column(Float)

    # legacy
    nb_legacy_files = Column(Integer)

    # PDepend metrics
    pdepend_cbo = Column(Float)
    pdepend_fan_out = Column(Float)
    pdepend_dit = Column(Float)
    pdepend_nof = Column(Float)
    pdepend_noc = Column(Float)
    pdepend_nom = Column(Float)
    pdepend_nopm = Column(Float)
    pdepend_vars = Column(Float)
    pdepend_wmc = Column(Float)
    pdepend_calls = Column(Float)
    pdepend_nocc = Column(Float)
    pdepend_noom = Column(Float)
    pdepend_noi = Column(Float)
    pdepend_nop = Column(Float)

    # radon
    radon_cc_total = Column(Float)
    radon_cc_avg = Column(Float)
    radon_loc_total = Column(Integer)
    radon_loc_avg = Column(Float)
    radon_lloc_total = Column(Integer)
    radon_lloc_avg = Column(Float)
    radon_sloc_total = Column(Integer)
    radon_sloc_avg = Column(Float)
    radon_comments_total = Column(Integer)
    radon_comments_avg = Column(Float)
    radon_docstring_total = Column(Integer)
    radon_docstring_avg = Column(Float)
    radon_blank_total = Column(Integer)
    radon_blank_avg = Column(Float)
    radon_single_comments_total = Column(Integer)
    radon_single_comments_avg = Column(Float)
    # radon calculated
    radon_noc_total = Column(Integer)
    radon_noc_avg = Column(Float)
    radon_nom_total = Column(Integer)
    radon_nom_avg = Column(Float)
    radon_nof_total = Column(Integer)
    radon_nof_avg = Column(Float)
    radon_class_loc_total = Column(Integer)
    radon_class_loc_avg = Column(Float)
    radon_method_loc_total = Column(Integer)
    radon_method_loc_avg = Column(Float)
    radon_func_loc_total = Column(Integer)
    radon_func_loc_avg = Column(Float)
    radon_wmc_total = Column(Integer)
    radon_wmc_avg = Column(Float)

    # pylint
    pylint_cbo = Column(Float)
    pylint_fan_out = Column(Float)
    pylint_dit = Column(Integer)
    pylint_noc = Column(Integer)
    pylint_nom = Column(Integer)
    pylint_nof = Column(Integer)
    pylint_num_field = Column(Integer)
    pylint_num_returns = Column(Integer)
    pylint_num_loops = Column(Integer)
    pylint_num_comparisons = Column(Integer)
    pylint_num_try_except = Column(Integer)
    pylint_num_str_literals = Column(Integer)
    pylint_num_numbers = Column(Integer)
    pylint_num_math_op = Column(Integer)
    pylint_num_variable = Column(Integer)
    pylint_num_inner_cls_and_lambda = Column(Integer)
    pylint_num_docstring = Column(Integer)
    pylint_num_import = Column(Integer)
    pylint_lcc = Column(Float)