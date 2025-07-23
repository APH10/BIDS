# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from bids.index import BIDSIndexer
from bids.ui.results import QueryResultScreen


class QueryScreen(ModalScreen):
    """A modal screen for entering database query parameters."""

    def compose(self):
        with Container(id="query_options_container"):
            yield Label("Database Query")
            yield Static("Search Term:", classes="label")
            yield Input(
                placeholder="e.g., 'malloc', 'libc'...",
                id="search_term_input",
            )
            yield Static("Number of Results (default 10):", classes="label")
            yield Input("10", placeholder="e.g., 50", id="num_results_input")
            yield Checkbox("Verbose Reporting", id="verbose_checkbox")
            with Horizontal(id="query_buttons"):
                yield Button("Run Query", variant="primary", id="run_query_button")
                yield Button("Cancel", id="cancel_button")

    def on_button_pressed(self, event):
        if event.button.id == "run_query_button":
            self.run_query()
        elif event.button.id == "cancel_button":
            self.app.pop_screen()  # Go back to MainScreen

    def run_query(self):
        search_term = self.query_one("#search_term_input", Input).value.strip()
        num_results_str = self.query_one("#num_results_input", Input).value.strip()
        verbose = self.query_one("#verbose_checkbox", Checkbox).value
        if not search_term:
            self.app.notify("Please enter a search term.", severity="warning")
            return
        try:
            num_results = int(num_results_str) if num_results_str else 10
            if num_results <= 0:
                self.app.notify(
                    "Number of results must be positive.", severity="warning"
                )
                return
        except ValueError:
            self.app.notify("Invalid number of results.", severity="error")
            return
        indexer = BIDSIndexer()
        # Get Data
        results = indexer.search(search_term, num_results)
        # Remove the input screen and replace with the results screen
        self.app.pop_screen()
        self.app.push_screen(QueryResultScreen(results, search_term, verbose=verbose))
