from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Button, Footer, Header, Static, Tree
from mav_logger import MavAnalyzer
from queue import Queue
from threading import Thread, Event
import signal
import sys
import time
import logging
from typing import (
    Coroutine,
    Dict
)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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

    def __init__(self):
        super().__init__()
        self.__stop = False
        self.queue = Queue()
        self.work_event = Event()
        self.run_work_thread()

    def _on_exit_app(self):
        self.stop()
        return super()._on_exit_app()
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(MavDisplay())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def run_work_thread(self):
        self.work_thread = Thread(target=self.render_tree, daemon=True, name="work_thread")
        self.work_thread.start()

    def stop(self):
        self.__stop = True
        log.info("------ try to stop TUI loop")
        self.work_event.set()

    def render_tree(self):
        
        while True:
            try:
                self.work_event.wait()
                if self.__stop:
                    log.info("Stopping render loop")
                    break
                data = self.queue.get()
                tree = self.query_one(Tree)    
                tree.clear()
                
                self.buile_tree(tree, data)

                tree.root.expand()
            except:
                log.error("Render failed", exc_info=True)

    def buile_tree(self, tree: Tree, data: Dict):
        title=""
        msgs = None
        for sys_id, comps in data.items():
            msgs = {}
            if len(data[sys_id]) == 1:
                comp_id = list(comps.keys())[0]
                title = f"{sys_id} ({comp_id})"
                msgs = data[sys_id][comp_id]
                node = tree.root.add(title, expand=True)
                # print(title + "\n")
                for msg_id, counter in msgs.items():
                    node.add_leaf(f"{msg_id} ({counter} Hz)")
                    # print(f"{msg_id} ({counter} Hz)\n")
            else:
                # print(f"{sys_id}\n")
                node = tree.root.add(str(sys_id), expand=True)
                for comp_id, msgs in data[sys_id].items():
                    comp_node = node.add(str(comp_id), expand=True)
                    for msg_id, counter in msgs.items():
                        comp_node.add_leaf(f"{msg_id} ({counter} Hz)")
                        # print(f"{msg_id} ({counter} Hz)\n")

    def put(self, data):
        self.queue.put(data)
        self.work_event.set()
        self.work_event.clear()

def signal_handler(signal, frame):
    mav.stop()
    
    log.info("-------------Program terminated----------------")
    app.exit(return_code=0)

if __name__ == "__main__":
    # app = Analyzer()
    # tree = {
    #     1: {
    #         1: {
    #             'HB': 5,
    #             "ALERT": 1
    #         }
    #     },
    #     255: {
    #         1: {
    #             "HBB": 2
    #         },
    #         195: {
    #             "HBX": 3
    #         }
    #     }
    # }
    # app.buile_tree(tree)
    signal.signal(signal.SIGINT, signal_handler)
    app = Analyzer()
    mav = MavAnalyzer()
    mav.on_data += app.put
    mav.run()
    
    app.run()