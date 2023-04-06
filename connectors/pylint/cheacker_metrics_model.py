

class CheckerData:
    cbo : float = 0
    # fan_in : float = 0
    fan_out : float = 0
    dit : float = 0
    noc : int = 0
    nom : int = 0
    nof : int = 0
    num_field : int = 0
    num_returns : int = 0
    num_loops : int = 0
    num_comparisons : int = 0
    num_try_except : int = 0
    # num_parenth_exps : int = 0
    num_str_literals : int = 0
    num_numbers : int = 0
    num_math_op : int = 0
    num_variable : int = 0
    # num_nested_blocks : int = 0
    num_inner_cls_and_lambda : int = 0
    # num_unique_words : int = 0
    # num_log_stmts : int = 0
    num_docstring : int = 0
    num_module : int = 0
    num_import : int = 0
    # nosi : int = 0
    # rfc : float = 0
    # wmc : float = 0 # can be computed by radon
    lcc : float = 0
    # lcom : int = 0

    def __str__(self):
        attributes = []
        for name in dir(self):
            if not name.startswith("__"):
                value = getattr(self, name)
                if not callable(value):
                    attributes.append(f"{name}={value}")
        return f"{self.__class__.__name__}({', '.join(attributes)})"   