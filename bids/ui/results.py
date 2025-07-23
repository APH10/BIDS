# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import json

from rich.text import Text
from textual import on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, Static


# Custom Highlighter
class SearchHighlighter:
    def __init__(self, search_term="", current_match_line=None):
        super().__init__()
        self.search_term = search_term.lower()
        self.current_match_line = current_match_line

    def __call__(self, text, line_number):
        """Applies highlighting to the given Text object."""
        if not self.search_term:
            return text
        plain_text = text.plain.lower()
        start = 0
        while True:
            # Highlights all matches in current line
            idx = plain_text.find(self.search_term, start)
            if idx == -1:
                break
            end = idx + len(self.search_term)
            if line_number == self.current_match_line:
                # Highlight the current match
                text.stylize("b on yellow", idx, end)
            else:
                # Highlight other matches with the regular style
                text.stylize("b reverse", idx, end)
            start = end
        return text


# A custom widget to contain and manage lines within a container
class LogContainer(Container):
    search_term: Reactive[str] = reactive("", always_update=True)
    current_match_line: Reactive[int | None] = reactive(None)

    def __init__(
        self,
        *children: Widget,
        name=None,
        id=None,
        classes=None,
        disabled=False,
    ):
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        # Initialise highlighter
        self._current_highlighter = SearchHighlighter("", None)

    def watch_search_term(self, new_search_term):
        # Re-initialize highlighter to update its internal search_term
        self._current_highlighter = SearchHighlighter(
            new_search_term, self.current_match_line
        )

    def watch_current_match_line(self, new_line):
        # Re-initialize highlighter to update its internal current_match_line
        self._current_highlighter = SearchHighlighter(self.search_term, new_line)

    def render_log_lines(self, all_messages: list[str]) -> None:
        """Renders all log messages as Static widgets with the current highlighter."""
        self.remove_children()  # Clear existing log lines
        for line_no, msg in enumerate(all_messages):
            rich_text = Text(msg)
            highlighted_text = self._current_highlighter(rich_text, line_no)
            self.mount(Static(highlighted_text))
        self.scroll_home()  # Scroll to the top after re-rendering


# Custom Input widget to handle the Escape key
class SearchInput(Input):
    """An Input widget for search with custom key handling."""

    def on_key(self, event):
        """Handles specific key presses like 'escape'."""
        if event.key == "escape":
            self.app.post_message(SearchCleared())
            self.value = ""
            event.prevent_default()
            event.stop()  # Stop the event from propagating further
            return


class SearchCleared(Message):
    """Posted when the search is cleared."""
    pass


