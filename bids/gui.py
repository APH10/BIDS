# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from textual.app import App
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Button, DirectoryTree, Footer, Header, Static

from bids.ui.analysis import AnalyseScreen
from bids.ui.query import QueryScreen
from bids.ui.sbom import SbomScreen


class MainScreen(Screen):
    selected_path: var[Path | None] = var(None)

    def compose(self):
        yield Header(id="head_panel", name="BIDS - Binary Analysis")
        with Container():
            yield DirectoryTree("/", id="tree-view")
            with VerticalScroll(id="actions-pane"):
                yield Static("Selected: None", id="selected-label")
                yield Button("Analyse Binary File", id="analyse", disabled=True)
                yield Button("Generate SBOM", id="generate_sbom", disabled=True)
                yield Button("Query Database", id="query_db")
        yield Footer()

    def watch_selected_path(self, path):
        label = self.query_one("#selected-label", Static)
        can_process = path is not None and (path.is_file() or path.is_dir())
        for button_id in ["#analyse", "#generate_sbom"]:
            self.query_one(button_id, Button).disabled = not can_process
        label.update(f"Selected: {path.name}" if path else "Selected: None")

    def on_directory_tree_file_selected(self, event):
        event.stop()
        self.selected_path = event.path

    def on_directory_tree_directory_selected(self, event):
        event.stop()
        self.selected_path = event.path

    def on_button_pressed(self, event):
        event.stop()
        if event.button.id == "generate_sbom" and self.selected_path:
            self.app.push_screen(SbomScreen(target_path=self.selected_path))
        elif event.button.id == "analyse" and self.selected_path:
            self.app.push_screen(AnalyseScreen(target_path=self.selected_path))
        elif event.button.id == "query_db":
            self.app.push_screen(QueryScreen())


class BidsUI(App):
    """A text based UI for the BIDS ELF analysis tools."""

    CSS_FILE = "bids_style.tcss"
    bids_dir, _ = os.path.split(__file__)
    CSS_PATH = os.path.join(bids_dir, CSS_FILE)

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self):
        self.push_screen(MainScreen())


def main(argv=None):
    app = BidsUI()
    app.run()


if __name__ == "__main__":
    main()
