
from pylint.reporters import BaseReporter
from pylint.message import Message
from pylint.reporters.ureports.nodes import Section
from pylint.utils import LinterStats

class CustomReporter(BaseReporter):

    def handle_message(self, msg: Message) -> None:
        """Do Nothing"""

    def _display(self, layout: Section) -> None:
        """Do Nothing"""

    def display_reports(self, layout: Section) -> None:
        """Do nothing"""

    def display_messages(self, layout: Section | None) -> None:
        """Do nothing"""
    
    def on_close(self, stats: LinterStats, previous_stats: LinterStats | None) -> None:
        """Do Nothing"""
        
    