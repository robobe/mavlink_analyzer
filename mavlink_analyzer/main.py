from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Button, Footer, Header, Static, Tree
from mav_logger import MavAnalyzer

class TimeDisplay(Static):
    """A widget to display elapsed time."""

class MavDisplay(Static):
    """A stopwatch widget."""

    def compose(self) -> ComposeResult:
        yield Tree("Root")

   

class Analyzer(App):
    """A Textual app to manage stopwatches."""
    CSS_PATH = "app_style.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(MavDisplay())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def render_tree(self, data):
        tree = self.query_one(Tree)
        tree.clear()
        for msg_id, meta in data.items():
            tree.root.add_leaf(f"{msg_id} ({meta.counter})")

        tree.root.expand()

if __name__ == "__main__":
    app = Analyzer()
    mav = MavAnalyzer()
    mav.on_data += app.render_tree
    mav.run()
    app.run()