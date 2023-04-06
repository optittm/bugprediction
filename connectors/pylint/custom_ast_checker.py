import astroid
from astroid.exceptions import InferenceError
from pylint.checkers import BaseChecker
from connectors.pylint.custom_linter import CustomLinter
from utils.math import Math

class CustomAstChecker(BaseChecker):
    # These properties have to be defined for the 
    # or the linter fink is a malformed checker
    name = 'class-visitor'
    priority = -1
    msgs = {'R0001': ('Custom checker.', 'Visited', 'CustomAstChecker class.')}

    import_list = set()
    method_data = {}
    class_depedency = {}
    class_method_rfc = {}
    class_method_defs = {}
    class_method_calls = {}
    
    def __init__(self, linter: "CustomLinter" = None) -> None:
        super().__init__(linter)
        self.data = linter.metrics
    
    # Methode call on class def visit
    def visit_classdef(self, node : astroid.ClassDef) -> None:
        self.count_docstring(node)

        self.data.noc += 1

        # count number of inner class
        for inner_node in node.body:
            if isinstance(inner_node, astroid.ClassDef):
                self.data.num_inner_cls_and_lambda += 1
        
        # count number of field
        for child_node in node.get_children():
            # is child field if is form of "var_name = x" or "var_name : type = x"
            if isinstance(child_node, astroid.nodes.Assign) or isinstance(child_node, astroid.nodes.AnnAssign):
                self.data.num_field += 1

        # Compute the DIT
        dit = self.__compute_class_dit(node)
        if (self.data.dit < dit):
            self.data.dit = dit

        # Prepare the cbo
        self.class_depedency[node.name] = set()
        # Increase the cbo with the inerit class
        if len(node.bases):
            # the direct inerit class
            bases_klass_nodes = [next(nodes.infer()) for nodes in node.bases]
            for klass in bases_klass_nodes:
                self.class_depedency[node.name].add(klass.name)

        # Compute data for lcc
        self.class_method_defs[node.name] = set()
        for method in node.methods():
            method_name = node.name + "." + method.name
            self.class_method_defs[node.name].add(method_name)
        if node.name not in self.class_method_calls:
            self.class_method_calls[node.name] = set()

    # Methode call on function def visit
    def visit_functiondef(self, node: astroid.FunctionDef) -> None:
        self.count_docstring(node)
        # is methode
        if node.is_method():
            self.visit_methoddef(node)
        # is function
        else:
            self.data.nof += 1

    def visit_methoddef(self, node: astroid) -> None:
        self.data.nom += 1
        
        # Prepare data for fan out
        method_name = node.parent.name + "." + node.name
        if not (method_name in self.method_data):
            self.method_data[method_name] = {"fan_out": 0}

    def visit_import(self, node: astroid) -> None:
        self.import_list.add(node.names[0][0])

    def visit_importfrom(self, node: astroid) -> None:
        self.import_list.add(node.names[0][0])

    def visit_excepthandler(self, node: astroid) -> None:
        self.data.num_try_except += 1
        
    def visit_return(self, node: astroid) -> None:
        self.data.num_returns += 1

    def visit_for(self, node: astroid) -> None:
        self.data.num_loops += 1

    def visit_while(self, node: astroid) -> None:
        self.data.num_loops += 1

    def visit_compare(self, node: astroid) -> None:
        self.data.num_comparisons += 1

    def visit_binop(self, node: astroid) -> None:
        self.data.num_math_op += 1

    def visit_assign(self, node: astroid) -> None:
        self.data.num_variable += 1

    def visit_lambda(self, node: astroid) -> None:
        self.data.num_inner_cls_and_lambda += 1

    def visit_const(self, node: astroid) -> None:
        if node.pytype() == "builtins.bool":
            pass
        elif node.pytype() == "builtins.str":
            self.data.num_str_literals += 1
        elif node.pytype() == "builtins.NoneType":
            pass
        else:
            self.data.num_numbers += 1

    # method call on function call visit
    def visit_call(self, node: astroid) -> None:
        # retrive the context
        context = node.frame()
        # check if the context is in the method
        if isinstance(context, astroid.FunctionDef) and context.is_method():
            # Retrive the class of the context method
            context_class = context.parent
            context_name = f"{context_class.name}.{context.name}"

            # compute the fan out
            # check if we can store the data or create it
            if context_name not in self.method_data:
                self.method_data[context_name] = {"fan_out": 0}
            self.method_data[context_name]["fan_out"] += 1

        # Get data for lcc
        if isinstance(node.func, astroid.Attribute):
            try:
                called_method_class = next(node.func.expr.infer())
                if called_method_class.name not in self.class_method_calls:
                    self.class_method_calls[called_method_class.name] = set()
                self.class_method_calls[called_method_class.name].add(node.func.attrname)
            except InferenceError:
                pass

    # methode call on module visit
    def visit_module(self, node) -> None:
        self.count_docstring(node)
    
    # methode call when the visit is complete
    def close(self) -> None:
        lcc_values = {}
        self.data.num_import = len(self.import_list)
        self.data.fan_out = Math.get_rounded_mean_safe([method["fan_out"] for method in self.method_data.values()])
        self.data.cbo = Math.get_rounded_mean_safe([len(v) for v in self.class_depedency.values()])
        for class_name in self.class_method_defs:
            called_methods = self.class_method_calls[class_name]
            defined_methods = self.class_method_defs[class_name]
            if len(defined_methods) == 0:
                lcc_values[class_name] = 0.0
            else:
                lcc_values[class_name] = 1.0 - (len(called_methods) / len(defined_methods))
        self.data.lcc = Math.get_rounded_mean_safe(lcc_values.values())

    def count_docstring(self, node: astroid) -> None:
        if (node.doc):
            self.data.num_docstring += 1

    # Compute the DIT for a simple class
    def __compute_class_dit(self, node: astroid):
        local_dit = 1
        # if this class is a leaf return 1
        if len(node.bases) < 0:
            return 1
        # else compute de dit for each inerit class
        # converte Name nodes to ClassDef nodes
        # We need to interprete the bases names to get the class
        bases_klass_nodes = [next(nodes.infer()) for nodes in node.bases]
        # This condition is for the case "class A(None)"
        if isinstance(bases_klass_nodes, astroid.ClassDef):
            for klass in bases_klass_nodes:
                klass_dit = self.__compute_class_dit(klass)
                # The DIT of the class is the max DIT of each inerit class
                # The class DIT is the inerit class dit + 1
                if klass_dit + 1 > local_dit :
                    local_dit = klass_dit + 1
        
        return local_dit
