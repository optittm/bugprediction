from pylint.lint import PyLinter

from connectors.pylint.cheacker_metrics_model import CheckerData

class CustomLinter(PyLinter):
    def __init__(self, reporter):
        super().__init__(reporter=reporter)
        self.metrics = CheckerData()