class QueryResultScreen(Screen):
    """A screen to display query results with pagination."""

    results: list[dict]  # Store all results
    page_size = 10
    current_page = 0
    _all_log = []
    # Control search box visibility
    show_search_input: Reactive[bool] = reactive(False)
    _match_indices = []  # Stores line numbers indices in _all_log of all matches
    current_match_index: Reactive[int | None] = reactive(
        None
    )  # Index within _match_indices list

    def __init__(
        self,
        results,
        search_term,
        page_size=10,
        verbose=False,
        name=None,
        id=None,
        classes=None,
    ) -> None:
        super().__init__(name, id, classes)
        self.results = results
        self.search_term = search_term
        self.page_size = page_size
        self.verbose = verbose
        self.current_page = 0  # Start at the first page
        self.content = "No results to display yet."

    def compose(self):
        yield Header(name=f"Query Results for: '{self.search_term}'")
        with Container():
            with VerticalScroll(id="results_container", classes="log-scroll-view"):
                yield LogContainer(id="log_display")
            # Input starts hidden
            yield Input(placeholder="Search...", id="search_input")
        with Horizontal(id="pagination_controls"):
            yield Button("First", id="first_page_button", disabled=True)
            yield Button("Previous", id="prev_page_button", disabled=True)
            yield Label("Page:")
            yield Input("1", id="page_input", classes="small_input")
            yield Label(f"of {self.total_pages}", id="total_pages_label")
            yield Button("Next", id="next_page_button", disabled=True)
            yield Button("Last", id="last_page_button", disabled=True)
            yield Button("Go", id="go_page_button")
        yield Footer()

    def watch_show_search_input(self, show_input):
        """Called when the show_search_input reactive property changes."""
        search_input = self.query_one("#search_input", Input)
        if show_input:
            search_input.styles.display = "block"  # Make it visible
            search_input.focus()
            self.notify(
                "Enter search term and press Enter. Press Escape to cancel.", timeout=3
            )
        else:
            search_input.styles.display = "none"  # Make it hidden
            search_input.blur()

    # Watcher for current_match_index to update LogContainer and scroll
    def watch_current_match_index(self, new_index):
        log_container = self.query_one("#log_display", LogContainer)
        if new_index is not None and self._match_indices:
            line_to_highlight = self._match_indices[new_index]
            log_container.current_match_line = line_to_highlight
            # Redraw to show highlight
            self._redraw_log_content(log_container.search_term)
            # Scroll to the highlighted line
            scroll_view = self.query_one("#results_container", VerticalScroll)
            log_content_widgets = log_container.children

            if 0 <= line_to_highlight < len(log_content_widgets):
                scroll_view.scroll_to_widget(
                    log_content_widgets[line_to_highlight], top=True, animate=True
                )
            self.notify(
                f"Match {new_index + 1} of {len(self._match_indices)}", timeout=1
            )
        else:
            # If no matches, clear current highlight
            log_container.current_match_line = None
            self._redraw_log_content(log_container.search_term)

    @property
    def total_pages(self):
        if not self.results:
            return 1
        return (len(self.results) + self.page_size - 1) // self.page_size

    def on_mount(self):
        self.display_current_page()

    def display_current_page(self):
        results_container = self.query_one("#results_container", VerticalScroll)
        # results_container = self.query_one("#results_container")
        if not self.results:
            results_container.mount(Static("No results found for this query."))
            self._update_pagination_buttons()
            self.query_one("#page_input", Input).value = "1"
            self.query_one("#total_pages_label", Label).update(f"of {self.total_pages}")
            return
        self._all_log = []

        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.results))
        current_page_results = self.results[start_index:end_index]

        if not current_page_results:
            # This case might happen if current_page is out of bounds
            self.current_page = 0
            self.display_current_page()  # Recurse to first page
            return

        result_text = ""
        for i, result in enumerate(current_page_results, 1):
            result_text = f"{i + (self.current_page*self.page_size)}. Score: {result['score']:.4f}"
            json_data = json.loads(result["content"])
            result_text += f'   File: {json_data["metadata"]["binary"]["filename"]}\n'
            if "description" in json_data["metadata"]["binary"]:
                result_text += f'   Description: {json_data["metadata"]["binary"]["description"]}\n'
            if self.verbose:
                result_text += "\n   Content:\n"
                # Add each line to support search highlighting process
                for line in json.dumps(json_data, indent=4).splitlines():
                    result_text += f"   {line}\n"
            # Mark end of query
            result_text += "-" * 120 + "\n"
            # Add each line
            for result_info in result_text.splitlines():
                self._all_log.append(result_info)

        self._update_pagination_buttons()
        self.query_one("#page_input", Input).value = str(
            self.current_page + 1
        )  # Update input field
        self.query_one("#total_pages_label", Label).update(f"of {self.total_pages}")
        # Initial redraw of the log content to populate the display
        self._redraw_log_content("")
        # Ensure search input is hidden initially by setting the reactive
        self.show_search_input = False

    def _update_pagination_buttons(self):
        self.query_one("#first_page_button", Button).disabled = self.current_page == 0
        self.query_one("#prev_page_button", Button).disabled = self.current_page == 0
        self.query_one("#next_page_button", Button).disabled = (
            self.current_page >= self.total_pages - 1
        )
        self.query_one("#last_page_button", Button).disabled = (
            self.current_page >= self.total_pages - 1
        )

    def on_button_pressed(self, event):
        if event.button.id == "prev_page_button":
            if self.current_page > 0:
                self.current_page -= 1
                self.display_current_page()
        elif event.button.id == "next_page_button":
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.display_current_page()
        elif event.button.id == "first_page_button":
            self.current_page = 0
            self.display_current_page()
        elif event.button.id == "last_page_button":
            self.current_page = self.total_pages - 1
            self.display_current_page()
        elif event.button.id == "go_page_button":
            try:
                page_num_input = self.query_one("#page_input", Input).value
                target_page = int(page_num_input) - 1  # Convert to 0-indexed
                if 0 <= target_page < self.total_pages:
                    self.current_page = target_page
                    self.display_current_page()
                else:
                    self.app.notify(
                        f"Page number out of range (1-{self.total_pages}).",
                        severity="warning",
                    )
            except ValueError:
                self.app.notify("Invalid page number.", severity="error")

    def action_toggle_search(self):
        """Toggles the visibility of the search input."""
        # Toggle the reactive property, which will trigger the watcher
        self.show_search_input = not self.show_search_input
        # Default input value when initally loaded
        if self.show_search_input:
            self.query_one("#search_input", Input).value = ""

    def action_next_match(self):
        if self._match_indices:
            if self.current_match_index is None:
                self.current_match_index = 0
            else:
                self.current_match_index = (self.current_match_index + 1) % len(
                    self._match_indices
                )
        else:
            self.notify("No active search or no matches found.", timeout=1)

    def action_previous_match(self):
        if self._match_indices:
            if self.current_match_index is None:
                self.current_match_index = len(self._match_indices) - 1
            else:
                self.current_match_index = (
                    self.current_match_index - 1 + len(self._match_indices)
                ) % len(self._match_indices)
        else:
            self.notify("No active search or no matches found.", timeout=1)

    def action_manage_escape(self) -> None:
        search_input = self.query_one("#search_input", Input)
        on_display = search_input.styles.display
        if on_display == "block":
            # Search box visible, clear and hide it
            self.post_message(SearchCleared())
        else:
            self.app.pop_screen()

    @on(Input.Submitted, "#search_input")
    def apply_search_and_highlight(self, event):
        """Applies the search term and refreshes the log display."""
        search_term = event.value.strip()
        log_container = self.query_one("#log_display", LogContainer)

        log_container.search_term = (
            search_term  # Update the reactive search term on LogContainer
        )
        # Find all matches and store their line numbers
        self._match_indices = []
        if search_term:  # Only search if term is not empty
            for i, msg in enumerate(self._all_log):
                if search_term.lower() in msg.lower():
                    self._match_indices.append(i)
        # Initialise current_match_index, which will trigger its watcher
        if self._match_indices:
            self.current_match_index = 0  # Go to the first match
        else:
            self.current_match_index = None  # No matches, clear current highlight
        # Hide the search input
        self.show_search_input = False

    @on(SearchCleared)
    def handle_search_cleared(self):
        """Handles the SearchCleared message to reset the display."""
        log_container = self.query_one("#log_display", LogContainer)

        log_container.search_term = ""  # Reset search term to clear highlighting
        self.current_match_index = None  # Reset current match
        self._match_indices = []  # Clear all matches
        # Hide the search input by setting reactive
        self.show_search_input = False
        self.notify("Search cleared.", timeout=1)  # Notify when search is cleared
        # Force a redraw of the log content to remove highlighting
        self._redraw_log_content("")

    def _redraw_log_content(self, current_search_term):
        """Helper method to clear and redraw the log content with current highlighting."""
        log_container = self.query_one("#log_display", LogContainer)
        # Pass the current match line to the LogContainer so it can update its highlighter
        log_container.current_match_line = (
            self._match_indices[self.current_match_index]
            if self.current_match_index is not None and self._match_indices
            else None
        )
        log_container.render_log_lines(self._all_log)
        # If a match is selected, scrolling is handled by watch_current_match_index.
        # Otherwise scroll to top.
        if self.current_match_index is None:
            self.query_one("#results_container", VerticalScroll).scroll_home()

    # Add bindings
    BINDINGS = [
        ("escape", "manage_escape", "Back"),
        ("slash", "toggle_search", "Search"),
        ("ctrl+f", "toggle_search", "Search"),
        ("n", "next_match", "Next Match"),
        ("p", "previous_match", "Previous Match"),
    ]
