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